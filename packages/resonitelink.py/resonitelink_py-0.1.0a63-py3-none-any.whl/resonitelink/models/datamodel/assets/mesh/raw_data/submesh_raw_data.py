from resonitelink.json import abstract_json_model
from abc import ABC, abstractmethod


@abstract_json_model()
class SubmeshRawData(ABC):
    @property
    @abstractmethod
    def indices_count(self) -> int:
        raise NotImplementedError()
