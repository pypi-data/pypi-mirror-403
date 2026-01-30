from abc import ABC, abstractmethod
from typing import List

from .model import KnowledgeExtraction


class KnowledgeExtractor(ABC):

    @abstractmethod
    def extract(self, chunk: str) -> KnowledgeExtraction:
        pass

    def extract_batch(self, chunks: List[str]) -> List[KnowledgeExtraction]:
        return [self.extract(chunk) for chunk in chunks]
