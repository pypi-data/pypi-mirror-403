from pathlib import Path
from typing import Optional

import click
import typer
from rich import print
from tabulate import tabulate

from thestage.color_scheme.color_scheme import ColorScheme
from thestage.config.business.config_provider import ConfigProvider
from thestage.connect.business.remote_server_service import RemoteServerService
from thestage.docker_container.communication.docker_container_api_client import DockerContainerApiClient
from thestage.docker_container.dto.container_response import DockerContainerDto
from thestage.docker_container.dto.enum.container_status import DockerContainerStatus
from thestage.exceptions.git_access_exception import GitAccessException
from thestage.git.communication.git_client import GitLocalClient
from thestage.global_dto.enums.yes_no_response import YesOrNoResponse
from thestage.helpers.error_handler import error_handler
from thestage.i18n.translation import __
from thestage.project.communication.project_api_client import ProjectApiClient
from thestage.project.dto.project_config import ProjectConfig
from thestage.project.dto.project_response import ProjectDto
from thestage.services.abstract_service import AbstractService
from thestage.services.clients.thestage_api.core.http_client_exception import HttpClientException
from thestage.services.filesystem_service import FileSystemService
from thestage.task.communication.task_api_client import TaskApiClient
from thestage.task.dto.view_response import TaskViewResponse


