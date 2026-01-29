from typing import Optional

from pydantic import Field, ConfigDict, BaseModel

from thestage.inference_simulator.dto.inference_simulator import InferenceSimulator


class GetInferenceSimulatorResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    inferenceSimulator: Optional[InferenceSimulator] = Field(None, alias='inferenceSimulator')


