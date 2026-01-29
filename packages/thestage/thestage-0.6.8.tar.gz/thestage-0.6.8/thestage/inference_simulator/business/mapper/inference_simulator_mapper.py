from typing import Optional

from thestage.inference_simulator.dto.inference_simulator_entity import InferenceSimulatorEntity
from thestage.services.abstract_mapper import AbstractMapper
from thestage.inference_simulator.dto.inference_simulator import InferenceSimulator


class InferenceSimulatorMapper(AbstractMapper):

    def build_entity(self, item: InferenceSimulator) -> Optional[InferenceSimulatorEntity]:
        if not item:
            return None

        return InferenceSimulatorEntity(
            public_id=item.public_id or '',
            slug=item.slug or '',
            status=item.status or '',
            http_endpoint=item.http_endpoint or '',
            grpc_endpoint=item.grpc_endpoint or '',
            metrics_endpoint=item.metrics_endpoint or '',
            started_at=item.created_at or '',
        )
