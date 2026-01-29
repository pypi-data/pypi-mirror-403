from typing import Optional, List

import typer
from typing_extensions import Annotated

from thestage.cli_command import CliCommand
from thestage.cli_command_helper import get_command_metadata, check_command_permission
from thestage.controllers.utils_controller import validate_config_and_get_service_factory, get_current_directory
from thestage.helpers.logger.app_logger import app_logger
from thestage.i18n.translation import __
from thestage.logging.business.logging_service import LoggingService
from thestage.task.dto.task import Task

app = typer.Typer(no_args_is_help=True, help=__("Manage project tasks"))
runner_app = typer.Typer(help="Project Runner")

@runner_app.command(name='run', no_args_is_help=True, help=__("Run a task within the project. By default, it uses the latest commit from the main branch and streams real-time task logs."), **get_command_metadata(CliCommand.PROJECT_RUN))
def run(
        command: Annotated[List[str], typer.Argument(
            help=__("Command to run (required)"),
        )],
        commit_hash: Optional[str] = typer.Option(
            None,
            '--commit-hash',
            '-hash',
            help=__("Commit hash to use. By default, the current HEAD commit is used."),
            is_eager=False,
        ),
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
        working_directory: Optional[str] = typer.Option(
            None,
            "--working-directory",
            "-wd",
            help=__("Full path to working directory"),
            show_default=False,
            is_eager=False,
        ),
        enable_log_stream: Optional[bool] = typer.Option(
            True,
            " /--no-logs",
            " /-nl",
            help=__("Disable real-time log streaming"),
            is_eager=False,
        ),
        task_title: Optional[str] = typer.Option(
            None,
            "--title",
            "-t",
            help=__("Provide a custom task title. Git commit message is used by default."),
            is_eager=False,
        ),
        files_to_add: Optional[str] = typer.Option(
            None,
            "--files-add",
            "-fa",
            help=__("Files to add to the commit. You can add files by their relative path from the working directory with a comma as a separator."),
            is_eager=False,
        ),
        is_skip_auto_commit: Optional[bool] = typer.Option(
            False,
            "--skip-autocommit",
            "-sa",
            help=__("Skip automatic commit of the changes"),
            is_eager=False,
        ),
):
    command_name = CliCommand.PROJECT_RUN
    app_logger.info(f'Running {command_name} from {get_current_directory()}')
    check_command_permission(command_name)

    if sum(v is not None for v in [docker_container_public_id, docker_container_slug]) != 1:
        typer.echo("Provide a single identifier for the container - name or ID.")
        raise typer.Exit(1)

    if not command:
        typer.echo(__('Command is required'))
        raise typer.Exit(1)

    service_factory = validate_config_and_get_service_factory(working_directory=working_directory)
    task_service = service_factory.get_task_service()

    task: Optional[Task] = task_service.project_run_task(
        run_command=" ".join(command),
        commit_hash=commit_hash,
        docker_container_public_id=docker_container_public_id,
        docker_container_slug=docker_container_slug,
        task_title=task_title,
        files_to_add=files_to_add,
        is_skip_auto_commit=is_skip_auto_commit,
    )

    if enable_log_stream:
        logging_service: LoggingService = service_factory.get_logging_service()
        logging_service.stream_task_logs_with_controls(task_public_id=task.public_id)

    raise typer.Exit(0)


@app.command(name='cancel', no_args_is_help=True, help=__("Cancel a task by ID"), **get_command_metadata(CliCommand.PROJECT_TASK_CANCEL))
def cancel_task(
        task_id: Annotated[str, typer.Argument(
            help=__("Task ID (required)"),
        )],
):
    command_name = CliCommand.PROJECT_TASK_CANCEL
    app_logger.info(f'Running {command_name} from {get_current_directory()}')
    check_command_permission(command_name)

    if not task_id:
        typer.echo('Task ID is required')
        raise typer.Exit(1)

    service_factory = validate_config_and_get_service_factory()
    task_service = service_factory.get_task_service()

    task_service.cancel_task(
        task_public_id=task_id
    )

    raise typer.Exit(0)


@app.command("ls", help=__("List tasks"), **get_command_metadata(CliCommand.PROJECT_TASK_LS))
def list_runs(
        project_public_id: Optional[str] = typer.Option(
            None,
            '--project-id',
            '-pid',
            help=__("Project ID. By default, project info is taken from the current directory"),
            is_eager=False,
        ),
        project_slug: Optional[str] = typer.Option(
            None,
            '--project-name',
            '-pn',
            help=__("Project name. By default, project info is taken from the current directory"),
            is_eager=False,
        ),
        row: int = typer.Option(
            5,
            '--row',
            '-r',
            help=__("Set number of rows displayed per page"),
            is_eager=False,
        ),
        page: int = typer.Option(
            1,
            '--page',
            '-p',
            help=__("Set starting page for displaying output"),
            is_eager=False,
        ),
):
    command_name = CliCommand.PROJECT_TASK_LS
    app_logger.info(f'Running {command_name} from {get_current_directory()}')
    check_command_permission(command_name)

    if sum(v is not None for v in [project_public_id, project_slug]) > 1:
        typer.echo("Provide a single identifier for project - ID or name.")
        raise typer.Exit(1)

    service_factory = validate_config_and_get_service_factory()
    task_service = service_factory.get_task_service()

    task_service.print_task_list(project_public_id=project_public_id, project_slug=project_slug, row=row, page=page)

    typer.echo(__("Tasks listing complete"))
    raise typer.Exit(0)


@app.command(name="logs", no_args_is_help=True, help=__("Stream real-time task logs or view last logs for a task"), **get_command_metadata(CliCommand.PROJECT_TASK_LOGS))
def task_logs(
        task_id: Optional[str] = typer.Argument(help=__("Task ID"),),
        logs_number: Optional[int] = typer.Option(
            None,
            '--number',
            '-n',
            help=__("Display a number of latest log entries. No real-time stream if provided."),
            is_eager=False,
        ),
):
    command_name = CliCommand.PROJECT_TASK_LOGS
    app_logger.info(f'Running {command_name} from {get_current_directory()}')
    check_command_permission(command_name)

    if not task_id:
        typer.echo(__('Task ID is required'))
        raise typer.Exit(1)

    service_factory = validate_config_and_get_service_factory()
    logging_service: LoggingService = service_factory.get_logging_service()

    if logs_number is None:
        logging_service.stream_task_logs_with_controls(task_public_id=task_id)
    else:
        logging_service.print_last_task_logs(task_public_id=task_id, logs_number=logs_number)

    app_logger.info(f'Task logs - end')
    raise typer.Exit(0)