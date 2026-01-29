from typing import Optional

import click
import typer
from git import Commit
from rich import print

from thestage.color_scheme.color_scheme import ColorScheme
from thestage.config.business.config_provider import ConfigProvider
from thestage.docker_container.communication.docker_container_api_client import DockerContainerApiClient
from thestage.docker_container.dto.container_response import DockerContainerDto
from thestage.git.communication.git_client import GitLocalClient
from thestage.global_dto.enums.yes_no_response import YesOrNoResponse
from thestage.helpers.error_handler import error_handler
from thestage.i18n.translation import __
from thestage.project.business.project_service import ProjectService
from thestage.project.dto.project_config import ProjectConfig
from thestage.services.abstract_service import AbstractService
from thestage.services.clients.thestage_api.dtos.paginated_entity_list import PaginatedEntityList
from thestage.services.filesystem_service import FileSystemService
from thestage.task.business.mapper.task_mapper import TaskMapper
from thestage.task.communication.task_api_client import TaskApiClient
from thestage.task.dto.run_task_response import RunTaskResponse
from thestage.task.dto.task import Task
from thestage.task.dto.task_entity import TaskEntity


class TaskService(AbstractService):
    def __init__(
            self,
            docker_container_api_client: DockerContainerApiClient,
            task_api_client: TaskApiClient,
            config_provider: ConfigProvider,
            git_local_client: GitLocalClient,
            file_system_service: FileSystemService,
            project_service: ProjectService,
    ):
        self.__docker_container_api_client = docker_container_api_client
        self.__task_api_client = task_api_client
        self.__config_provider = config_provider
        self.__git_local_client = git_local_client
        self.__file_system_service = file_system_service
        self.__project_service = project_service


    @error_handler()
    def project_run_task(
            self,
            run_command: str,
            docker_container_slug: str,
            docker_container_public_id: str,
            task_title: Optional[str] = None,
            commit_hash: Optional[str] = None,
            files_to_add: Optional[str] = None,
            is_skip_auto_commit: Optional[bool] = False,
    ) -> Optional[Task]:
        config = self.__config_provider.get_config()
        project_config: ProjectConfig = self.__project_service.get_fixed_project_config()
        if not project_config:
            typer.echo(__("No project found at the path: %path%. Initialize or clone a project first.",
                          {"path": config.runtime.working_directory}))
            raise typer.Exit(1)

        if not docker_container_public_id and not docker_container_slug and not project_config.default_container_public_id:
            typer.echo(__('Docker container ID or name is required'))
            raise typer.Exit(1)

        final_container_public_id = docker_container_public_id
        final_container_slug = docker_container_slug
        if not final_container_public_id and not final_container_slug:
            final_container_public_id = project_config.default_container_public_id
            typer.echo(
                f"Using default docker container for this project: '{project_config.default_container_public_id}'")

        container: DockerContainerDto = self.__docker_container_api_client.get_container(
            container_slug=final_container_slug,
            container_public_id=final_container_public_id
        )

        if container is None:
            if final_container_slug:
                typer.echo(f"Could not find container with name '{final_container_slug}'")
            if final_container_public_id:
                typer.echo(f"Could not find container with ID '{final_container_public_id}'")
            if project_config.default_container_public_id == final_container_public_id:
                project_config.default_container_public_id = None
                project_config.prompt_for_default_container = True
                self.__config_provider.save_project_config(project_config=project_config)
                typer.echo(f"Default container settings were reset")
            raise typer.Exit(1)

        if container.project.public_id != project_config.public_id:
            typer.echo(
                f"Provided container '{container.public_id}' is not related to project '{project_config.public_id}'")
            raise typer.Exit(1)

        if (project_config.prompt_for_default_container is None or project_config.prompt_for_default_container) and (
                docker_container_slug or docker_container_public_id) and (
                project_config.default_container_public_id != container.public_id):
            set_default_container_answer: str = typer.prompt(
                text=f"Would you like to set '{docker_container_slug}' as a default container for this project installation?",
                show_choices=True,
                default=YesOrNoResponse.YES.value,
                type=click.Choice([r.value for r in YesOrNoResponse]),
                show_default=True,
            )
            project_config.prompt_for_default_container = False
            if set_default_container_answer == YesOrNoResponse.YES.value:
                project_config.default_container_public_id = container.public_id

            self.__config_provider.save_project_config(project_config=project_config)

        has_wrong_args = files_to_add and commit_hash or is_skip_auto_commit and commit_hash or files_to_add and is_skip_auto_commit

        if has_wrong_args:
            warning_msg = f"[{ColorScheme.WARNING.value}][WARNING] You can provide only one of the following arguments: --commit-hash, --files-add, --skip-autocommit[{ColorScheme.WARNING.value}]"
            print(warning_msg)
            raise typer.Exit(1)

        if not is_skip_auto_commit and not commit_hash:
            is_git_folder = self.__git_local_client.is_present_local_git(path=config.runtime.working_directory)
            if not is_git_folder:
                typer.echo("Error: Working directory is not a git repository")
                raise typer.Exit(1)

            is_commit_allowed: bool = True
            has_changes = self.__git_local_client.has_changes_with_untracked(
                path=config.runtime.working_directory,
            )

            if self.__git_local_client.is_head_detached(path=config.runtime.working_directory):
                is_commit_allowed = False
                print(f"[{ColorScheme.GIT_HEADLESS.value}]HEAD is detached[{ColorScheme.GIT_HEADLESS.value}]")

                is_headless_commits_present = self.__git_local_client.is_head_committed_in_headless_state(
                    path=config.runtime.working_directory)
                if is_headless_commits_present:
                    print(
                        f"[{ColorScheme.GIT_HEADLESS.value}]Current commit created in detached HEAD state. Cannot use it to run the task. Consider using 'project checkout' command to return to a valid reference.[{ColorScheme.GIT_HEADLESS.value}]")
                    raise typer.Exit(1)

                if has_changes:
                    print(
                        f"[{ColorScheme.GIT_HEADLESS.value}]Local changes detected in detached head state. They will not impact the task execution.[{ColorScheme.GIT_HEADLESS.value}]")
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
                if not self.__git_local_client.add_files_with_size_limit_or_warn(config.runtime.working_directory,
                                                                                 files_to_add):
                    warning_msg = f"[{ColorScheme.WARNING.value}][WARNING] Task was not started [{ColorScheme.WARNING.value}]"
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
                        typer.echo("Cannot run task with uncommitted changes - aborting")
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
                    else:
                        typer.echo(__('Commit message cannot be empty'))
                        raise typer.Exit(0)
                else:
                    pass
                    # possible to push new empty branch - only that there's a wrong place to do so

                self.__git_local_client.push_changes(
                    path=config.runtime.working_directory,
                    deploy_key_path=project_config.deploy_key_path
                )
                typer.echo(__("Pushed changes to remote repository"))

        if not commit_hash:
            commit = self.__git_local_client.get_current_commit(path=config.runtime.working_directory)
            if not commit or not isinstance(commit, Commit):
                print('[red]Error: No current commit found in the local repository[/red]')
                raise typer.Exit(0)
            commit_hash = commit.hexsha
        else:
            commit = self.__git_local_client.get_commit_by_hash(path=config.runtime.working_directory,
                                                                commit_hash=commit_hash)
            if not commit or not isinstance(commit, Commit):
                print(f'[red]Error: commit \'{commit_hash}\' was not found in the local repository[/red]')
                raise typer.Exit(0)

        if not task_title:
            task_title = commit.message.strip() if commit.message else f'Task_{commit_hash}'
            if not commit.message:
                typer.echo(f'Commit message is empty. Task title is set to "{task_title}"')

        run_task_response: RunTaskResponse = self.__task_api_client.execute_project_task(
            project_public_id=project_config.public_id,
            docker_container_public_id=container.public_id,
            run_command=run_command,
            commit_hash=commit_hash,
            task_title=task_title,
        )
        if run_task_response:
            if run_task_response.message:
                print(f"[{ColorScheme.WARNING.value}]{run_task_response.message}[{ColorScheme.WARNING.value}]")
            if run_task_response.is_success and run_task_response.task:
                typer.echo(f"Task '{run_task_response.task.title}' has been scheduled successfully. Task ID: {run_task_response.task.public_id}")
                if run_task_response.tasksInQueue:
                    typer.echo(f"There are tasks in queue ahead of this new task:")
                    for queued_task_item in run_task_response.tasksInQueue:
                        typer.echo(f"{queued_task_item.public_id} - {queued_task_item.frontend_status.status_translation}")
                return run_task_response.task
            else:
                typer.echo(f'The task failed with an error: {run_task_response.message}')
                raise typer.Exit(1)
        else:
            typer.echo("The task failed with an error")
            raise typer.Exit(1)

    @error_handler()
    def cancel_task(self, task_public_id: str):
        cancel_result = self.__task_api_client.cancel_task(
            task_public_id=task_public_id,
        )

        if cancel_result.is_success:
            typer.echo(f'Task {task_public_id} has been canceled')
        else:
            typer.echo(f'Task {task_public_id} could not be canceled: {cancel_result.message}')

    def print_task_list(self, project_public_id: Optional[str], project_slug: Optional[str], row, page):
        if not project_slug and not project_public_id:
            project_config: ProjectConfig = self.__config_provider.read_project_config()
            if not project_config:
                typer.echo(
                    __("Provide the project unique ID or run this command from within an initialized project directory"))
                raise typer.Exit(1)
            project_public_id = project_config.public_id

        self.print(
            func_get_data=self.get_project_task_list,
            func_special_params={
                'project_public_id': project_public_id,
                'project_slug': project_slug,
            },
            mapper=TaskMapper(),
            headers=list(map(lambda x: x.alias, TaskEntity.model_fields.values())),
            row=row,
            page=page,
            max_col_width=[100, 100, 100, 100, 100, 100, 100, 100],
            show_index="never",
        )

    @error_handler()
    def get_project_task_list(
            self,
            project_public_id: Optional[str],
            project_slug: Optional[str],
            row: int = 5,
            page: int = 1,
    ) -> PaginatedEntityList[Task]:
        data: Optional[PaginatedEntityList[Task]] = self.__task_api_client.get_task_list_for_project(
            project_public_id=project_public_id,
            project_slug=project_slug,
            page=page,
            limit=row,
        )

        return data