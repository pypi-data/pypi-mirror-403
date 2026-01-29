from typing import Optional, List, Dict

from thestage.config.business.config_provider import ConfigProvider
from thestage.services.clients.thestage_api.core.api_client_core import TheStageApiClientCore
from thestage.services.clients.thestage_api.dtos.paginated_entity_list import PaginatedEntityList

from thestage.instance.dto.instance_rented_response import (
    InstanceRentedListResponse,
    InstanceRentedDto,
    InstanceRentedItemResponse,
    InstanceRentedBusinessStatusMapperResponse
)
from thestage.instance.dto.selfhosted_instance_response import (
    SelfHostedInstanceListResponse,
    SelfHostedInstanceDto,
    SelfHostedRentedItemResponse,
    SelfHostedRentedRentedBusinessStatusMapperResponse
)


class InstanceApiClient(TheStageApiClientCore):
    def __init__(self, config_provider: ConfigProvider):
        super().__init__(url=config_provider.get_config().main.thestage_api_url)
        self.__config_provider = config_provider

    def get_rented_instance_list(
            self,
            statuses: List[str],
            page: int = 1,
            limit: int = 10,
    ) -> PaginatedEntityList[InstanceRentedDto]:
        data = {
            #"statuses": [item.value for item in statuses],
            "entityFilterRequest": {
                "orderByField": "createdAt",
                "orderByDirection": "DESC",
                "page": page,
                "limit": limit
            },
        }

        if statuses:
            data['businessStatuses'] = statuses

        response = self._request(
            method='POST',
            url='/user-api/v3/instance-rented/list',
            data=data,
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        result = InstanceRentedListResponse.model_validate(response) if response else None
        return result.paginated_list if result and result.paginated_list else ([], None)

    def get_rented_business_status_map(self) -> Optional[Dict[str, str]]:
        response = self._request(
            method='POST',
            url='/user-api/v2/instance-rented/business-status-localized-map',
            data=None,
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        data = InstanceRentedBusinessStatusMapperResponse.model_validate(response) if response else None

        return data.instance_rented_business_status_map if data else None



    def get_rented_instance(
            self,
            instance_public_id: Optional[str] = None,
            instance_slug: Optional[str] = None,
    ) -> Optional[InstanceRentedDto]:
        if not instance_slug and not instance_public_id:
            return None

        data = {
            "instanceRentedPublicId": instance_public_id,
            "instanceRentedSlug": instance_slug,
        }

        response = self._request(
            method='POST',
            url='/user-api/v3/instance-rented/view',
            data=data,
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        return InstanceRentedItemResponse.model_validate(response).instance_rented if response else None

    def get_selfhosted_instance(
            self,
            instance_public_id: Optional[str] = None,
            instance_slug: Optional[str] = None,
    ) -> Optional[SelfHostedInstanceDto]:
        if not instance_slug and not instance_public_id:
            return None

        data = {
            "selfhostedInstancePublicId": instance_public_id,
            "selfhostedInstanceSlug": instance_slug,
        }

        response = self._request(
            method='POST',
            url='/user-api/v3/self-hosted-instance/view',
            data=data,
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        return SelfHostedRentedItemResponse.model_validate(response).selfhosted_instance if response else None

    def get_selfhosted_instance_list(
            self,
            statuses: List[str],
            page: int = 1,
            limit: int = 10,
    ) -> PaginatedEntityList[SelfHostedInstanceDto]:
        data = {
            "entityFilterRequest": {
                "orderByField": "createdAt",
                "orderByDirection": "DESC",
                "page": page,
                "limit": limit
            }
        }

        if statuses:
            data['businessStatuses'] = statuses

        response = self._request(
            method='POST',
            url='/user-api/v3/self-hosted-instance/list',
            data=data,
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        result = SelfHostedInstanceListResponse.model_validate(response) if response else None
        return result.paginated_list if result and result.paginated_list else ([], None)

    def get_selfhosted_business_status_map(self) -> Optional[Dict[str, str]]:
        response = self._request(
            method='POST',
            url='/user-api/v2/self-hosted-instance/business-status-localized-map',
            data=None,
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        data = SelfHostedRentedRentedBusinessStatusMapperResponse.model_validate(response) if response else None
        return data.selfhosted_instance_business_status_map if data else None