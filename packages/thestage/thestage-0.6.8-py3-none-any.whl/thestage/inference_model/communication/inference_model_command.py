import time
import re
from typing import Optional, List

import typer

from thestage.cli_command import CliCommand
from thestage.cli_command_helper import get_command_metadata, check_command_permission
from thestage.controllers.utils_controller import validate_config_and_get_service_factory, get_current_directory
from thestage.helpers.logger.app_logger import app_logger
from thestage.i18n.translation import __
from thestage.inference_model.business.inference_model_service import InferenceModelService
from thestage.logging.business.logging_service import LoggingService
from thestage.project.business.project_service import ProjectService

app = typer.Typer(no_args_is_help=True, help="Manage project inference simulator models")
@app.command("ls", help=__("List inference simulator models"), **get_command_metadata(CliCommand.PROJECT_MODEL_LS))
def list_inference_simulator_models(
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
        statuses: List[str] = typer.Option(
            None,
            '--status',
            '-s',
            help=__("Filter by status, use --status all to list all inference simulator models"),
            is_eager=False,
        ),
):
    command_name = CliCommand.PROJECT_MODEL_LS
    app_logger.info(f'Running {command_name} from {get_current_directory()}')
    check_command_permission(command_name)

    if sum(v is not None for v in [project_public_id, project_slug]) > 1:
        typer.echo("Provide a single identifier for project - ID or name.")
        raise typer.Exit(1)

    service_factory = validate_config_and_get_service_factory()
    inference_model_service: InferenceModelService = service_factory.get_inference_model_service()

    inference_model_service.print_inference_simulator_model_list(
        project_public_id=project_public_id,
        project_slug=project_slug,
        statuses=statuses,
        row=row,
        page=page
    )

    typer.echo(__("Inference simulator models listing complete"))
    raise typer.Exit(0)


@app.command("deploy-instance", no_args_is_help=True, help=__("Deploy inference simulator model to an instance"), **get_command_metadata(CliCommand.PROJECT_MODEL_DEPLOY_INSTANCE))
def deploy_inference_simulator_model_to_instance(
        model_public_id: Optional[str] = typer.Option(
            None,
            '--model-id',
            '-mid',
            help="Inference simulator model ID",
            is_eager=False,
        ),
        model_slug: Optional[str] = typer.Option(
            None,
            '--model-name',
            '-mn',
            help="Inference simulator model name",
            is_eager=False,
        ),
        rented_instance_public_id: Optional[str] = typer.Option(
            None,
            '--rented-instance-id',
            '-rid',
            help=__("Rented instance ID on which the inference simulator will run"),
            is_eager=False,
        ),
        rented_instance_slug: Optional[str] = typer.Option(
            None,
            '--rented-instance-name',
            '-rn',
            help=__("Rented instance name on which the inference simulator will run"),
            is_eager=False,
        ),
        self_hosted_instance_public_id: Optional[str] = typer.Option(
            None,
            '--self-hosted-instance-id',
            '-sid',
            help=__("Self-hosted instance ID on which the inference simulator will run"),
            is_eager=False,
        ),
        self_hosted_instance_slug: Optional[str] = typer.Option(
            None,
            '--self-hosted-instance-name',
            '-sn',
            help=__("Self-hosted instance name on which the inference simulator will run"),
            is_eager=False,
        ),
        working_directory: Optional[str] = typer.Option(
            None,
            "--working-directory",
            "-wd",
            help=__("Full path to working directory. By default, the current directory is used"),
            show_default=False,
            is_eager=False,
        ),
        enable_log_stream: Optional[bool] = typer.Option(
            True,
            "--no-logs",
            "-nl",
            help=__("Disable real-time log streaming"),
            is_eager=False,
        ),
):
    command_name = CliCommand.PROJECT_MODEL_DEPLOY_INSTANCE
    app_logger.info(f'Running {command_name} from {get_current_directory()}')
    check_command_permission(command_name)

    if model_slug and not re.match(r"^[a-zA-Z0-9-]+$", model_slug):
        raise typer.BadParameter(__("Invalid UID format. UID can only contain letters, numbers, and hyphens."))

    new_inference_simulator_slug = f"{model_slug}-{int(time.time())}"

    service_factory = validate_config_and_get_service_factory(working_directory=working_directory)
    inference_model_service: InferenceModelService = service_factory.get_inference_model_service()

    inference_simulator_public_id=inference_model_service.project_deploy_inference_simulator_model_to_instance(
        model_public_id=model_public_id,
        model_slug=model_slug,
        new_inference_simulator_slug=new_inference_simulator_slug,
        rented_instance_public_id=rented_instance_public_id,
        rented_instance_slug=rented_instance_slug,
        self_hosted_instance_public_id=self_hosted_instance_public_id,
        self_hosted_instance_slug=self_hosted_instance_slug,
    )

    if enable_log_stream:
        logging_service: LoggingService = service_factory.get_logging_service()

        logging_service.stream_inference_simulator_logs_with_controls(
            public_id=inference_simulator_public_id
        )
    raise typer.Exit(0)


