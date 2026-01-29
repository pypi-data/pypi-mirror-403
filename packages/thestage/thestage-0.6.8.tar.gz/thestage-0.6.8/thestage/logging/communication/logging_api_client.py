from typing import Optional

import httpx

from thestage.config.business.config_provider import ConfigProvider
from thestage.services.clients.thestage_api.core.api_client_core import TheStageApiClientCore
from thestage.logging.dto.log_polling_request import LogPollingRequest
from thestage.logging.dto.log_polling_response import LogPollingResponse
from thestage.logging.dto.user_logs_query_request import UserLogsQueryRequest
from thestage.logging.dto.user_logs_query_response import UserLogsQueryResponse


class LoggingApiClient(TheStageApiClientCore):
    def __init__(self, config_provider: ConfigProvider):
        super().__init__(url=config_provider.get_config().main.thestage_api_url)
        self.__config_provider = config_provider

    async def poll_logs_httpx(self, docker_container_public_id: Optional[str], last_log_timestamp: str,
                              last_log_id: str, task_public_id: Optional[str] = None,
                              inference_simulator_public_id: Optional[str] = None) -> Optional[LogPollingResponse]:
        request_headers = {'Content-Type': 'application/json'}
        token = self.__config_provider.get_config().main.thestage_auth_token
        if token: request_headers['Authorization'] = f"Bearer {token}"

        request = LogPollingRequest(
            inferenceSimulatorPublicId=inference_simulator_public_id,
            taskPublicId=task_public_id,
            dockerContainerPublicId=docker_container_public_id,
            lastLogTimestamp=last_log_timestamp,
            lastLogId=last_log_id
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=f"{self._get_host()}/user-api/v2/logging/poll",
                headers=request_headers,
                json=request.model_dump(),
                timeout=3.5
            )

            return LogPollingResponse.model_validate(response.json()) if response else None


    def query_user_logs(self, limit: int, task_public_id: Optional[str] = None,
                        inference_simulator_public_id: Optional[str] = None,
                        container_public_id: Optional[str] = None) -> UserLogsQueryResponse:
        request = UserLogsQueryRequest(
            inferenceSimulatorPublicId=inference_simulator_public_id,
            taskPublicId=task_public_id,
            containerPublicId=container_public_id,
            limit=limit,
            ascendingOrder=False,
        )

        response = self._request(
            method='POST',
            url='/user-api/v2/logging/query-user-logs',
            data=request.model_dump(),
            token=self.__config_provider.get_config().main.thestage_auth_token,
        )

        result = UserLogsQueryResponse.model_validate(response) if response else None
        return result