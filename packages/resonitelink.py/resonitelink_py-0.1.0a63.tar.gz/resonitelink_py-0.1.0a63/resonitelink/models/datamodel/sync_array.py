from resonitelink.json import MISSING, abstract_json_model, json_list
from typing import List, Any
from abc import ABC, abstractmethod

from .member import Member


@abstract_json_model()
class SyncArray(Member, ABC):
    values : List[Any] = json_list("values", object, abstract=True, default=MISSING)

    @property
    @abstractmethod
    def element_type(self) -> str:
        raise NotImplementedError()