@app.command("deploy-sagemaker", no_args_is_help=True, help=__("Deploy inference simulator model to SageMaker"), **get_command_metadata(CliCommand.PROJECT_MODEL_DEPLOY_SAGEMAKER))
def deploy_inference_simulator_model_to_sagemaker(
        model_public_id: Optional[str] = typer.Option(
            None,
            '--model-id',
            '-mid',
            help="Inference simulator model ID",
            is_eager=False,
        ),
        model_slug: Optional[str] = typer.Option(
            None,
            '--model-name',
            '-mn',
            help="Inference simulator model name",
            is_eager=False,
        ),
        arn: Optional[str] = typer.Option(
            None,
            '--amazon-resource-name',
            '-arn',
            help=__("Amazon Resource Name of the IAM Role to use, e.g., arn:aws:iam::{aws_account_id}:role/{role}"),
            is_eager=False,
        ),
        working_directory: Optional[str] = typer.Option(
            None,
            "--working-directory",
            "-wd",
            help=__("Full path to working directory. By default, the current directory is used"),
            show_default=False,
            is_eager=False,
        ),
        instance_type: Optional[str] = typer.Option(
            None,
            '--instance-type',
            '-it',
            help=__("Instance type on which the inference simulator model will be deployed"),
            is_eager=False,
        ),
        initial_variant_weight: Optional[float] = typer.Option(
            None,
            "--initial-variant-weight",
            "-ivw",
            help=__("Initial Variant Weight. By default 1.0"),
            show_default=False,
            is_eager=False,
        ),
        initial_instance_count: Optional[int] = typer.Option(
            None,
            "--initial-instance-count",
            "-iic",
            help=__("Initial Instance Count"),
            show_default=False,
            is_eager=False,
        ),

):
    command_name = CliCommand.PROJECT_MODEL_DEPLOY_SAGEMAKER
    app_logger.info(f'Running {command_name} from {get_current_directory()}')
    check_command_permission(command_name)

    if sum(v is not None for v in [model_public_id, model_slug]) != 1:
        typer.echo("Provide a single identifier for inference simulator model - ID or name.")
        raise typer.Exit(1)

    if model_slug and not re.match(r"^[a-zA-Z0-9-]+$", model_slug):
        raise typer.BadParameter(__("Invalid UID format. UID can only contain letters, numbers, and hyphens."))

    service_factory = validate_config_and_get_service_factory(working_directory=working_directory)
    inference_model_service: InferenceModelService = service_factory.get_inference_model_service()

    inference_model_service.project_deploy_inference_simulator_model_to_sagemaker(
        model_public_id=model_public_id,
        model_slug=model_slug,
        arn=arn,
        instance_type=instance_type,
        initial_variant_weight=initial_variant_weight,
        initial_instance_count=initial_instance_count,
    )
