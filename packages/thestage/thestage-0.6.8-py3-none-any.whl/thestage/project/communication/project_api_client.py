from typing import Optional

from thestage.config.business.config_provider import ConfigProvider
from thestage.services.clients.thestage_api.core.api_client_core import TheStageApiClientCore

from thestage.project.dto.project_response import ProjectDto, ProjectViewResponse
from thestage.project.dto.get_deploy_ssh_key_request import ProjectGetDeploySshKeyRequest
from thestage.project.dto.get_deploy_ssh_key_response import ProjectGetDeploySshKeyResponse


class ProjectApiClient(TheStageApiClientCore):
    def __init__(self, config_provider: ConfigProvider):
        super().__init__(url=config_provider.get_config().main.thestage_api_url)
        self.__config_provider = config_provider

    def get_project(self, slug: Optional[str], public_id: Optional[str]) -> Optional[ProjectDto]:
        data = {
            "projectSlug": slug,
            "projectPublicId": public_id,
        }

        response = self._request(
            method='POST',
            url='/user-api/v2/project/view',
            data=data,
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        result = ProjectViewResponse.model_validate(response) if response else None
        project = ProjectDto.model_validate(result.project) if result else None
        return project if result and result.is_success else None

    def get_project_deploy_ssh_key(self, public_id: str) -> str:
        request = ProjectGetDeploySshKeyRequest(
            projectPublicId=public_id,
        )

        response = self._request(
            method='POST',
            url='/user-api/v1/project/get-deploy-ssh-key',
            data=request.model_dump(),
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        result = ProjectGetDeploySshKeyResponse.model_validate(response) if response else None
        return result.privateKey if result and result.is_success else None