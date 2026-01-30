from abc import ABC, abstractmethod

from attr import dataclass


@dataclass
class VectorSearchResponse:
    answers: list[str]
    full_response: str = None


class VectorDataBaseProvider(ABC):

    @abstractmethod
    def search(self, query: str, n_results: int = 5, **kwargs) -> VectorSearchResponse:
        pass
