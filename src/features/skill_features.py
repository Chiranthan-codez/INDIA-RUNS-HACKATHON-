import math
import re
from src.ingestion.candidate_model import Candidate
from src.config.settings import JDRequirements


# Canonical skill taxonomy mapped to JD requirements.
# Each key is a "JD requirement bucket"; values are skill name patterns that satisfy it.
JD_SKILL_BUCKETS = {
    "embeddings_retrieval": [
        "sentence-transformers", "sentence transformers", "embeddings",
        "embedding", "bge", "e5", "openai embeddings", "word2vec",
        "dense retrieval", "semantic search", "neural retrieval",
    ],
    "vector_database": [
        "pinecone", "weaviate", "qdrant", "milvus", "opensearch",
        "elasticsearch", "faiss", "vector database", "vector db",
        "annoy", "scann", "chroma", "chromadb",
    ],
    "python": [
        "python",
    ],
    "ranking_evaluation": [
        "ndcg", "mrr", "map", "ranking", "information retrieval",
        "search relevance", "a/b testing", "evaluation framework",
        "learning to rank", "ltr",
    ],
    "llm_finetuning": [
        "lora", "qlora", "peft", "fine-tuning", "fine tuning",
        "finetuning", "llm", "large language model",
    ],
    "nlp_core": [
        "nlp", "natural language processing", "text classification",
        "named entity", "ner", "transformers", "bert", "gpt",
        "huggingface", "hugging face", "tokenization", "spacy",
    ],
    "ml_frameworks": [
        "pytorch", "tensorflow", "keras", "scikit-learn", "sklearn",
        "xgboost", "lightgbm", "catboost",
    ],
    "data_engineering": [
        "spark", "airflow", "kafka", "data pipeline", "etl",
        "data engineering", "dbt", "snowflake", "bigquery",
    ],
}


class SkillFeatures:
    """
    Extracts skill-alignment features by matching candidate skills against
    the JD's required and preferred skill buckets.

    Algorithm:
        For each candidate skill, check if it matches any JD skill bucket.
        Weight matches by proficiency level, endorsement count, and usage duration.

    Complexity: O(S * B * P) per candidate where S = skills, B = buckets, P = patterns.
    For typical values (S=15, B=8, P=10): ~1200 comparisons — negligible.
    """

    PROFICIENCY_WEIGHTS = {
        "expert": 1.0,
        "advanced": 0.75,
        "intermediate": 0.5,
        "beginner": 0.25,
    }

    def __init__(self, jd: JDRequirements):
        self.jd = jd
        # Pre-compile regex patterns for each bucket
        self._bucket_patterns = {}
        for bucket_name, patterns in JD_SKILL_BUCKETS.items():
            escaped = [re.escape(p) for p in patterns]
            combined = r"\b(" + "|".join(escaped) + r")\b"
            self._bucket_patterns[bucket_name] = re.compile(combined, re.IGNORECASE)

    def extract(self, candidate: Candidate) -> dict:
        skills = candidate.skills

        matched_buckets = set()
        total_weighted_score = 0.0
        expert_zero_duration_count = 0
        total_skill_count = len(skills)

        for skill in skills:
            skill_name = skill.name.lower()
            proficiency_w = self.PROFICIENCY_WEIGHTS.get(skill.proficiency, 0.25)
            endorsement_w = math.log1p(skill.endorsements)
            duration_w = math.log1p(skill.duration_months)

            # Check for keyword stuffer signal: expert + 0 months
            if skill.proficiency == "expert" and skill.duration_months == 0:
                expert_zero_duration_count += 1

            # Match against each JD bucket
            for bucket_name, pattern in self._bucket_patterns.items():
                if pattern.search(skill_name):
                    matched_buckets.add(bucket_name)
                    total_weighted_score += proficiency_w * endorsement_w * duration_w

        # Normalize
        num_buckets = len(JD_SKILL_BUCKETS)
        bucket_coverage = len(matched_buckets) / num_buckets if num_buckets > 0 else 0.0

        # Trust multiplier: penalizes candidates with many expert-0-duration skills
        trust_multiplier = 1.0
        if expert_zero_duration_count >= 3:
            trust_multiplier = max(0.1, 1.0 - 0.15 * expert_zero_duration_count)

        return {
            "skill_bucket_coverage": bucket_coverage,
            "skill_weighted_score": total_weighted_score,
            "skill_matched_bucket_count": float(len(matched_buckets)),
            "skill_total_count": float(total_skill_count),
            "skill_trust_multiplier": trust_multiplier,
            "skill_expert_zero_count": float(expert_zero_duration_count),
        }
