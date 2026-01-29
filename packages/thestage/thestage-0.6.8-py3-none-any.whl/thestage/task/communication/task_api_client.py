from typing import Optional, List, Dict

from thestage.config.business.config_provider import ConfigProvider
from thestage.global_dto.enums.order_direction_type import OrderDirectionType
from thestage.services.clients.thestage_api.core.api_client_core import TheStageApiClientCore
from thestage.services.clients.thestage_api.dtos.entity_filter_request import EntityFilterRequest
from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse
from thestage.services.clients.thestage_api.dtos.paginated_entity_list import PaginatedEntityList
from thestage.task.dto.list_for_project_request import TaskListForProjectRequest
from thestage.task.dto.list_for_project_response import TaskListForProjectResponse
from thestage.task.dto.run_task_request import RunTaskRequest
from thestage.task.dto.run_task_response import RunTaskResponse
from thestage.task.dto.status_localized_map_response import TaskStatusLocalizedMapResponse
from thestage.task.dto.view_response import TaskViewResponse
from thestage.task.dto.task import Task


class TaskApiClient(TheStageApiClientCore):
    def __init__(self, config_provider: ConfigProvider):
        super().__init__(url=config_provider.get_config().main.thestage_api_url)
        self.__config_provider = config_provider

    def get_task(
            self,
            task_public_id: str,
    ) -> Optional[TaskViewResponse]:
        data = {
            "taskPublicId": task_public_id,
        }

        response = self._request(
            method='POST',
            url='/user-api/v2/task/view',
            data=data,
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        result = TaskViewResponse.model_validate(response) if response else None
        return result if result and result.is_success else None

    def get_task_list_for_project(
            self,
            project_public_id: Optional[str],
            project_slug: Optional[str],
            page: int = 1,
            limit: int = 10,
    ) -> Optional[PaginatedEntityList[Task]]:
        request = TaskListForProjectRequest(
            projectPublicId=project_public_id,
            projectSlug=project_slug,
            entityFilterRequest=EntityFilterRequest(
                orderByField="createdAt",
                orderByDirection=OrderDirectionType.DESC,
                page=page,
                limit=limit,
            ),
        )

        response = self._request(
            method='POST',
            url='/user-api/v2/task/list',
            data=request.model_dump(),
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        result = TaskListForProjectResponse.model_validate(response) if response else None
        return result.tasks if result and result.is_success else None

    def get_task_localized_status_map(self) -> Optional[Dict[str, str]]:
        response = self._request(
            method='POST',
            url='/user-api/v1/task/status-localized-mapping',
            data=None,
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        data = TaskStatusLocalizedMapResponse.model_validate(response) if response else None

        return data.taskStatusMap if data else None

    def cancel_task(
            self,
            task_public_id: str,
    ) -> Optional[TheStageBaseResponse]:
        data = {
            "taskPublicId": task_public_id,
        }

        response = self._request(
            method='POST',
            url='/user-api/v2/task/cancel',
            data=data,
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        result = TheStageBaseResponse.model_validate(response) if response else None
        return result if result else None

    def execute_project_task(
            self,
            project_public_id: str,
            run_command: str,
            task_title: str,
            docker_container_public_id: str,
            commit_hash: Optional[str] = None,
    ) -> Optional[RunTaskResponse]:
        request = RunTaskRequest(
            projectPublicId=project_public_id,
            dockerContainerPublicId=docker_container_public_id,
            commitHash=commit_hash,
            runCommand=run_command,
            taskTitle=task_title,
        )

        response = self._request(
            method='POST',
            url='/user-api/v2/task/execute',
            data=request.model_dump(),
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        return RunTaskResponse.model_validate(response) if response else None
