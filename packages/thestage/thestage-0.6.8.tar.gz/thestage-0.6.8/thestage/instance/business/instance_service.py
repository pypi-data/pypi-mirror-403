from pathlib import Path
from typing import List, Optional

import typer

from thestage.instance.communication.instance_api_client import InstanceApiClient
from thestage.instance.dto.rented_instance import RentedInstanceEntity
from thestage.instance.dto.self_hosted_instance import SelfHostedInstanceEntity
from thestage.i18n.translation import __
from thestage.instance.dto.enum.selfhosted_status import SelfhostedBusinessStatus
from thestage.instance.dto.enum.instance_rented_status import InstanceRentedBusinessStatus
from thestage.services.abstract_service import AbstractService
from thestage.helpers.error_handler import error_handler
from thestage.instance.dto.instance_rented_response import InstanceRentedDto
from thestage.services.clients.thestage_api.dtos.paginated_entity_list import PaginatedEntityList
from thestage.instance.dto.selfhosted_instance_response import SelfHostedInstanceDto
from thestage.config.business.config_provider import ConfigProvider
from thestage.instance.business.mapper.rented_instance_mapper import RentedInstanceMapper
from thestage.instance.business.mapper.selfhosted_instance_mapper import SelfHostedInstanceMapper
from thestage.connect.business.remote_server_service import RemoteServerService


