from typing import Optional

from pydantic import Field, ConfigDict

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse


class AddSshKeyToUserResponse(TheStageBaseResponse):
    model_config = ConfigDict(use_enum_values=True)

    sshKeyPairPublicId: Optional[str] = Field(None, alias='sshKeyPairPublicId')