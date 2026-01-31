from abc import ABC, abstractmethod
from typing import Iterable


class UserContextInterface(ABC):

    @property
    @abstractmethod
    def id(self) -> str: ...

    @property
    @abstractmethod
    def roles(self) -> Iterable[str]: ...