class InstanceService(AbstractService):
    __instance_api_client: InstanceApiClient = None
    __config_provider: ConfigProvider = None

    def __init__(
            self,
            instance_api_client: InstanceApiClient,
            config_provider: ConfigProvider,
            remote_server_service: RemoteServerService,
    ):
        self.__instance_api_client = instance_api_client
        self.__remote_server_service = remote_server_service
        self.__config_provider = config_provider


    @error_handler()
    def check_instance_status_to_connect(
            self,
            instance: InstanceRentedDto,
    ) -> InstanceRentedDto:
        if instance:
            if instance.frontend_status.status_key in [
                InstanceRentedBusinessStatus.IN_QUEUE.name,
                InstanceRentedBusinessStatus.CREATING.name,
                InstanceRentedBusinessStatus.REBOOTING.name,
                InstanceRentedBusinessStatus.STARTING.name,
            ]:
                typer.echo(__('Cannot connect to rented server instance: it is either in the process of being rented or rebooted'))
                raise typer.Exit(1)
            elif instance.frontend_status.status_key in [
                InstanceRentedBusinessStatus.TERMINATING.name,
                InstanceRentedBusinessStatus.RENTAL_ERROR.name,
            ]:
                typer.echo(__('Cannot connect to rented server instance: renting failed'))
                raise typer.Exit(1)
            elif instance.frontend_status.status_key in [
                InstanceRentedBusinessStatus.STOPPED.name,
                InstanceRentedBusinessStatus.STOPPING.name,
                InstanceRentedBusinessStatus.DELETED.name,
            ]:
                typer.echo(__('Cannot connect to rented server instance: it is either stopped or has been deleted'))
                raise typer.Exit(1)
            elif instance.frontend_status.status_key in [
                InstanceRentedBusinessStatus.UNKNOWN.name,
                InstanceRentedBusinessStatus.ALL.name,
            ]:
                typer.echo(__('Cannot connect to rented server instance: instance status unknown'))
                raise typer.Exit(1)

        return instance

    @error_handler()
    def check_selfhosted_status_to_connect(
            self,
            instance: SelfHostedInstanceDto,
    ) -> SelfHostedInstanceDto:
        if instance:
            if instance.frontend_status.status_key in [
                SelfhostedBusinessStatus.AWAITING_CONFIGURATION.name,
            ]:
                typer.echo(__('Cannot connect to self-hosted instance: it is awaiting configuration'))
                raise typer.Exit(1)
            elif instance.frontend_status.status_key in [
                SelfhostedBusinessStatus.UNREACHABLE_DAEMON.name,
                SelfhostedBusinessStatus.DELETED.name,
            ]:
                typer.echo(__('Cannot connect to self-hosted instance: it may be turned off or unreachable'))
                raise typer.Exit(1)
            elif instance.frontend_status.status_key in [
                SelfhostedBusinessStatus.UNKNOWN.name,
                SelfhostedBusinessStatus.ALL.name,
            ]:
                typer.echo(__('Cannot connect to self-hosted instance: instance status unknown'))
                raise typer.Exit(1)

        return instance

    @error_handler()
    def connect_to_rented_instance(
            self,
            instance_rented_public_id: Optional[str],
            instance_rented_slug: Optional[str],
            input_ssh_key_path: Optional[str]
    ):
        instance = self.__instance_api_client.get_rented_instance(
            instance_public_id=instance_rented_public_id,
            instance_slug=instance_rented_slug,
        )

        if instance:
            self.check_instance_status_to_connect(
                instance=instance,
            )

            ssh_path_from_config: Optional[str] = None
            if not input_ssh_key_path:
                ssh_path_from_config = self.__config_provider.get_valid_private_key_path_by_ip_address(instance.ip_address)
                if ssh_path_from_config:
                    typer.echo(f"Using configured SSH key for this instance: {ssh_path_from_config}")

            if not input_ssh_key_path and not ssh_path_from_config:
                typer.echo('Using SSH agent to connect to server instance')

            self.__remote_server_service.connect_to_instance(
                ip_address=instance.ip_address,
                username=instance.host_username,
                private_key_path=ssh_path_from_config or input_ssh_key_path
            )

            # cannot really detect how ssh connection was ended. capturing stderr using subprocess feels bad/unreliable.
            if input_ssh_key_path:
                self.__config_provider.update_remote_server_config_entry(ip_address=instance.ip_address, ssh_key_path=Path(input_ssh_key_path))
        else:
            typer.echo(__("Server instance not found: %instance_item%", {'instance_item': instance_rented_slug}))


    @error_handler()
    def connect_to_selfhosted_instance(
            self,
            selfhosted_instance_public_id: Optional[str],
            selfhosted_instance_slug: Optional[str],
            username: str,
            input_ssh_key_path: Optional[str],
    ):
        if not username:
            username = 'root'
            typer.echo(__("No remote server username provided, using 'root' as username"))

        instance = self.__instance_api_client.get_selfhosted_instance(
            instance_public_id=selfhosted_instance_public_id,
            instance_slug=selfhosted_instance_slug,
        )

        if instance:
            self.check_selfhosted_status_to_connect(
                instance=instance,
            )

            ssh_path_from_config: Optional[str] = None
            if not input_ssh_key_path:
                ssh_path_from_config = self.__config_provider.get_valid_private_key_path_by_ip_address(instance.ip_address)
                if ssh_path_from_config:
                    typer.echo(f"Using configured SSH key for this instance: {ssh_path_from_config}")

            if not input_ssh_key_path and not ssh_path_from_config:
                typer.echo('Using SSH agent to connect to server instance')

            self.__remote_server_service.connect_to_instance(
                ip_address=instance.ip_address,
                username=username,
                private_key_path=ssh_path_from_config or input_ssh_key_path
            )

            if input_ssh_key_path:
                self.__config_provider.update_remote_server_config_entry(ip_address=instance.ip_address, ssh_key_path=Path(input_ssh_key_path))
        else:
            typer.echo("Self-hosted instance not found")


    @error_handler()
    def get_rented_list(
            self,
            statuses: List[str],
            row: int = 5,
            page: int = 1,
    ) -> PaginatedEntityList[InstanceRentedDto]:
        data = self.__instance_api_client.get_rented_instance_list(
            statuses=statuses,
            page=page,
            limit=row,
        )

        return data

    @error_handler()
    def get_self_hosted_list(
            self,
            statuses: List[str],
            row: int = 5,
            page: int = 1,
    ) -> PaginatedEntityList[SelfHostedInstanceDto]:
        data = self.__instance_api_client.get_selfhosted_instance_list(
            statuses=statuses,
            page=page,
            limit=row,
        )
        return data


    @error_handler()
    def print_self_hosted_instance_list(self, statuses, row, page):
        selfhosted_instance_status_map = self.__instance_api_client.get_selfhosted_business_status_map()

        if not statuses:
            statuses = ({key: selfhosted_instance_status_map[key] for key in [
                SelfhostedBusinessStatus.AWAITING_CONFIGURATION,
                SelfhostedBusinessStatus.RUNNING,
                SelfhostedBusinessStatus.UNREACHABLE_DAEMON,
            ]}).values()

        if "all" in statuses:
            statuses = selfhosted_instance_status_map.values()

        for input_status_item in statuses:
            if input_status_item not in selfhosted_instance_status_map.values():
                typer.echo(__("'%invalid_status%' is not one of %valid_statuses%", {
                    'invalid_status': input_status_item,
                    'valid_statuses': str(list(selfhosted_instance_status_map.values()))
                }))
                raise typer.Exit(1)

        typer.echo(__(
            "Listing self-hosted instances with the following statuses: %statuses%, to view all self-hosted instances, use --status all",
            placeholders={
                'statuses': ', '.join([status_item for status_item in statuses])
            }))

        backend_statuses: List[str] = [key for key, value in selfhosted_instance_status_map.items() if value in statuses]

        self.print(
            func_get_data=self.get_self_hosted_list,
            func_special_params={
                'statuses': backend_statuses,
            },
            mapper=SelfHostedInstanceMapper(),
            headers=list(map(lambda x: x.alias, SelfHostedInstanceEntity.model_fields.values())),
            row=row,
            page=page,
            show_index="never",
        )


    @error_handler()
    def print_rented_instance_list(self, statuses, row, page):
        instance_rented_status_map = self.__instance_api_client.get_rented_business_status_map()

        if not statuses:
            statuses = ({key: instance_rented_status_map[key] for key in [
                InstanceRentedBusinessStatus.ONLINE,
                InstanceRentedBusinessStatus.CREATING,
                InstanceRentedBusinessStatus.TERMINATING,
                InstanceRentedBusinessStatus.REBOOTING,
            ]}).values()

        if "all" in statuses:
            statuses = instance_rented_status_map.values()

        for input_status_item in statuses:
            if input_status_item not in instance_rented_status_map.values():
                typer.echo(__("'%invalid_status%' is not one of %valid_statuses%", {
                    'invalid_status': input_status_item,
                    'valid_statuses': str(list(instance_rented_status_map.values()))
                }))
                raise typer.Exit(1)

        typer.echo(__(
            "Listing rented server instances with the following statuses: %statuses%, to view all rented server instances, use --status all",
            placeholders={
                'statuses': ', '.join([status_item for status_item in statuses])
            }))

        backend_statuses: List[str] = [key for key, value in instance_rented_status_map.items() if value in statuses]

        self.print(
            func_get_data=self.get_rented_list,
            func_special_params={
                'statuses': backend_statuses,
            },
            mapper=RentedInstanceMapper(),
            headers=list(map(lambda x: x.alias, RentedInstanceEntity.model_fields.values())),
            row=row,
            page=page,
            show_index="never",
        )