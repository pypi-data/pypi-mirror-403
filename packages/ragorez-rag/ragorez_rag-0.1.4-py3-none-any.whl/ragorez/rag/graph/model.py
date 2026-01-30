from dataclasses import dataclass
from typing import Dict, Any, List, Iterable, Optional


@dataclass
class Entity:
    text: str
    type: str
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Relation:
    subject: Entity
    predicate: str
    object: Entity
    source: str = ""


@dataclass
class GraphSearchResponse:
    relations: list[Relation]
    full_response: Any = None

    def get_sources(self) -> list[str]:
        return [i.source for i in self.relations]


@dataclass
class KnowledgeExtraction:
    chunk: str
    entities: List[Entity]
    relations: List[Relation]
    metadata: Dict[str, Any] = None
