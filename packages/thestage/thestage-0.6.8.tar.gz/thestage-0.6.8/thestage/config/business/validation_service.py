import typer

from thestage.config.business.config_provider import ConfigProvider
from thestage.config.dto.config_entity import ConfigEntity
from thestage.i18n.translation import __
from thestage.services.clients.thestage_api.core.api_client_core import TheStageApiClientCore


class ValidationService:
    _core_client: TheStageApiClientCore = None
    _config_provider: ConfigProvider = None

    def __init__(
            self,
            core_client: TheStageApiClientCore,
            config_provider: ConfigProvider,
    ):
        self._core_client = core_client
        self._config_provider = config_provider


    def check_token(self):
        config = self._config_provider.get_config()
        token = config.main.thestage_auth_token
        if not token:
            token: str = typer.prompt(
                text=f'Authenticate using valid TheStage AI access token ({config.main.thestage_api_url})',
                show_choices=False,
                type=str,
                show_default=False,
            )

# TODO this fails with 503 error - AttributeError("'bytes' object has no attribute 'text'") from _parse_api_response method in core
        if not token:
            return

        token_validate_response = self._core_client.validate_token(token=token)
        is_valid = token_validate_response.is_success if token_validate_response else False
        if not is_valid:
            typer.echo(__(
                'Access token is invalid: generate access token using TheStage AI WebApp'
            ))
            raise typer.Exit(1)

        if config.main.thestage_auth_token != token:
            config.main.thestage_auth_token = token
            self._config_provider.update_config(updated_config=config)
            self._config_provider.update_allowed_commands_and_is_token_valid(validate_token_response=token_validate_response)


    @staticmethod
    def is_present_token(config: ConfigEntity) -> bool:
        present_token = True
        if not config:
            present_token = False
        else:
            if not config.main.thestage_auth_token:
                present_token = False

        return present_token
