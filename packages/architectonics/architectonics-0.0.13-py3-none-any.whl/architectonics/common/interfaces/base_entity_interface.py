from abc import ABC, abstractmethod
from datetime import datetime
from typing import ClassVar


class BaseEntityInterface(ABC):
    PK_FIELD: ClassVar[str]

    @property
    @abstractmethod
    def id(self) -> str: ...

    @property
    @abstractmethod
    def created_at(self) -> datetime: ...

    @property
    @abstractmethod
    def updated_at(self) -> datetime: ...
