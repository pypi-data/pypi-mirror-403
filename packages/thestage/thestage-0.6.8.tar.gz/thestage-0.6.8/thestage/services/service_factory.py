from typing import Optional

from thestage.config.business.app_config_service import AppConfigService
from thestage.config.business.config_provider import ConfigProvider
from thestage.config.business.validation_service import ValidationService
from thestage.connect.business.connect_service import ConnectService
from thestage.connect.business.remote_server_service import RemoteServerService
from thestage.connect.communication.connect_api_client import ConnectApiClient
from thestage.docker_container.business.container_service import ContainerService
from thestage.docker_container.communication.docker_container_api_client import DockerContainerApiClient
from thestage.git.communication.git_client import GitLocalClient
from thestage.inference_model.business.inference_model_service import InferenceModelService
from thestage.inference_model.communication.inference_model_api_client import InferenceModelApiClient
from thestage.inference_simulator.business.inference_simulator_service import InferenceSimulatorService
from thestage.inference_simulator.communication.inference_simulator_api_client import InferenceSimulatorApiClient
from thestage.instance.business.instance_service import InstanceService
from thestage.instance.communication.instance_api_client import InstanceApiClient
from thestage.logging.business.logging_service import LoggingService
from thestage.logging.communication.logging_api_client import LoggingApiClient
from thestage.project.business.project_service import ProjectService
from thestage.project.communication.project_api_client import ProjectApiClient
from thestage.services.clients.thestage_api.core.api_client_core import TheStageApiClientCore
from thestage.services.filesystem_service import FileSystemService
from thestage.task.business.task_service import TaskService
from thestage.task.communication.task_api_client import TaskApiClient


