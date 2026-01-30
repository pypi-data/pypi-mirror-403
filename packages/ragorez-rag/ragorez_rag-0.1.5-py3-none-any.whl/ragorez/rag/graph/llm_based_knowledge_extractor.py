import yaml

from .knowledge_extraction import KnowledgeExtractor
from .model import KnowledgeExtraction, Relation, Entity
from ..llm.llm_provider import LLMProvider

SYSTEM_MESSAGE_ADDITIONAL = """
CRITICAL RULES FOR OUTPUT FORMAT:
1. You MUST return ONLY a valid YAML object, NOTHING ELSE
2. NO markdown formatting (no ```yaml ```)
3. NO additional text before or after the YAML
4. USE LANGUAGE OF ORIGINAL TEXT

REQUIRED YAML STRUCTURE:
entities:
  - text: "Entity name"
    type: "Entity type"
relations:
  - subject: "subject"
    predicate: "relation"
    object: "object"
"""


def clean_markdown(response: str):
    if response.startswith("```") and response.endswith("```"):
        lines = response.splitlines()
        return "\n".join(lines[1:-1])
    return response


class LLMBasedKnowledgeExtractor(KnowledgeExtractor):
    def __init__(self, llm_provider: LLMProvider, **kwargs):
        self.llm = llm_provider
        self.system_message = ((kwargs.get("system_message") or "Parse input text. Return only entities and relations")
                               + SYSTEM_MESSAGE_ADDITIONAL)
        self.prompt_template = kwargs.get("prompt_template") or """{input}"""
        self.cleaners = kwargs.get("cleaner") or [lambda x: clean_markdown(x)]

    def extract(self, chunk: str) -> KnowledgeExtraction:
        response = self.llm.generate(
            prompt=self.prompt_template.format(input=chunk),
            system_message=self.system_message,
            temperature=0,
            max_tokens=500
        )
        for cleaner in self.cleaners:
            response = cleaner(response)
        try:
            data = yaml.safe_load(response)
        except:
            return KnowledgeExtraction(chunk="", entities=[], relations=[])
        entities = {
            e["text"]: Entity(text=e["text"], type=e.get("type", "UNKNOWN"))
            for e in data.get("entities", [])
        }
        relations = []
        for rel in data.get("relations", []):
            subject = entities.get(rel["subject"]) or Entity(text=rel["subject"], type="UNKNOWN")
            object_ = entities.get(rel["object"]) or Entity(text=rel["object"], type="UNKNOWN")
            relations.append(Relation(
                subject=subject,
                predicate=rel["predicate"],
                object=object_,
                source=chunk
            ))
        return KnowledgeExtraction(
            chunk=chunk,
            entities=list(entities.values()),
            relations=relations
        )
