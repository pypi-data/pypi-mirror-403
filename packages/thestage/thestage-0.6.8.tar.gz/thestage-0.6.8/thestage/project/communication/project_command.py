from typing import Optional

import typer

from thestage.task.communication import task_command
from thestage.cli_command import CliCommand
from thestage.cli_command_helper import get_command_metadata, check_command_permission, get_command_group_help_panel
from thestage.controllers.utils_controller import validate_config_and_get_service_factory, get_current_directory
from thestage.helpers.logger.app_logger import app_logger
from thestage.i18n.translation import __

app = typer.Typer(no_args_is_help=True, help=__("Manage projects"))
config_app = typer.Typer(no_args_is_help=True, help=__("Manage project config"))
app.add_typer(config_app, name="config", rich_help_panel=get_command_group_help_panel())
app.add_typer(task_command.runner_app, name="")


@app.command(name='clone', no_args_is_help=True, help=__("Clone project repository to empty directory"), **get_command_metadata(CliCommand.PROJECT_CLONE))
def clone(
        project_public_id: Optional[str] = typer.Option(
            None,
            "--project-id",
            "-pid",
            help=__("Project ID. ID or name is required"),
            is_eager=False,
        ),
        project_slug: Optional[str] = typer.Option(
            None,
            "--project-name",
            "-pn",
            help=__("Project name. ID or name is required."),
            is_eager=False,
        ),
        working_directory: Optional[str] = typer.Option(
            None,
            "--working-directory",
            "-wd",
            help=__("Full path to the working directory: current directory used by default"),
            is_eager=False,
        ),
):
    command_name = CliCommand.PROJECT_CLONE
    app_logger.info(f'Running {command_name} from {get_current_directory()}')
    check_command_permission(command_name)

    if sum(v is not None for v in [project_public_id, project_slug]) != 1:
        typer.echo("Provide a single identifier for the project - name or ID.")
        raise typer.Exit(1)

    if not working_directory:
        project_dir_name = project_public_id if project_slug is None else project_slug
        working_directory = get_current_directory().joinpath(project_dir_name)

    service_factory = validate_config_and_get_service_factory(working_directory=working_directory)
    project_service = service_factory.get_project_service()

    project_service.clone_project(
        project_slug=project_slug,
        project_public_id=project_public_id,
    )

    raise typer.Exit(0)


@app.command(name='init', no_args_is_help=True, help=__("Initialize project repository with existing files"), **get_command_metadata(CliCommand.PROJECT_INIT))
def init(
        project_public_id: Optional[str] = typer.Option(
            None,
            "--project-id",
            "-pid",
            help=__("Project ID. ID or name is required"),
            is_eager=False,
        ),
        project_slug: Optional[str] = typer.Option(
            None,
            "--project-name",
            "-pn",
            help=__("Project name. ID or name is required."),
            is_eager=False,
        ),
        working_directory: Optional[str] = typer.Option(
            None,
            "--working-directory",
            "-wd",
            help=__("Full path to working directory"),
            is_eager=False,
        ),
):
    command_name = CliCommand.PROJECT_INIT
    app_logger.info(f'Running {command_name} from {get_current_directory()}')
    check_command_permission(command_name)

    if sum(v is not None for v in [project_public_id, project_slug]) != 1:
        typer.echo("Provide a single identifier for the project - name or ID.")
        raise typer.Exit(1)

    service_factory = validate_config_and_get_service_factory(working_directory=working_directory)
    project_service = service_factory.get_project_service()
    project_config = service_factory.get_config_provider().read_project_config()

    if project_config:
        typer.echo(__("Directory is initialized and already contains working project"))
        raise typer.Exit(1)

    project_service.init_project(
        project_slug=project_slug,
        project_public_id=project_public_id,
    )

    raise typer.Exit(0)



@app.command(name='checkout', no_args_is_help=True, help=__("Checkout project repository to a specific reference"), **get_command_metadata(CliCommand.PROJECT_CHECKOUT))
def checkout_project(
        task_public_id: Optional[str] = typer.Option(
            None,
            "--task-id",
            "-tid",
            help="Task ID to checkout",
            is_eager=False,
        ),
        branch_name: Optional[str] = typer.Option(
            None,
            "--branch",
            "-b",
            help="Branch name to checkout. Use '/' value to checkout to the main branch.",
            is_eager=False,
        ),
        working_directory: Optional[str] = typer.Option(
            None,
            "--working-directory",
            "-wd",
            help=__("Full path to working directory"),
            is_eager=False,
        ),
):
    command_name = CliCommand.PROJECT_CHECKOUT
    app_logger.info(f'Running {command_name} from {get_current_directory()}')
    check_command_permission(command_name)

    if sum(v is not None for v in [branch_name, task_public_id]) != 1:
        typer.echo("Provide a single identifier for checkout - task ID or branch name.")
        raise typer.Exit(1)

    service_factory = validate_config_and_get_service_factory(working_directory=working_directory)
    project_service = service_factory.get_project_service()

    final_branch_name = branch_name
    if branch_name == "/":
        final_branch_name = None

    project_service.checkout_project(
        task_public_id=task_public_id,
        branch_name=final_branch_name,
    )

    raise typer.Exit(0)


