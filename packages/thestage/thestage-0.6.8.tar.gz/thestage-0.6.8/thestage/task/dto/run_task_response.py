from typing import Optional, List

from pydantic import Field, ConfigDict

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse
from thestage.task.dto.task import Task


class RunTaskResponse(TheStageBaseResponse):
    model_config = ConfigDict(use_enum_values=True)

    task: Task = Field(None, alias='task')
    tasksInQueue: Optional[List[Task]] = Field(None, alias='tasksInQueue')
