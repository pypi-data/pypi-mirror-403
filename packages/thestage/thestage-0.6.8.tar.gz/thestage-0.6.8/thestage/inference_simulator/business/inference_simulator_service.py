import json
import os
from pathlib import Path
from typing import Optional, List

import click
import typer
from git import Commit
from rich import print

from thestage.color_scheme.color_scheme import ColorScheme
from thestage.config.business.config_provider import ConfigProvider
from thestage.git.communication.git_client import GitLocalClient
from thestage.global_dto.enums.yes_no_response import YesOrNoResponse
from thestage.helpers.error_handler import error_handler
from thestage.i18n.translation import __
from thestage.inference_model.communication.inference_model_api_client import InferenceModelApiClient
from thestage.inference_model.dto.push_inference_simulator_model_response import \
    PushInferenceSimulatorModelResponse
from thestage.inference_simulator.business.mapper.inference_simulator_mapper import InferenceSimulatorMapper
from thestage.inference_simulator.communication.inference_simulator_api_client import InferenceSimulatorApiClient
from thestage.inference_simulator.dto.enum.inference_simulator_status import InferenceSimulatorStatus
from thestage.inference_simulator.dto.get_inference_simulator_response import \
    GetInferenceSimulatorResponse
from thestage.inference_simulator.dto.inference_simulator import InferenceSimulator
from thestage.inference_simulator.dto.inference_simulator_entity import InferenceSimulatorEntity
from thestage.inference_simulator.dto.start_inference_simulator_response import \
    StartInferenceSimulatorResponse
from thestage.project.business.project_service import ProjectService
from thestage.project.dto.project_config import ProjectConfig
from thestage.services.abstract_service import AbstractService
from thestage.services.clients.thestage_api.dtos.paginated_entity_list import PaginatedEntityList


