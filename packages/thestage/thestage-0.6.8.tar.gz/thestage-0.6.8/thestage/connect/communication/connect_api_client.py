from typing import Optional

from thestage.config.business.config_provider import ConfigProvider
from thestage.services.clients.thestage_api.core.api_client_core import TheStageApiClientCore
from thestage.connect.dto.add_ssh_key_to_user_request import AddSshKeyToUserRequest
from thestage.connect.dto.add_ssh_key_to_user_response import AddSshKeyToUserResponse
from thestage.connect.dto.is_user_has_public_ssh_key_request import IsUserHasSshPublicKeyRequest
from thestage.connect.dto.is_user_has_public_ssh_key_response import IsUserHasSshPublicKeyResponse
from thestage.connect.dto.add_ssh_public_key_to_instance_request import AddSshPublicKeyToInstanceRequest
from thestage.connect.dto.add_ssh_public_key_to_instance_response import AddSshPublicKeyToInstanceResponse
from thestage.connect.dto.connect_resolve_response import ConnectResolveOptionsResponse


class ConnectApiClient(TheStageApiClientCore):
    def __init__(self, config_provider: ConfigProvider):
        super().__init__(url=config_provider.get_config().main.thestage_api_url)
        self.__config_provider = config_provider

    def add_public_ssh_key_to_user(self, public_key: str, note: str) -> AddSshKeyToUserResponse:
        request = AddSshKeyToUserRequest(
            sshKey=public_key,
            note=note
        )

        response = self._request(
            method='POST',
            url='/user-api/v2/ssh-key/add-public-key-to-user',
            data=request.model_dump(),
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        result = AddSshKeyToUserResponse.model_validate(response) if response else None
        return result


    def is_user_has_ssh_public_key(self, public_key: str) -> IsUserHasSshPublicKeyResponse:
        request = IsUserHasSshPublicKeyRequest(
            sshKey=public_key,
        )

        response = self._request(
            method='POST',
            url='/user-api/v2/ssh-key/is-user-has-public-ssh-key',
            data=request.model_dump(),
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        result = IsUserHasSshPublicKeyResponse.model_validate(response) if response else None
        return result


    def add_public_ssh_key_to_instance_rented(self, instance_rented_public_id: str,
                                              ssh_key_pair_public_id: str) -> AddSshPublicKeyToInstanceResponse:
        request = AddSshPublicKeyToInstanceRequest(
            instanceRentedPublicId=instance_rented_public_id,
            sshPublicKeyPublicId=ssh_key_pair_public_id,
        )

        response = self._request(
            method='POST',
            url='/user-api/v2/ssh-key/add-public-ssh-key-to-instance-rented',
            data=request.model_dump(),
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        result = AddSshPublicKeyToInstanceResponse.model_validate(response) if response else None
        return result

    def resolve_user_input(
            self,
            entity_identifier: str
    ) -> Optional[ConnectResolveOptionsResponse]:
        data = {
            "entityIdentifier": entity_identifier,
        }

        response = self._request(
            method='POST',
            url='/user-api/v1/resolve-user-input',
            data=data,
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        return ConnectResolveOptionsResponse.model_validate(response) if response else None