class ServiceFactory:
    __git_local_client: Optional[GitLocalClient] = None
    __file_system_service: Optional[FileSystemService] = None
    __config_provider: Optional[ConfigProvider] = None
    __task_api_client: Optional[TaskApiClient] = None
    __project_api_client: Optional[ProjectApiClient] = None
    __inference_model_api_client: Optional[InferenceModelApiClient] = None
    __inference_simulator_api_client: Optional[InferenceSimulatorApiClient] = None
    __instance_api_client: Optional[InstanceApiClient] = None
    __docker_container_api_client: Optional[DockerContainerApiClient] = None
    __connect_api_client: Optional[ConnectApiClient] = None
    __logging_api_client: Optional[LoggingApiClient] = None

    def get_validation_service(self) -> ValidationService:
        config_provider = self.get_config_provider()
        core_client = TheStageApiClientCore(url=config_provider.get_config().main.thestage_api_url)
        return ValidationService(
            core_client=core_client,
            config_provider=config_provider,
        )

    def get_instance_service(self) -> InstanceService:
        return InstanceService(
            instance_api_client=self.get_instance_api_client(),
            remote_server_service=self.get_remote_server_service(),
            config_provider=self.get_config_provider(),
        )

    def get_container_service(self) -> ContainerService:
        return ContainerService(
            docker_container_api_client=self.get_docker_container_api_client(),
            remote_server_service=self.get_remote_server_service(),
            file_system_service=self.get_file_system_service(),
            config_provider=self.get_config_provider(),
            connect_api_client=self.get_connect_api_client(),
        )

    def get_connect_service(self) -> ConnectService:
        return ConnectService(
            instance_api_client=self.get_instance_api_client(),
            connect_api_client=self.get_connect_api_client(),
            instance_service=self.get_instance_service(),
            container_service=self.get_container_service(),
            logging_service=self.get_logging_service(),
        )

    def get_project_service(self) -> ProjectService:
        return ProjectService(
            task_api_client=self.get_task_api_client(),
            docker_container_api_client=self.get_docker_container_api_client(),
            project_api_client=self.get_project_api_client(),
            remote_server_service=self.get_remote_server_service(),
            file_system_service=self.get_file_system_service(),
            git_local_client=self.get_git_local_client(),
            config_provider=self.get_config_provider(),
        )

    def get_task_service(self) -> TaskService:
        return TaskService(
            docker_container_api_client=self.get_docker_container_api_client(),
            project_service=self.get_project_service(),
            task_api_client=self.get_task_api_client(),
            config_provider=self.get_config_provider(),
            git_local_client=self.get_git_local_client(),
            file_system_service=self.get_file_system_service(),
        )

    def get_inference_simulator_service(self) -> InferenceSimulatorService:
        return InferenceSimulatorService(
            inference_simulator_api_client=self.get_inference_simulator_api_client(),
            inference_model_api_client=self.get_inference_model_api_client(),
            config_provider=self.get_config_provider(),
            git_local_client=self.get_git_local_client(),
            project_service=self.get_project_service(),
        )

    def get_inference_model_service(self) -> InferenceModelService:
        return InferenceModelService(
            inference_model_api_client=self.get_inference_model_api_client(),
            config_provider=self.get_config_provider(),
            project_service=self.get_project_service(),
        )

    def get_remote_server_service(self) -> RemoteServerService:
        return RemoteServerService(
            file_system_service=self.get_file_system_service(),
            config_provider=self.get_config_provider(),
        )

    def get_app_config_service(self) -> AppConfigService:
        return AppConfigService(
            config_provider=self.get_config_provider(),
            validation_service=self.get_validation_service(),
        )

    def get_logging_service(self) -> LoggingService:
        return LoggingService(
            logging_api_client=self.get_logging_api_client(),
            docker_container_api_client=self.get_docker_container_api_client(),
            task_api_client=self.get_task_api_client(),
            inference_simulator_api_client=self.get_inference_simulator_api_client(),
        )

    def get_task_api_client(self) -> TaskApiClient:
        if not self.__task_api_client:
            self.__task_api_client = TaskApiClient(config_provider=self.get_config_provider())
        return self.__task_api_client

    def get_project_api_client(self) -> ProjectApiClient:
        if not self.__project_api_client:
            self.__project_api_client = ProjectApiClient(config_provider=self.get_config_provider())
        return self.__project_api_client

    def get_inference_model_api_client(self) -> InferenceModelApiClient:
        if not self.__inference_model_api_client:
            self.__inference_model_api_client = InferenceModelApiClient(config_provider=self.get_config_provider())
        return self.__inference_model_api_client

    def get_inference_simulator_api_client(self) -> InferenceSimulatorApiClient:
        if not self.__inference_simulator_api_client:
            self.__inference_simulator_api_client = InferenceSimulatorApiClient(config_provider=self.get_config_provider())
        return self.__inference_simulator_api_client

    def get_instance_api_client(self) -> InstanceApiClient:
        if not self.__instance_api_client:
            self.__instance_api_client = InstanceApiClient(config_provider=self.get_config_provider())
        return self.__instance_api_client

    def get_docker_container_api_client(self) -> DockerContainerApiClient:
        if not self.__docker_container_api_client:
            self.__docker_container_api_client = DockerContainerApiClient(config_provider=self.get_config_provider())
        return self.__docker_container_api_client

    def get_connect_api_client(self) -> ConnectApiClient:
        if not self.__connect_api_client:
            self.__connect_api_client = ConnectApiClient(config_provider=self.get_config_provider())
        return self.__connect_api_client

    def get_logging_api_client(self) -> LoggingApiClient:
        if not self.__logging_api_client:
            self.__logging_api_client = LoggingApiClient(config_provider=self.get_config_provider())
        return self.__logging_api_client

    def get_git_local_client(self):
        if not self.__git_local_client:
            self.__git_local_client = GitLocalClient(file_system_service=self.get_file_system_service())
        return self.__git_local_client

    def get_file_system_service(self) -> FileSystemService:
        if not self.__file_system_service:
            self.__file_system_service = FileSystemService()
        return self.__file_system_service

    def get_config_provider(self) -> ConfigProvider:
        if not self.__config_provider:
            self.__config_provider = ConfigProvider(self.get_file_system_service())
        return self.__config_provider