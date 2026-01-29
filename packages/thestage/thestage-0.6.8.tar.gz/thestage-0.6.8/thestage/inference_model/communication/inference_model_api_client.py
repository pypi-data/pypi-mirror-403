from typing import Optional, List, Dict

from thestage.config.business.config_provider import ConfigProvider
from thestage.global_dto.enums.order_direction_type import OrderDirectionType
from thestage.helpers.error_handler import error_handler
from thestage.services.clients.thestage_api.core.api_client_core import TheStageApiClientCore
from thestage.services.clients.thestage_api.dtos.entity_filter_request import EntityFilterRequest
from thestage.services.clients.thestage_api.dtos.paginated_entity_list import PaginatedEntityList

from thestage.inference_model.dto.inference_model import InferenceModel
from thestage.inference_model.dto.inference_simulator_model_list_for_project_request import InferenceSimulatorModelListForProjectRequest
from thestage.inference_model.dto.inference_simulator_model_list_for_project_response import InferenceSimulatorModelListForProjectResponse
from thestage.inference_model.dto.push_inference_simulator_model_request import PushInferenceSimulatorModelRequest
from thestage.inference_model.dto.push_inference_simulator_model_response import PushInferenceSimulatorModelResponse
from thestage.inference_model.dto.inference_simulator_model_response import InferenceSimulatorModelStatusMapperResponse
from thestage.inference_model.dto.deploy_inference_model_to_instance_request import DeployInferenceModelToInstanceRequest
from thestage.inference_model.dto.deploy_inference_model_to_instance_response import DeployInferenceModelToInstanceResponse
from thestage.inference_model.dto.deploy_inference_model_to_sagemaker_request import DeployInferenceModelToSagemakerRequest
from thestage.inference_model.dto.deploy_inference_model_to_sagemaker_response import DeployInferenceModelToSagemakerResponse


class InferenceModelApiClient(TheStageApiClientCore):
    def __init__(self, config_provider: ConfigProvider):
        super().__init__(url=config_provider.get_config().main.thestage_api_url)
        self.__config_provider = config_provider

    def get_inference_simulator_model_list_for_project(
            self,
            project_public_id: Optional[str],
            project_slug: Optional[str],
            statuses: Optional[List[str]] = None,
            page: int = 1,
            limit: int = 10,
    ) -> Optional[PaginatedEntityList[InferenceModel]]:
        request = InferenceSimulatorModelListForProjectRequest(
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
            url='/user-api/v2/inference-simulator-model/list',
            data=request.model_dump(),
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )
        result = InferenceSimulatorModelListForProjectResponse.model_validate(response) if response else None
        return result.inferenceSimulatorModels if result and result.is_success else None


    def push_project_inference_simulator_model(
            self,
            public_id: Optional[str],
            slug: Optional[str],
    ) -> Optional[PushInferenceSimulatorModelResponse]:
        request = PushInferenceSimulatorModelRequest(
            inferenceSimulatorPublicId=public_id,
            inferenceSimulatorSlug=slug,
        )

        response = self._request(
            method='POST',
            url='/user-api/v2/inference-simulator/push-model',
            data=request.model_dump(),
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        return PushInferenceSimulatorModelResponse.model_validate(response) if response else None


    def get_inference_simulator_model_business_status_map(self) -> Optional[Dict[str, str]]:
        response = self._request(
            method='POST',
            url='/user-api/v1/inference-simulator-model/status-localized-mapping',
            data=None,
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        data = InferenceSimulatorModelStatusMapperResponse.model_validate(response) if response else None

        return data.inference_simulator_model_status_map if data else None


    @error_handler()
    def deploy_inference_model_to_instance(
            self,
            model_public_id: str,
            model_slug: str,
            new_inference_simulator_slug: str,
            rented_instance_public_id: Optional[str] = None,
            rented_instance_slug: Optional[str] = None,
            self_hosted_instance_public_id: Optional[str] = None,
            self_hosted_instance_slug: Optional[str] = None,

    ) -> Optional[DeployInferenceModelToInstanceResponse]:
        request = DeployInferenceModelToInstanceRequest(
            modelPublicId=model_public_id,
            modelSlug=model_slug,
            instanceRentedPublicId=rented_instance_public_id,
            instanceRentedSlug=rented_instance_slug,
            selfhostedInstancePublicId=self_hosted_instance_public_id,
            selfhostedInstanceSlug=self_hosted_instance_slug
        )

        response = self._request(
            method='POST',
            url='/user-api/v2/inference-simulator-model/deploy/instance',
            data=request.model_dump(),
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )
        return DeployInferenceModelToInstanceResponse.model_validate(response) if response else None


    @error_handler()
    def deploy_inference_model_to_sagemaker(
            self,
            model_public_id: Optional[str],
            model_slug: Optional[str],
            arn: Optional[str] = None,
    ) -> Optional[DeployInferenceModelToSagemakerResponse]:
        request = DeployInferenceModelToSagemakerRequest(
            modelPublicId=model_public_id,
            modelSlug=model_slug,
            arn=arn,
        )

        response = self._request(
            method='POST',
            url='/user-api/v1/inference-simulator-model/grant-user-arn-access',
            data=request.model_dump(),
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )
        return DeployInferenceModelToSagemakerResponse.model_validate(response) if response else None