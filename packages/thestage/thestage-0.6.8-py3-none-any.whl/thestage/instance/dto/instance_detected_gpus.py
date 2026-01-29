from typing import Optional, List

from pydantic import Field, BaseModel, ConfigDict

from thestage.instance.dto.enum.gpu_name import InstanceGpuType


class InstanceDaemonGpuDto(BaseModel):

    gpu_id: Optional[int] = Field(None, alias='gpuId')
    name: Optional[str] = Field(None, alias='name')
    uuid: Optional[str] = Field(None, alias='uuid')
    type: Optional[InstanceGpuType] = Field(InstanceGpuType.UNKNOWN, alias='type')


class InstanceDetectedGpusDto(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    gpus: List[InstanceDaemonGpuDto] = Field(default_factory=list, alias='gpus')
