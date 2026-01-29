from typing import Optional

from thestage.task.dto.task_entity import TaskEntity
from thestage.services.abstract_mapper import AbstractMapper
from thestage.task.dto.task import Task


class TaskMapper(AbstractMapper):

    def build_entity(self, item: Task) -> Optional[TaskEntity]:
        if not item:
            return None

        return TaskEntity(
            public_id=item.public_id or '',
            title=item.title or '',
            status=item.frontend_status.status_translation or '',
            docker_container_public_id=item.docker_container_public_id,
            started_at=item.started_at or '',
            finished_at=item.finished_at or '',
        )
