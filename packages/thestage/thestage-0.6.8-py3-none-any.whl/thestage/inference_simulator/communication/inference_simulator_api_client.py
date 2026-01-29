from typing import Optional, List, Dict

from thestage.config.business.config_provider import ConfigProvider
from thestage.global_dto.enums.order_direction_type import OrderDirectionType
from thestage.helpers.error_handler import error_handler
from thestage.services.clients.thestage_api.core.api_client_core import TheStageApiClientCore
from thestage.services.clients.thestage_api.dtos.entity_filter_request import EntityFilterRequest
from thestage.services.clients.thestage_api.dtos.paginated_entity_list import PaginatedEntityList

from thestage.inference_simulator.dto.inference_simulator import InferenceSimulator
from thestage.inference_simulator.dto.inference_simulator_list_request import InferenceSimulatorListRequest
from thestage.inference_simulator.dto.inference_simulator_list_response import InferenceSimulatorListResponse
from thestage.inference_simulator.dto.start_inference_simulator_request import StartInferenceSimulatorRequest
from thestage.inference_simulator.dto.start_inference_simulator_response import StartInferenceSimulatorResponse
from thestage.inference_simulator.dto.inference_simulator_response import InferenceSimulatorStatusMapperResponse
from thestage.inference_simulator.dto.get_inference_simulator_request import GetInferenceSimulatorRequest
from thestage.inference_simulator.dto.get_inference_simulator_response import GetInferenceSimulatorResponse


class InferenceSimulatorApiClient(TheStageApiClientCore):
    def __init__(self, config_provider: ConfigProvider):
        super().__init__(url=config_provider.get_config().main.thestage_api_url)
        self.__config_provider = config_provider

    def get_inference_simulator_list(
            self,
            project_public_id: Optional[str],
            project_slug: Optional[str],
            statuses: List[str] = [],
            page: int = 1,
            limit: int = 10,
    ) -> Optional[PaginatedEntityList[InferenceSimulator]]:
        request = InferenceSimulatorListRequest(
            projectPublicId=project_public_id,
            projectSlug=project_slug,
            statuses=statuses,
            entityFilterRequest=EntityFilterRequest(
                orderByField="createdAt",
                orderByDirection=OrderDirectionType.DESC,
                page=page,
                limit=limit,
            ),
        )

        response = self._request(
            method='POST',
            url='/user-api/v2/inference-simulator/list',
            data=request.model_dump(),
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )
        result = InferenceSimulatorListResponse.model_validate(response) if response else None
        return result.inferenceSimulators if result and result.is_success else None

    def start_project_inference_simulator(
            self,
            project_public_id: str,
            commit_hash: Optional[str] = None,
            rented_instance_public_id: Optional[str] = None,
            rented_instance_slug: Optional[str] = None,
            self_hosted_instance_public_id: Optional[str] = None,
            self_hosted_instance_slug: Optional[str] = None,
            inference_dir: Optional[str] = None,
            is_skip_installation: Optional[bool] = False,
    ) -> Optional[StartInferenceSimulatorResponse]:
        request = StartInferenceSimulatorRequest(
            projectPublicId=project_public_id,
            commitHash=commit_hash,
            instanceRentedPublicId=rented_instance_public_id,
            instanceRentedSlug=rented_instance_slug,
            selfhostedInstancePublicId=self_hosted_instance_public_id,
            selfhostedInstanceSlug=self_hosted_instance_slug,
            inferenceDir=inference_dir,
            isSkipInstallation=is_skip_installation,
        )

        response = self._request(
            method='POST',
            url='/user-api/v2/project/inference-simulator/create',
            data=request.model_dump(),
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        return StartInferenceSimulatorResponse.model_validate(response) if response else None

    def get_inference_simulator_business_status_map(self) -> Optional[Dict[str, str]]:
        response = self._request(
            method='POST',
            url='/user-api/v1/inference-simulator/status-localized-mapping',
            data=None,
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        data = InferenceSimulatorStatusMapperResponse.model_validate(response) if response else None

        return data.inference_simulator_status_map if data else None

    @error_handler()
    def get_inference_simulator(
            self,
            public_id: Optional[str] = None,
            slug: Optional[str] = None,
    ) -> Optional[GetInferenceSimulatorResponse]:
        request = GetInferenceSimulatorRequest(
            publicId=public_id,
            slug=slug,
        )

        response = self._request(
            method='POST',
            url='/user-api/v2/inference-simulator/get',
            data=request.model_dump(),
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )
        return GetInferenceSimulatorResponse.model_validate(response) if response else None