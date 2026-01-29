from typing import Optional

from pydantic import Field, BaseModel, ConfigDict

from thestage.docker_container.dto.enum.container_pending_action import DockerContainerAction

class DockerContainerActionRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    dockerContainerPublicId: Optional[str] = Field(None, alias='dockerContainerPublicId')
    action: DockerContainerAction = Field(None, alias='action')
