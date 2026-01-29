from typing import Optional, List, Dict

from thestage.config.business.config_provider import ConfigProvider
from thestage.global_dto.enums.order_direction_type import OrderDirectionType
from thestage.services.clients.thestage_api.core.api_client_core import TheStageApiClientCore
from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse
from thestage.services.clients.thestage_api.dtos.entity_filter_request import EntityFilterRequest
from thestage.services.clients.thestage_api.dtos.paginated_entity_list import PaginatedEntityList

from thestage.docker_container.dto.container_action_request import DockerContainerActionRequest
from thestage.docker_container.dto.container_response import (
    DockerContainerDto,
    DockerContainerViewResponse,
    ContainerBusinessStatusMapperResponse
)
from thestage.docker_container.dto.docker_container_list_request import DockerContainerListRequest
from thestage.docker_container.dto.docker_container_list_response import DockerContainerListResponse


class DockerContainerApiClient(TheStageApiClientCore):
    def __init__(self, config_provider: ConfigProvider):
        super().__init__(url=config_provider.get_config().main.thestage_api_url)
        self.__config_provider = config_provider

    def get_container_list(
            self,
            project_public_id: Optional[str] = None,
            project_slug: Optional[str] = None,
            statuses: List[str] = [],
            page: int = 1,
            limit: int = 10,
    ) -> PaginatedEntityList[DockerContainerDto]:
        request = DockerContainerListRequest(
            statuses=statuses,
            projectPublicId=project_public_id,
            projectSlug=project_slug,
            entityFilterRequest=EntityFilterRequest(
                orderByField="createdAt",
                orderByDirection=OrderDirectionType.DESC,
                page=page,
                limit=limit,
            ),
        )

        response = self._request(
            method='POST',
            url='/user-api/v2/docker-container/list',
            data=request.model_dump(),
            token=self.__config_provider.get_config().main.thestage_auth_token
        )

        result = DockerContainerListResponse.model_validate(response) if response else None
        # return result.paginatedList.entities, result.paginatedList.pagination_data.total_pages if result and result.is_success else None
        return result.paginatedList if result and result.is_success else None

    def get_container(
            self,
            container_slug: Optional[str] = None,
            container_public_id: Optional[str] = None,
    ) -> Optional[DockerContainerDto]:
        data = {
            "dockerContainerPublicId": container_public_id,
            "dockerContainerSlug": container_slug,
        }

        response = self._request(
            method='POST',
            url='/user-api/v2/docker-container/view',
            data=data,
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        return DockerContainerViewResponse.model_validate(response).docker_container if response else None

    def container_action(
            self,
            request_param: DockerContainerActionRequest,
    ) -> TheStageBaseResponse:

        response = self._request(
            method='POST',
            url='/user-api/v2/docker-container/action',
            data=request_param.model_dump(by_alias=True),
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        result = TheStageBaseResponse.model_validate(response) if response else None
        return result

    def get_container_business_status_map(self) -> Optional[Dict[str, str]]:
        response = self._request(
            method='POST',
            url='/user-api/v1/docker-container/status-localized-mapping',
            data=None,
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        data = ContainerBusinessStatusMapperResponse.model_validate(response) if response else None
        return data.docker_container_status_map if data else None