class InferenceSimulatorService(AbstractService):
    def __init__(
            self,
            inference_simulator_api_client: InferenceSimulatorApiClient,
            inference_model_api_client: InferenceModelApiClient,
            config_provider: ConfigProvider,
            git_local_client: GitLocalClient,
            project_service: ProjectService,
    ):
        self.__inference_simulator_api_client = inference_simulator_api_client
        self.__inference_model_api_client = inference_model_api_client
        self.__config_provider = config_provider
        self.__git_local_client = git_local_client
        self.__project_service = project_service

    @error_handler()
    def project_run_inference_simulator(
            self,
            commit_hash: Optional[str] = None,
            rented_instance_public_id: Optional[str] = None,
            rented_instance_slug: Optional[str] = None,
            self_hosted_instance_public_id: Optional[str] = None,
            self_hosted_instance_slug: Optional[str] = None,
            inference_dir: Optional[str] = None,
            is_skip_installation: Optional[bool] = False,
            files_to_add: Optional[str] = None,
            is_skip_auto_commit: Optional[bool] = False,
    ) -> Optional[InferenceSimulator]:
        config = self.__config_provider.get_config()
        project_config: ProjectConfig = self.__project_service.get_fixed_project_config()

        if not project_config:
            typer.echo(__("No project found at the path: %path%. Please initialize or clone a project first. Or provide path to project using --working-directory option.",
                          {"path": config.runtime.working_directory}))
            raise typer.Exit(1)

        instance_args_count = sum(v is not None for v in [rented_instance_public_id, rented_instance_slug, self_hosted_instance_public_id, self_hosted_instance_slug])
        if instance_args_count != 1:
            typer.echo("Please provide a single instance (rented or self-hosted) identifier - name or ID.")
            raise typer.Exit(1)

        has_wrong_args = files_to_add and commit_hash or is_skip_auto_commit and commit_hash or files_to_add and is_skip_auto_commit
        if has_wrong_args:
            warning_msg = f"[{ColorScheme.WARNING.value}][WARNING] You can provide only one of the following arguments: --commit-hash, --files-add, --skip-autocommit[{ColorScheme.WARNING.value}]"
            print(warning_msg)
            raise typer.Exit(1)

        if not is_skip_auto_commit and not commit_hash:
            is_git_folder = self.__git_local_client.is_present_local_git(path=config.runtime.working_directory)
            if not is_git_folder:
                typer.echo("Error: Working directory is not a git repository.")
                raise typer.Exit(1)

            is_commit_allowed: bool = True
            has_changes = self.__git_local_client.has_changes_with_untracked(
                path=config.runtime.working_directory,
            )

            if self.__git_local_client.is_head_detached(path=config.runtime.working_directory):
                print(f"[{ColorScheme.GIT_HEADLESS.value}]HEAD is detached[{ColorScheme.GIT_HEADLESS.value}]")

                is_headless_commits_present = self.__git_local_client.is_head_committed_in_headless_state(
                    path=config.runtime.working_directory)
                if is_headless_commits_present:
                    print(
                        f"[{ColorScheme.GIT_HEADLESS.value}]Current commit was made in detached head state. Cannot use it to start the inference simulator. Consider using 'project checkout' command to return to a valid reference.[{ColorScheme.GIT_HEADLESS.value}]")
                    raise typer.Exit(1)

                if has_changes:
                    print(
                        f"[{ColorScheme.GIT_HEADLESS.value}]Local changes detected in detached head state. They will not impact the inference simulator.[{ColorScheme.GIT_HEADLESS.value}]")
                    is_commit_allowed = False
                    response: YesOrNoResponse = typer.prompt(
                        text=__('Continue?'),
                        show_choices=True,
                        default=YesOrNoResponse.YES.value,
                        type=click.Choice([r.value for r in YesOrNoResponse]),
                        show_default=True,
                    )
                    if response == YesOrNoResponse.NO:
                        raise typer.Exit(0)

            if is_commit_allowed:
                if not self.__git_local_client.add_files_with_size_limit_or_warn(config.runtime.working_directory, files_to_add):
                    warning_msg = f"[{ColorScheme.WARNING.value}][WARNING] Inference simulator was not started [{ColorScheme.WARNING.value}]"
                    print(warning_msg)
                    raise typer.Exit(1)

                diff_stat = self.__git_local_client.git_diff_stat(repo_path=config.runtime.working_directory)

                if has_changes and diff_stat:
                    branch_name = self.__git_local_client.get_active_branch_name(config.runtime.working_directory)
                    typer.echo(__('Active branch [%branch_name%] has uncommitted changes: %diff_stat_bottomline%', {
                        'diff_stat_bottomline': diff_stat,
                        'branch_name': branch_name,
                    }))

                    response: str = typer.prompt(
                        text=__('Commit changes?'),
                        show_choices=True,
                        default=YesOrNoResponse.YES.value,
                        type=click.Choice([r.value for r in YesOrNoResponse]),
                        show_default=True,
                    )
                    if response == YesOrNoResponse.NO.value:
                        typer.echo("inference simulator cannot use uncommitted changes - aborting")
                        raise typer.Exit(0)

                    commit_name = typer.prompt(
                        text=__('Please provide commit message'),
                        show_choices=False,
                        type=str,
                        show_default=False,
                    )

                    if commit_name:
                        commit_result = self.__git_local_client.commit_local_changes(
                            path=config.runtime.working_directory,
                            name=commit_name
                        )

                        if commit_result:
                            # in docs not Commit object, on real - str
                            if isinstance(commit_result, str):
                                typer.echo(commit_result)

                        self.__git_local_client.push_changes(
                            path=config.runtime.working_directory,
                            deploy_key_path=project_config.deploy_key_path
                        )
                        typer.echo(__("Pushed changes to remote repository"))
                    else:
                        typer.echo(__('Cannot commit with empty commit name, your code will run without last changes.'))
                else:
                    pass
                    # possible to push new empty branch - only that there's a wrong place to do so

        if not commit_hash:
            commit = self.__git_local_client.get_current_commit(path=config.runtime.working_directory)
            if commit and isinstance(commit, Commit):
                commit_hash = commit.hexsha

        start_inference_simulator_response: StartInferenceSimulatorResponse = self.__inference_simulator_api_client.start_project_inference_simulator(
            project_public_id=project_config.public_id,
            commit_hash=commit_hash,
            rented_instance_public_id=rented_instance_public_id,
            rented_instance_slug=rented_instance_slug,
            self_hosted_instance_public_id=self_hosted_instance_public_id,
            self_hosted_instance_slug=self_hosted_instance_slug,
            inference_dir=inference_dir,
            is_skip_installation=is_skip_installation,
        )
        if start_inference_simulator_response:
            if start_inference_simulator_response.message:
                typer.echo(start_inference_simulator_response.message)
            if start_inference_simulator_response.is_success and start_inference_simulator_response.inferenceSimulator:
                typer.echo("Inference simulator has been scheduled to run successfully.")
                return start_inference_simulator_response.inferenceSimulator
            else:
                typer.echo(__(
                    'Failed to start inference simulator: %server_massage%',
                    {'server_massage': start_inference_simulator_response.message or ""}
                ))
                raise typer.Exit(1)
        else:
            typer.echo(__("Failed to start inference simulator"))
            raise typer.Exit(1)


    @error_handler()
    def project_push_inference_simulator(
            self,
            public_id: Optional[str] = None,
            slug: Optional[str] = None,
    ):

        push_inference_simulator_model_response: PushInferenceSimulatorModelResponse = self.__inference_model_api_client.push_project_inference_simulator_model(
            public_id=public_id,
            slug=slug,
        )
        if push_inference_simulator_model_response:
            if push_inference_simulator_model_response.message:
                typer.echo(push_inference_simulator_model_response.message)
            if push_inference_simulator_model_response.is_success:
                typer.echo("Inference simulator has been successfully scheduled to be pushed to S3 and ECR.")
            else:
                typer.echo(__(
                    'Failed to push inference simulator: %server_massage%',
                    {'server_massage': push_inference_simulator_model_response.message or ""}
                ))
                raise typer.Exit(1)
        else:
            typer.echo(__("Failed to push inference simulator"))
            raise typer.Exit(1)

    @error_handler()
    def project_get_and_save_inference_simulator_metadata(
            self,
            inference_simulator_public_id: Optional[str] = None,
            inference_simulator_slug: Optional[str] = None,
            file_path: Optional[str] = None,
    ):
        get_inference_metadata_response: GetInferenceSimulatorResponse = self.__inference_simulator_api_client.get_inference_simulator(
            public_id=inference_simulator_public_id,
            slug=inference_simulator_slug,
        )

        metadata = get_inference_metadata_response.inferenceSimulator.qlip_serve_metadata

        if metadata:
            typer.echo("qlip_serve_metadata:")
            typer.echo(json.dumps(metadata, indent=4))

            if not file_path:
                file_path = Path(os.getcwd()) / "metadata.json"
                typer.echo(__("No file path provided. Saving metadata to %file_path%", {"file_path": str(file_path)}))

            try:
                parsed_metadata = metadata

                output_file = Path(file_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with output_file.open("w", encoding="utf-8") as file:
                    json.dump(parsed_metadata, file, indent=4)
                typer.echo(__("Metadata successfully saved to %file_path%", {"file_path": str(file_path)}))
            except Exception as e:
                typer.echo(__("Failed to save metadata to %file_path%. Error: %error%",
                              {"file_path": file_path, "error": str(e)}))
                raise typer.Exit(1)
        else:
            typer.echo(__("No qlip_serve_metadata found"))
            raise typer.Exit(1)


    @error_handler()
    def get_project_inference_simulator_list(
            self,
            project_public_id: Optional[str],
            project_slug: Optional[str],
            statuses: List[str],
            row: int = 5,
            page: int = 1,
    ) -> PaginatedEntityList[InferenceSimulator]:
        data: Optional[PaginatedEntityList[InferenceSimulator]] = self.__inference_simulator_api_client.get_inference_simulator_list(
            statuses=statuses,
            project_public_id=project_public_id,
            project_slug=project_slug,
            page=page,
            limit=row,
        )

        return data

    @error_handler()
    def print_inference_simulator_list(self, project_public_id, project_slug, statuses, row, page):
        if not project_public_id and not project_slug:
            project_config: ProjectConfig = self.__config_provider.read_project_config()
            if not project_config:
                typer.echo(__("Provide the project unique ID or run this command from within an initialized project directory"))
                raise typer.Exit(1)
            project_public_id = project_config.public_id

        inference_simulator_status_map = self.__inference_simulator_api_client.get_inference_simulator_business_status_map()

        if not statuses:
            statuses = ({key: inference_simulator_status_map[key] for key in [
                InferenceSimulatorStatus.SCHEDULED,
                InferenceSimulatorStatus.CREATING,
                InferenceSimulatorStatus.RUNNING,
            ]}).values()

        if "all" in statuses:
            statuses = inference_simulator_status_map.values()

        for input_status_item in statuses:
            if input_status_item not in inference_simulator_status_map.values():
                typer.echo(__("'%invalid_status%' is not one of %valid_statuses%", {
                    'invalid_status': input_status_item,
                    'valid_statuses': str(list(inference_simulator_status_map.values()))
                }))
                raise typer.Exit(1)

        typer.echo(__(
            "Listing inference simulators with the following statuses: %statuses%, to view all inference simulators, use --status all",
            placeholders={
                'statuses': ', '.join([status_item for status_item in statuses])
            }))

        backend_statuses: List[str] = [key for key, value in inference_simulator_status_map.items() if value in statuses]

        self.print(
            func_get_data=self.get_project_inference_simulator_list,
            func_special_params={
                'project_public_id': project_public_id,
                'project_slug': project_slug,
                'statuses': backend_statuses,
            },
            mapper=InferenceSimulatorMapper(),
            headers=list(map(lambda x: x.alias, InferenceSimulatorEntity.model_fields.values())),
            row=row,
            page=page,
            max_col_width=[100, 100, 100, 100, 100, 100, 100, 100],
            show_index="never",
        )