from dataclasses import dataclass
from typing import Dict, Any

from .graph.db import GraphDataBaseProvider
from .graph.knowledge_extraction import KnowledgeExtractor
from .llm.llm_provider import LLMProvider
from .vector.db import VectorDataBaseProvider


@dataclass
class GraphRagPipelineSettings:
    graph_db: GraphDataBaseProvider
    knowledge_extractor: KnowledgeExtractor


@dataclass
class GraphRAGPipelineResult:
    additional_context: list[str]


class GraphRAGPipeline:
    def __init__(self, settings: GraphRagPipelineSettings):
        self.graph_db = settings.graph_db
        self.knowledge_extractor = settings.knowledge_extractor

    def process(self, question: str, chunks: list[str]) -> GraphRAGPipelineResult:
        knowledge = self.knowledge_extractor.extract_batch(chunks)
        self.graph_db.add_knowledge(knowledge)
        knowledge = self.knowledge_extractor.extract(question)
        sources = self.graph_db.search(knowledge).get_sources()
        return GraphRAGPipelineResult(additional_context=list(sources))


@dataclass
class RAGPipelineSettings:
    vector_db: VectorDataBaseProvider
    llm_provider: LLMProvider
    system_template: str = None
    prompt_template: str = None
    graph_rag_pipeline: GraphRAGPipeline = None


class RAGPipeline:

    def __init__(self, settings: RAGPipelineSettings, **kwargs):
        """
        prompt_template works with {question} and {context}. Question = initial prompt. Context = result of searching in knowledge database
        """
        self.vector_db: VectorDataBaseProvider = settings.vector_db
        self.llm: LLMProvider = settings.llm_provider
        self.system_template: str = settings.system_template
        self.prompt_template: str = settings.prompt_template or "Question: {question}.\nAdditional Context:{context}."
        self.graph_rag_pipeline = settings.graph_rag_pipeline

    def process(self,
                question: str,
                n_results: int = 5) -> Dict[str, Any]:
        search_results = self.vector_db.search(question, n_results)
        context = "\n".join(search_results.answers) + ". "
        if self.graph_rag_pipeline is not None:
            additional_context = self._call_graph_rag(question, search_results.answers).additional_context
            context += ".".join(additional_context)
        prompt = self.prompt_template.format(context=context, question=question)
        response = self.llm.generate(
            prompt=prompt,
            system_message=self.system_template,
            temperature=0,
            max_tokens=1000
        )
        return {
            "question": question,
            "answer": response,
            "sources": context,
        }

    def _call_graph_rag(self, question: str, chunks: list[str]) -> GraphRAGPipelineResult:
        return self.graph_rag_pipeline.process(question, chunks)
