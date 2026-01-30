from resonitelink.json import MISSING, abstract_json_model, json_element
from typing import Any
from abc import ABC, abstractmethod

from .member import Member


@abstract_json_model()
class Field(Member, ABC):
    value : Any = json_element("value", object, default=MISSING, abstract=True)

    @property
    @abstractmethod
    def value_type_name(self) -> str:
        raise NotImplementedError()
