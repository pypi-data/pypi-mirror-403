from typing import Optional

from pydantic import Field, ConfigDict

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse


class DeployInferenceModelToInstanceResponse(TheStageBaseResponse):
    model_config = ConfigDict(use_enum_values=True)

    inferenceSimulatorPublicId: Optional[str] = Field(None, alias='inferenceSimulatorPublicId')


