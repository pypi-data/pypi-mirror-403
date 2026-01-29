from pydantic import Field, ConfigDict

from thestage.services.clients.thestage_api.dtos.base_response import TheStageBaseResponse
from thestage.docker_container.dto.container_response import DockerContainerDto
from thestage.services.clients.thestage_api.dtos.paginated_entity_list import PaginatedEntityList


class DockerContainerListResponse(TheStageBaseResponse):
    model_config = ConfigDict(use_enum_values=True)

    paginatedList: PaginatedEntityList[DockerContainerDto] = Field(None, alias='paginatedList')
