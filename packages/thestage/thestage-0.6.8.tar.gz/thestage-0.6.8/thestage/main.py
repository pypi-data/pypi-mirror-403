import traceback

from thestage.cli_command_helper import get_command_group_help_panel
from thestage.helpers.logger.app_logger import app_logger, get_log_path_from_os
from thestage.services.clients.thestage_api.core.api_client_core import TheStageApiClientCore
from thestage.services.service_factory import ServiceFactory
from rich import print


def main():
    service_factory = ServiceFactory()
    config_provider = service_factory.get_config_provider()
    config = config_provider.build_config()

    try:
        try:
            api_client = TheStageApiClientCore(url=config.main.thestage_api_url)
            token_info = api_client.validate_token(config.main.thestage_auth_token)
            config_provider.update_allowed_commands_and_is_token_valid(validate_token_response=token_info)
        except Exception as e:
            app_logger.error(f'{traceback.format_exc()}')
            print('Error connecting to TheStage servers')  # TODO inquire what we want here if backend is offline
            print(f'Application logs path: {str(get_log_path_from_os())}')
            return

        from thestage.controllers import base_controller
        from thestage.config.communication import config_command
        from thestage.project.communication import project_command
        from thestage.inference_simulator.communication import inference_simulator_command
        from thestage.inference_model.communication import inference_model_command
        from thestage.task.communication import task_command
        from thestage.instance.communication import instance_command
        from thestage.docker_container.communication import docker_command

        project_command.app.add_typer(
            inference_simulator_command.app,
            name="inference-simulator",
            rich_help_panel=get_command_group_help_panel()
        )
        project_command.app.add_typer(
            inference_model_command.app,
            name="model",
            rich_help_panel=get_command_group_help_panel()
        )
        project_command.app.add_typer(
            task_command.app,
            name="task",
            rich_help_panel=get_command_group_help_panel()
        )

        base_controller.app.add_typer(
            project_command.app,
            name="project",
            rich_help_panel=get_command_group_help_panel()
        )

        base_controller.app.add_typer(
            docker_command.app,
            name="container",
            rich_help_panel=get_command_group_help_panel()
        )
        base_controller.app.add_typer(
            instance_command.app,
            name="instance",
            rich_help_panel=get_command_group_help_panel()
        )
        base_controller.app.add_typer(
            config_command.app,
            name="config",
            rich_help_panel=get_command_group_help_panel()
        )

        base_controller.app()
    except KeyboardInterrupt:
        print('THESTAGE: Keyboard Interrupt')
