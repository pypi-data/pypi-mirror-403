from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from thestage.services.clients.thestage_api.dtos.frontend_status import FrontendStatusDto


class Task(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    public_id: Optional[str] = Field(None, alias='publicId')
    docker_container_public_id: Optional[str] = Field(None, alias='dockerContainerPublicId')
    title: Optional[str] = Field(None, alias='title')
    frontend_status: FrontendStatusDto = Field(None, alias='frontendStatus')
    commit_hash: Optional[str] = Field(None, alias='commitHash')
    started_at: Optional[str] = Field(None, alias='startedAt')
    finished_at: Optional[str] = Field(None, alias='finishedAt')
