from abc import ABC, abstractmethod
from itertools import chain
from typing import Iterable

from .knowledge_extraction import KnowledgeExtraction
from .model import GraphSearchResponse


class GraphDataBaseProvider(ABC):

    @abstractmethod
    def search(self, knowledge: KnowledgeExtraction, n_results: int = None, **kwargs) -> GraphSearchResponse:
        pass

    @abstractmethod
    def add_knowledge(self, knowledge: list[KnowledgeExtraction], **kwargs):
        pass


def union_graph_search_response(responses: Iterable[GraphSearchResponse]) -> GraphSearchResponse:
    all_relations = chain.from_iterable(response.relations for response in responses)
    return GraphSearchResponse(relations=all_relations,
                               full_response=(i.full_response for i in responses if i.full_response))


class GraphDataBaseMultiStrategyProvider(GraphDataBaseProvider):

    def __init__(self, search_db: list[GraphDataBaseProvider] | GraphDataBaseProvider,
                 insert_db: list[GraphDataBaseProvider] | GraphDataBaseProvider):
        self.search_dbs = search_db if isinstance(search_db, list) else [search_db]
        self.insert_dbs = insert_db if isinstance(insert_db, list) else [insert_db]

    def add_knowledge(self, knowledge: list[KnowledgeExtraction], **kwargs):
        for db in self.insert_dbs:
            db.add_knowledge(knowledge, **kwargs)

    def search(self, knowledge: KnowledgeExtraction, n_results: int = None, **kwargs) -> GraphSearchResponse:
        return union_graph_search_response(
            (db.search(knowledge, n_results, **kwargs) for db in self.search_dbs))
