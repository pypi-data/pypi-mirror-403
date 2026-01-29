from typing import Optional

from pydantic import Field

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse
from thestage.task.dto.task import Task


class TaskViewResponse(TheStageBaseResponse):
    task: Optional[Task] = Field(None, alias='task')
