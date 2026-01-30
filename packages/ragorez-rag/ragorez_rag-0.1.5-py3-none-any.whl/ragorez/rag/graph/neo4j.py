from neo4j import Driver
from sentence_transformers import SentenceTransformer

from .db import GraphDataBaseProvider
from .model import GraphSearchResponse, Relation, Entity, KnowledgeExtraction


class TextNeo4jDataBaseProvider(GraphDataBaseProvider):
    def __init__(
            self,
            driver: Driver,
            n_results: int = 5
    ):
        self.driver = driver
        self.n_results = n_results

    def search(self, knowledge: KnowledgeExtraction, n_results: int = None, **kwargs) -> GraphSearchResponse:
        query_entities = [entity.text for entity in knowledge.entities]
        n_results = n_results if n_results is not None else self.n_results
        with self.driver.session() as session:
            result = session.run("""
                MATCH (s)-[r]->(o)
                WHERE any(entity in $entities WHERE
                    toLower(s.text) CONTAINS toLower(entity) OR
                    toLower(o.text) CONTAINS toLower(entity))
                RETURN s.text as subject_text,
                       s.type as subject_type,
                       r.type as relation_type,
                       o.text as object_text,
                       o.type as object_type,
                       r.source as source
                LIMIT $limit
            """, entities=query_entities, limit=n_results)
            relations = []
            for record in result:
                subject = Entity(
                    text=record["subject_text"],
                    type=record["subject_type"]
                )
                object_ = Entity(
                    text=record["object_text"],
                    type=record["object_type"]
                )
                relations.append(Relation(
                    subject=subject,
                    predicate=record["relation_type"],
                    object=object_,
                    source=record["source"] or ""
                ))
            return GraphSearchResponse(relations=relations, full_response=result.consume())

    def add_knowledge(self, knowledge: list[KnowledgeExtraction], **kwargs):
        with self.driver.session() as session:
            for extraction in knowledge:
                entity_ids = {}
                for entity in extraction.entities:
                    result = session.run("""
                        MERGE (e:Entity {text: $text, type: $type})
                        ON CREATE SET e.created_at = timestamp()
                        ON MATCH SET e.updated_at = timestamp()
                        SET e.metadata = $metadata,
                            e.embedding = $embedding
                        RETURN id(e) as entity_id
                    """,
                                         text=entity.text,
                                         type=entity.type,
                                         metadata=entity.metadata,
                                         embedding=entity.embedding
                                         )
                    entity_id = result.single()["entity_id"]
                    entity_ids[f"{entity.type}:{entity.text}"] = entity_id
                for relation in extraction.relations:
                    subject_key = f"{relation.subject.type}:{relation.subject.text}"
                    object_key = f"{relation.object.type}:{relation.object.text}"
                    if subject_key in entity_ids and object_key in entity_ids:
                        session.run("""
                            MATCH (s:Entity) WHERE id(s) = $subject_id
                            MATCH (o:Entity) WHERE id(o) = $object_id
                            MERGE (s)-[r:RELATION {type: $relation_type}]->(o)
                            SET r.source = $source
                        """,
                                    subject_id=entity_ids[subject_key],
                                    object_id=entity_ids[object_key],
                                    relation_type=relation.predicate,
                                    source=relation.source
                                    )

    def close(self):
        if self.driver:
            self.driver.close()


class SemanticNeo4JDataBaseProvider(TextNeo4jDataBaseProvider):
    def __init__(
            self,
            driver: Driver,
            embedding_model: SentenceTransformer,
            n_results: int = 5
    ):
        super().__init__(driver, n_results)
        self.embedding_model = embedding_model
        self._setup_vector_index()

    def _setup_vector_index(self):
        with self.driver.session() as session:
            session.run("""
                CREATE VECTOR INDEX entity_embeddings IF NOT EXISTS
                FOR (e:Entity) ON e.embedding
                OPTIONS {indexConfig: {
                    `vector.dimensions`: $dimensions,
                    `vector.similarity_function`: 'cosine'
                }}
            """, dimensions=self.embedding_model.get_sentence_embedding_dimension())

    def search(self, knowledge: KnowledgeExtraction, n_results: int = None, **kwargs) -> GraphSearchResponse:
        n_results = n_results if n_results is not None else self.n_results
        relations = []
        with self.driver.session() as session:
            for entity in knowledge.entities:
                query_embedding = self.embedding_model.encode(entity.text)
                result = session.run("""
                    CALL db.index.vector.queryNodes(
                        'entity_embeddings', 
                        $top_k, 
                        $embedding
                    ) YIELD node, score
                    MATCH (node)-[r]->(related)
                    RETURN node.text as subject_text,
                           node.type as subject_type,
                           r.type as relation_type,
                           related.text as object_text,
                           related.type as object_type,
                           r.source as source,
                           score
                    ORDER BY score DESC
                    LIMIT $limit
                """, top_k=n_results, embedding=query_embedding, limit=n_results)
                for record in result:
                    subject = Entity(
                        text=record["subject_text"],
                        type=record["subject_type"]
                    )
                    object_ = Entity(
                        text=record["object_text"],
                        type=record["object_type"]
                    )
                    relations.append(Relation(
                        subject=subject,
                        predicate=record["relation_type"],
                        object=object_,
                        source=record["source"] or ""
                    ))
            return GraphSearchResponse(relations=relations)

    def add_knowledge(self, knowledge: list[KnowledgeExtraction], **kwargs):
        for extraction in knowledge:
            for entity in extraction.entities:
                entity.embedding = self.embedding_model.encode(entity.text).tolist()
        super().add_knowledge(knowledge, **kwargs)
