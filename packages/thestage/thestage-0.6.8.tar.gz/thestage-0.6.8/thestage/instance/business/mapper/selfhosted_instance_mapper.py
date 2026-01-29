from typing import Optional

from thestage.instance.dto.self_hosted_instance import SelfHostedInstanceEntity
from thestage.instance.dto.enum.gpu_name import InstanceGpuType
from thestage.instance.dto.selfhosted_instance_response import SelfHostedInstanceDto
from thestage.services.abstract_mapper import AbstractMapper


class SelfHostedInstanceMapper(AbstractMapper):

    def build_entity(self, item: SelfHostedInstanceDto) -> Optional[SelfHostedInstanceEntity]:
        if not item:
            return None

        gpus = []
        if item.detected_gpus:
            gpus = [item.type.value for item in item.detected_gpus.gpus]

        if len(gpus) == 0:
            gpus = [InstanceGpuType.NO_GPU]

        return SelfHostedInstanceEntity(
            slug=item.slug,
            public_id=item.public_id,
            cpu_type=item.cpu_type,
            cpu_cores=item.cpu_cores,
            gpu_type=', '.join(gpus),
            ip_address=item.ip_address,
            status=item.frontend_status.status_translation if item.frontend_status else None,
        )
