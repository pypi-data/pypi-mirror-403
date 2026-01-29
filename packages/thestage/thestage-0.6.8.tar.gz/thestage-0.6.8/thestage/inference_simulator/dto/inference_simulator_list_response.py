
from pydantic import Field, ConfigDict

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse
from thestage.services.clients.thestage_api.dtos.paginated_entity_list import PaginatedEntityList
from thestage.inference_simulator.dto.inference_simulator import InferenceSimulator


class InferenceSimulatorListResponse(TheStageBaseResponse):
    model_config = ConfigDict(use_enum_values=True)

    inferenceSimulators: PaginatedEntityList[InferenceSimulator] = Field(None, alias='inferenceSimulators')
