from dataclasses import dataclass, field
from datetime import datetime
import uuid

from architectonics.common.interfaces.base_model_interface import BaseModelInterface


@dataclass
class BaseModel(BaseModelInterface):
    id: str = field(
        default_factory=lambda: str(
            uuid.uuid4(),
        ),
    )

    created_at: datetime = field(
        default_factory=datetime.utcnow,
    )

    updated_at: datetime = field(
        default_factory=datetime.utcnow,
    )
