
from pydantic import Field, ConfigDict

from thestage.inference_model.dto.inference_model import InferenceModel
from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse
from thestage.services.clients.thestage_api.dtos.paginated_entity_list import PaginatedEntityList


class InferenceSimulatorModelListForProjectResponse(TheStageBaseResponse):
    model_config = ConfigDict(use_enum_values=True)

    inferenceSimulatorModels: PaginatedEntityList[InferenceModel] = Field(None, alias='inferenceSimulatorModels')
