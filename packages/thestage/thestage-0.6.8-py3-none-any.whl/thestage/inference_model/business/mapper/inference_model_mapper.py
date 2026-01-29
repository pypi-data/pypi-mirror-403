from typing import Optional

from thestage.inference_model.dto.inference_model_entity import InferenceModelEntity
from thestage.services.abstract_mapper import AbstractMapper
from thestage.inference_model.dto.inference_model import InferenceModel


class InferenceModelMapper(AbstractMapper):
    def build_entity(self, item: InferenceModel) -> Optional[InferenceModelEntity]:
        if not item:
            return None

        return InferenceModelEntity(
            public_id=item.public_id,
            slug=item.slug,
            status=item.status or '',
            commit_hash=item.commit_hash or '',
            environment_metadata=item.environment_metadata or {},
            started_at=item.created_at or '',
            finished_at=item.updated_at or ''  # TODO updated_at cannot be finished_at
        )
