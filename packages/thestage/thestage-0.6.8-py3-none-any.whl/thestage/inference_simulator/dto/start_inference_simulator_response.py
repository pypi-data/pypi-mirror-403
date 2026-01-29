from pydantic import Field, ConfigDict

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse
from thestage.inference_simulator.dto.inference_simulator import InferenceSimulator


class StartInferenceSimulatorResponse(TheStageBaseResponse):
    model_config = ConfigDict(use_enum_values=True)

    inferenceSimulator: InferenceSimulator = Field(None, alias='inferenceSimulator')