class ProjectService(AbstractService):
    __docker_container_api_client: DockerContainerApiClient = None
    __project_api_client: ProjectApiClient = None
    __task_api_client: TaskApiClient = None
    __config_provider: ConfigProvider = None

    def __init__(
            self,
            task_api_client: TaskApiClient,
            project_api_client: ProjectApiClient,
            docker_container_api_client: DockerContainerApiClient,
            config_provider: ConfigProvider,
            remote_server_service: RemoteServerService,
            file_system_service: FileSystemService,
            git_local_client: GitLocalClient,
    ):
        self.__docker_container_api_client = docker_container_api_client
        self.__task_api_client = task_api_client
        self.__project_api_client = project_api_client
        self.__remote_server_service = remote_server_service
        self.__file_system_service = file_system_service
        self.__git_local_client = git_local_client
        self.__config_provider = config_provider


    @error_handler()
    def init_project(
            self,
            project_slug: Optional[str] = None,
            project_public_id: Optional[str] = None,
    ):
        config = self.__config_provider.get_config()
        project: Optional[ProjectDto] = self.__project_api_client.get_project(
            slug=project_slug,
            public_id=project_public_id,
        )

        if not project:
            typer.echo('Project not found')
            raise typer.Exit(1)

        is_git_folder = self.__git_local_client.is_present_local_git(
            path=config.runtime.working_directory,
        )
        if is_git_folder:
            has_remote = self.__git_local_client.has_remote(
                path=config.runtime.working_directory,
            )
            if has_remote:
                typer.echo(__('Local repository already has a remote configured; aborting initialization'))
                raise typer.Exit(1)

        if not project.git_repository_url:
            typer.echo(__('Project does not have git repository url'))
            raise typer.Exit(1)

        if project.last_commit_hash or project.last_commit_description:
            continue_with_non_empty_repo: YesOrNoResponse = typer.prompt(
                text=__('Remote repository is probably not empty: latest commit is "{commit_description}" (sha: {commit_hash})\nDo you wish to continue?').format(commit_description=project.last_commit_description, commit_hash=project.last_commit_hash),
                show_choices=True,
                default=YesOrNoResponse.YES.value,
                type=click.Choice([r.value for r in YesOrNoResponse]),
                show_default=True,
            )
            if continue_with_non_empty_repo == YesOrNoResponse.NO:
                typer.echo(__('Project init aborted'))
                raise typer.Exit(0)

        deploy_ssh_key = self.__project_api_client.get_project_deploy_ssh_key(
            public_id=project.public_id,
        )

        deploy_key_path = self.__config_provider.save_project_deploy_ssh_key(
            deploy_ssh_key=deploy_ssh_key,
            project_public_id=project.public_id,
        )

        if is_git_folder:
            has_changes = self.__git_local_client.has_changes_with_untracked(
                path=config.runtime.working_directory,
            )
            if has_changes:
                typer.echo(__('Local repository has uncommitted changes or untracked files. Use an empty directory'))
                raise typer.Exit(1)
        else:
            repo = self.__git_local_client.init_repository(
                path=config.runtime.working_directory,
            )

        is_remote_added = self.__git_local_client.add_remote_to_repo(
            path=config.runtime.working_directory,
            remote_url=project.git_repository_url,
            remote_name=project.git_repository_name,
        )
        if not is_remote_added:
            typer.echo(__('We cannot add remote, something wrong'))
            raise typer.Exit(2)

        self.__git_local_client.git_fetch(path=config.runtime.working_directory, deploy_key_path=deploy_key_path)

        self.__git_local_client.init_gitignore(path=config.runtime.working_directory)

        self.__git_local_client.git_add_all(repo_path=config.runtime.working_directory)

        project_config = ProjectConfig()
        project_config.public_id = project.public_id
        project_config.slug = project.slug
        project_config.git_repository_url = project.git_repository_url
        project_config.deploy_key_path = str(deploy_key_path)
        self.__config_provider.save_project_config(project_config=project_config)

        typer.echo(__("Project successfully initialized at %path%", {"path": config.runtime.working_directory}))


    @error_handler()
    def clone_project(
            self,
            project_slug: str,
            project_public_id: str
    ):
        config = self.__config_provider.get_config()
        project: Optional[ProjectDto] = self.__project_api_client.get_project(
            slug=project_slug,
            public_id=project_public_id
        )

        if not project:
            typer.echo('Project not found')
            raise typer.Exit(1)

        if not self.__file_system_service.is_folder_empty(folder=config.runtime.working_directory, auto_create=True):
            typer.echo(__("Cannot clone: the folder is not empty"))
            raise typer.Exit(1)

        is_git_folder = self.__git_local_client.is_present_local_git(
            path=config.runtime.working_directory,
        )

        if is_git_folder:
            typer.echo(__('Directory already contains a git repository. Cannot clone here'))
            raise typer.Exit(1)

        if not project.git_repository_url:
            typer.echo(__("Unexpected Project error, missing Repository"))
            raise typer.Exit(1)

        deploy_ssh_key = self.__project_api_client.get_project_deploy_ssh_key(public_id=project.public_id)
        deploy_key_path = self.__config_provider.save_project_deploy_ssh_key(deploy_ssh_key=deploy_ssh_key, project_public_id=project.public_id,)

        try:
            self.__git_local_client.clone(
                url=project.git_repository_url,
                path=config.runtime.working_directory,
                deploy_key_path=deploy_key_path
            )
            self.__git_local_client.init_gitignore(path=config.runtime.working_directory)
        except GitAccessException as ex:
            typer.echo(ex.get_message())
            typer.echo(ex.get_dop_message())
            typer.echo(__(
                "Check you email or open this repo url %git_url% and 'Accept invitation'",
                {
                    'git_url': ex.get_url()
                }
            ))
            raise typer.Exit(1)

        project_config = ProjectConfig()
        project_config.public_id = project.public_id
        project_config.slug = project.slug
        project_config.git_repository_url = project.git_repository_url
        project_config.deploy_key_path = str(deploy_key_path)
        self.__config_provider.save_project_config(project_config=project_config)
        typer.echo(__("Project successfully cloned to %path%", {"path": config.runtime.working_directory}))

    @error_handler()
    def checkout_project(
            self,
            task_public_id: Optional[str],
            branch_name: Optional[str],
    ):
        config = self.__config_provider.get_config()
        project_config: ProjectConfig = self.get_fixed_project_config()
        if not project_config:
            typer.echo(__("Command must be run from an initialized project directory"))
            raise typer.Exit(1)

        target_commit_hash: Optional[str] = None
        if task_public_id:
            task_view_response: Optional[TaskViewResponse] = None
            try:
                task_view_response = self.__task_api_client.get_task(task_public_id=task_public_id)
            except HttpClientException as e:
                if e.get_status_code() == 400:
                    typer.echo(f"Task {task_public_id} was not found")
                    # overriding arguments here
                    branch_name = str(task_public_id)
                    task_public_id = None

            if task_view_response and task_view_response.task:
                target_commit_hash = task_view_response.task.commit_hash
                if not target_commit_hash:
                    typer.echo(f"Task ({task_public_id}) has no commit hash")  # possible legacy problems
                    raise typer.Exit(1)

        is_commit_allowed: bool = True

        if self.__git_local_client.is_head_detached(path=config.runtime.working_directory):
            is_commit_allowed = False
            if self.__git_local_client.is_head_committed_in_headless_state(path=config.runtime.working_directory):
                commit_message = self.__git_local_client.get_current_commit(
                    path=config.runtime.working_directory).message
                print(
                    f"[{ColorScheme.GIT_HEADLESS.value}]Your current commit '{commit_message.strip()}' was likely created in detached head state. Checking out will discard all changes.[/{ColorScheme.GIT_HEADLESS.value}]")
                response: YesOrNoResponse = typer.prompt(
                    text=__('Continue?'),
                    show_choices=True,
                    default=YesOrNoResponse.YES.value,
                    type=click.Choice([r.value for r in YesOrNoResponse]),
                    show_default=True,
                )
                if response == YesOrNoResponse.NO:
                    raise typer.Exit(0)
        else:
            if self.__git_local_client.get_active_branch_name(path=config.runtime.working_directory) == branch_name:
                typer.echo(f"You are already at branch '{branch_name}'")
                raise typer.Exit(0)

        if is_commit_allowed:
            self.__git_local_client.git_add_all(repo_path=config.runtime.working_directory)

            has_changes = self.__git_local_client.has_changes_with_untracked(
                path=config.runtime.working_directory,
            )

            if has_changes:
                active_branch_name = self.__git_local_client.get_active_branch_name(config.runtime.working_directory)
                diff_stat = self.__git_local_client.git_diff_stat(repo_path=config.runtime.working_directory)
                typer.echo(__('Active branch [%branch_name%] has uncommitted changes: %diff_stat_bottomline%', {
                    'diff_stat_bottomline': diff_stat,
                    'branch_name': active_branch_name,
                }))

                response: str = typer.prompt(
                    text=__('Commit changes?'),
                    show_choices=True,
                    default=YesOrNoResponse.YES.value,
                    type=click.Choice([r.value for r in YesOrNoResponse]),
                    show_default=True,
                )
                if response == YesOrNoResponse.NO.value:
                    typer.echo(__('Cannot checkout with uncommitted changes'))
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
                    typer.echo(__('Cannot commit with empty commit name'))
                    raise typer.Exit(0)

        if target_commit_hash:
            if self.__git_local_client.get_current_commit(
                    path=config.runtime.working_directory).hexsha != target_commit_hash:
                is_checkout_successful = self.__git_local_client.git_checkout_to_commit(
                    path=config.runtime.working_directory,
                    commit_hash=target_commit_hash
                )

                if is_checkout_successful:
                    print(f"Checked out to commit {target_commit_hash}")
                    print(
                        f"[{ColorScheme.GIT_HEADLESS.value}]HEAD is detached. To be able make changes in repository, checkout to any branch.[/{ColorScheme.GIT_HEADLESS.value}]")
            else:
                typer.echo("HEAD is already at requested commit")
        elif branch_name:
            if self.__git_local_client.is_branch_exists(path=config.runtime.working_directory, branch_name=branch_name):
                self.__git_local_client.git_checkout_to_branch(
                    path=config.runtime.working_directory,
                    branch=branch_name
                )
                typer.echo(f"Checked out to branch '{branch_name}'")
            else:
                typer.echo(f"Branch '{branch_name}' was not found in project repository")
        else:
            main_branch = self.__git_local_client.find_main_branch_name(path=config.runtime.working_directory)
            if main_branch:
                self.__git_local_client.git_checkout_to_branch(
                    path=config.runtime.working_directory,
                    branch=main_branch
                )
                typer.echo(f"Checked out to detected main branch: '{main_branch}'")
            else:
                typer.echo("No main branch found")

    @error_handler()
    def set_default_container(
            self,
            container_public_id: Optional[str],
            container_slug: Optional[str],
    ):
        project_config: ProjectConfig = self.__config_provider.read_project_config()

        if project_config is None:
            typer.echo(f"No project found in working directory")
            raise typer.Exit(1)

        container: Optional[DockerContainerDto] = None
        if container_slug or container_public_id:
            container: DockerContainerDto = self.__docker_container_api_client.get_container(
                container_public_id=container_public_id,
                container_slug=container_slug,
            )
            if container is None:
                typer.echo(f"Could not find container '{container_slug or container_public_id}'")
                raise typer.Exit(1)

            if container.project.public_id != project_config.public_id:
                typer.echo(
                    f"Provided container '{container_slug or container_public_id}' is not related to current project '{project_config.public_id}'")
                raise typer.Exit(1)

            if container.frontend_status.status_key != DockerContainerStatus.RUNNING:
                typer.echo(
                    f"Note: provided container '{container_slug or container_public_id}' is in status '{container.frontend_status.status_translation}'")

        project_config.default_container_public_id = container.public_id if container else None
        project_config.prompt_for_default_container = False
        self.__config_provider.save_project_config(project_config=project_config)
        typer.echo("Default container settings were updated")

    @error_handler()
    def print_project_config(self):
        project_config: ProjectConfig = self.__config_provider.read_project_config()

        if project_config is None:
            typer.echo(f"No project found in working directory")
            raise typer.Exit(1)

        is_deploy_key_exists = project_config.deploy_key_path and self.__file_system_service.check_if_path_exist(
            project_config.deploy_key_path)

        typer.echo(tabulate(
            [
                [
                    "Project ID", project_config.public_id
                ],
                [
                    "Project name", project_config.slug
                ],
                [
                    "Default docker container ID",
                    project_config.default_container_public_id if project_config.default_container_public_id else "<None>"
                ],
                [
                    "Deploy key path", project_config.deploy_key_path if is_deploy_key_exists else "<None>"
                ],
            ],
            showindex=False,
            tablefmt="simple",
        ))

        if is_deploy_key_exists:
            typer.echo("")
            typer.echo(f"You can insert the following text:")
            print(
                f"[{ColorScheme.USEFUL_INFO.value}]GIT_SSH_COMMAND=\"ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -i {project_config.deploy_key_path}\"[{ColorScheme.USEFUL_INFO.value}]")
            typer.echo(f"before any regular git command to manage your local Project repository directly")

    @error_handler()
    def get_fixed_project_config(self) -> Optional[ProjectConfig]:
        project_config: ProjectConfig = self.__config_provider.read_project_config()
        if project_config is None:
            return None

        if project_config.public_id is None:
            project = self.__project_api_client.get_project(public_id=None, slug=project_config.slug)
            project_config.public_id = project.public_id
            self.__config_provider.save_project_config(project_config=project_config)

        if not Path(project_config.deploy_key_path).is_file():
            deploy_ssh_key = self.__project_api_client.get_project_deploy_ssh_key(
                public_id=project_config.public_id,
            )

            deploy_key_path = self.__config_provider.save_project_deploy_ssh_key(
                deploy_ssh_key=deploy_ssh_key,
                project_public_id=project_config.public_id,
            )

            project_config.deploy_key_path = deploy_key_path
            self.__config_provider.save_project_config(project_config=project_config)
            typer.echo(f'Recreated missing deploy key for the project')

        return project_config

    @error_handler()
    def pull_project(self):
        config = self.__config_provider.get_config()
        project_config: ProjectConfig = self.get_fixed_project_config()
        if not project_config:
            typer.echo(__("No project found at the path: %path%. Please initialize or clone a project first.",
                          {"path": config.runtime.working_directory}))
            raise typer.Exit(1)

        typer.echo("Pulling code from remote repository...")
        self.__git_local_client.git_pull(
            path=config.runtime.working_directory,
            deploy_key_path=project_config.deploy_key_path,
        )

    @error_handler()
    def reset_project(self):
        config = self.__config_provider.get_config()
        project_config: ProjectConfig = self.get_fixed_project_config()
        if not project_config:
            typer.echo(__("No project found at the path: %path%. Please initialize or clone a project first.",
                          {"path": config.runtime.working_directory}))
            raise typer.Exit(1)

        typer.echo("Fetching code from remote repository...")
        self.__git_local_client.git_fetch(
            path=config.runtime.working_directory,
            deploy_key_path=project_config.deploy_key_path,
        )
        typer.echo("Resetting local branch...")
        self.__git_local_client.reset_hard(
            path=config.runtime.working_directory,
            deploy_key_path=project_config.deploy_key_path,
            reset_to_origin=True
        )
