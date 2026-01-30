import chromadb

from .db import VectorDataBaseProvider, VectorSearchResponse


class ChromaDbProvider(VectorDataBaseProvider):
    def __init__(self,
                 collection: chromadb.Collection):
        self.collection = collection

    def search(self, query: str, n_results: int = 5, **kwargs) -> VectorSearchResponse:
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return VectorSearchResponse(answers=results['documents'][0])
