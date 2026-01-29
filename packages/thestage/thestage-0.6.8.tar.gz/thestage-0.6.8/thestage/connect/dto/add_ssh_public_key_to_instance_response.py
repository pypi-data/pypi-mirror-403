from pydantic import ConfigDict

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse


class AddSshPublicKeyToInstanceResponse(TheStageBaseResponse):
    model_config = ConfigDict(use_enum_values=True)

