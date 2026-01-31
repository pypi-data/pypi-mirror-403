from datetime import datetime
from typing import ClassVar, Protocol


class BaseEntityInterface(Protocol):
    PK_FIELD: ClassVar[str]

    @property
    def id(self) -> str: ...

    @property
    def created_at(self) -> datetime: ...

    @property
    def updated_at(self) -> datetime: ...
