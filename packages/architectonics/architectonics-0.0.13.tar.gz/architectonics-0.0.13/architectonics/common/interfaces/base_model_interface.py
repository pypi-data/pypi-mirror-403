from abc import ABC, abstractmethod
from datetime import datetime


class BaseModelInterface(ABC):

    @property
    @abstractmethod
    def id(self) -> str: ...

    @property
    @abstractmethod
    def created_at(self) -> datetime: ...

    @property
    @abstractmethod
    def updated_at(self) -> datetime: ...