@app.command(name='pull', help=__("Pulls the changes from the remote project repository. Equivalent to 'git pull'."), **get_command_metadata(CliCommand.PROJECT_PULL))
def pull_project(
        working_directory: Optional[str] = typer.Option(
            None,
            "--working-directory",
            "-wd",
            help=__("Full path to working directory"),
            is_eager=False,
        ),
):
    command_name = CliCommand.PROJECT_PULL
    app_logger.info(f'Running {command_name} from {get_current_directory()}')
    check_command_permission(command_name)

    service_factory = validate_config_and_get_service_factory(working_directory=working_directory)
    project_service = service_factory.get_project_service()

    project_service.pull_project()

    raise typer.Exit(0)


@app.command(name='reset', help=__("Resets the current project branch to remote counterpart. All working tree changes will be lost. Equivalent to 'git fetch && git reset --hard origin/{ref}'."), **get_command_metadata(CliCommand.PROJECT_RESET))
def reset_project(
        working_directory: Optional[str] = typer.Option(
            None,
            "--working-directory",
            "-wd",
            help=__("Full path to working directory"),
            is_eager=False,
        ),
):
    command_name = CliCommand.PROJECT_RESET
    app_logger.info(f'Running {command_name} from {get_current_directory()}')
    check_command_permission(command_name)

    service_factory = validate_config_and_get_service_factory(working_directory=working_directory)
    project_service = service_factory.get_project_service()

    project_service.reset_project()

    raise typer.Exit(0)


@config_app.command(name='set-default-container', no_args_is_help=True, help=__("Set default docker container for a project installation"), **get_command_metadata(CliCommand.PROJECT_CONFIG_SET_DEFAULT_CONTAINER))
def set_default_container(
        docker_container_public_id: Optional[str] = typer.Option(
            None,
            '--container-id',
            '-cid',
            help=__("Docker container ID"),
            is_eager=False,
        ),
        docker_container_slug: Optional[str] = typer.Option(
            None,
            '--container-name',
            '-cn',
            help=__("Docker container name"),
            is_eager=False,
        ),
        unset_default_container: Optional[bool] = typer.Option(
            False,
            "--unset",
            "-u",
            help=__("Unsets the default docker container"),
            is_eager=False,
        ),
        working_directory: Optional[str] = typer.Option(
            None,
            "--working-directory",
            "-wd",
            help=__("Full path to working directory"),
            is_eager=False,
        ),
):
    command_name = CliCommand.PROJECT_CONFIG_SET_DEFAULT_CONTAINER
    app_logger.info(f'Running {command_name} from {get_current_directory()}')
    check_command_permission(command_name)

    container_args_count = sum(v is not None for v in [docker_container_public_id, docker_container_slug])
    if container_args_count > 1:
        typer.echo("Provide a single identifier for the container - name or ID.")
        raise typer.Exit(1)

    service_factory = validate_config_and_get_service_factory(working_directory=working_directory)

    if unset_default_container and container_args_count > 0:
        typer.echo("Cannot provide container identifier and '--unset' flag simultaneously")
        raise typer.Exit(1)

    if not unset_default_container and container_args_count != 1:
        typer.echo("Provide container identifier or use '--unset' flag")
        raise typer.Exit(1)

    project_service = service_factory.get_project_service()

    project_service.set_default_container(
        container_public_id=docker_container_public_id,
        container_slug=docker_container_slug,
    )

    raise typer.Exit(0)


@config_app.command(name='get', no_args_is_help=False, help=__("View config for a local project installation"), **get_command_metadata(CliCommand.PROJECT_CONFIG_GET))
def get_project_config(
        working_directory: Optional[str] = typer.Option(
            None,
            "--working-directory",
            "-wd",
            help=__("Full path to working directory"),
            is_eager=False,
        ),
):
    command_name = CliCommand.PROJECT_CONFIG_GET
    app_logger.info(f'Running {command_name} from {get_current_directory()}')
    check_command_permission(command_name)

    service_factory = validate_config_and_get_service_factory(working_directory=working_directory)
    project_service = service_factory.get_project_service()

    project_service.print_project_config()

    raise typer.Exit(0)
