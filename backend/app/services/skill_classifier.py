import numpy as np
from typing import Dict, Any, List
from app.services.normalizer import skill_normalizer
from app.services.embedding_service import embedding_service
from app.core.logging.logging import logger

class SkillClassificationEngine:
    """
    Categorizes skills into high-fidelity hierarchical paths.
    Enables structured tech stack matching.
    """
    TAXONOMY = {
        "python": ["Programming Language", "Backend", "AI Ecosystem"],
        "kubernetes": ["DevOps", "Container Orchestration", "Cloud Infrastructure"],
        "docker": ["DevOps", "Containerization", "Cloud Infrastructure"],
        "javascript": ["Programming Language", "Frontend", "Web Ecosystem"],
        "typescript": ["Programming Language", "Frontend", "Web Ecosystem"],
        "java": ["Programming Language", "Backend", "Enterprise Ecosystem"],
        "go": ["Programming Language", "Backend", "Cloud Native Ecosystem"],
        "c++": ["Programming Language", "Systems Programming", "High Performance Systems"],
        "rust": ["Programming Language", "Systems Programming", "Memory Safety Systems"],
        "aws": ["Cloud Platform", "Cloud Infrastructure", "Amazon Web Services"],
        "gcp": ["Cloud Platform", "Cloud Infrastructure", "Google Cloud Platform"],
        "azure": ["Cloud Platform", "Cloud Infrastructure", "Microsoft Azure"],
        "pytorch": ["Framework", "AI Ecosystem", "Deep Learning"],
        "tensorflow": ["Framework", "AI Ecosystem", "Deep Learning"],
        "fastapi": ["Framework", "Backend", "API Services"],
        "react": ["Framework", "Frontend", "Web Ecosystem"],
        "angular": ["Framework", "Frontend", "Web Ecosystem"],
        "vue": ["Framework", "Frontend", "Web Ecosystem"],
        "sql": ["Database", "SQL", "Relational Database"],
        "postgresql": ["Database", "SQL", "Relational Database"],
        "mongodb": ["Database", "NoSQL", "Document Database"],
        "redis": ["Database", "NoSQL", "In-Memory Database"],
        "terraform": ["DevOps", "Infrastructure as Code", "Cloud Infrastructure"],
        "git": ["DevOps", "Version Control", "Collaboration Tools"],
    }

    def __init__(self):
        # We can precompute embeddings for TAXONOMY keys for semantic fallback
        self._taxonomy_embeddings = {}

    async def _get_closest_taxonomy_match(self, skill_name: str) -> str | None:
        """
        Calculates cosine similarity between input skill and taxonomy keys using local embedding provider.
        """
        try:
            # Check for exact case-insensitive match first
            skill_clean = skill_name.strip().lower()
            if skill_clean in self.TAXONOMY:
                return skill_clean
                
            # If not found, use embeddings
            if not self._taxonomy_embeddings:
                keys = list(self.TAXONOMY.keys())
                vectors = await embedding_service.provider.embed_documents(keys)
                self._taxonomy_embeddings = dict(zip(keys, vectors))

            skill_vector = await embedding_service.provider.embed_query(skill_name)
            
            best_match = None
            highest_score = -1.0
            
            for key, key_vector in self._taxonomy_embeddings.items():
                dot_product = np.dot(skill_vector, key_vector)
                norm_a = np.linalg.norm(skill_vector)
                norm_b = np.linalg.norm(key_vector)
                similarity = float(dot_product / (norm_a * norm_b) if norm_a > 0 and norm_b > 0 else 0.0)
                
                if similarity > highest_score:
                    highest_score = similarity
                    best_match = key
            
            # Allow semantic match only if similarity > 0.75
            if highest_score > 0.75:
                return best_match
        except Exception as e:
            logger.error("skill_semantic_fallback_failed", skill=skill_name, error=str(e))
        return None

    async def classify(self, skill_name: str) -> Dict[str, Any]:
        """
        Classifies skill and returns full hierarchical path.
        """
        s_clean = skill_name.strip().lower()
        
        # 1. Check exact taxonomy
        if s_clean in self.TAXONOMY:
            path = self.TAXONOMY[s_clean]
            return {
                "name": skill_name,
                "normalized_name": skill_name.title() if s_clean not in ["aws", "gcp", "k8s"] else skill_name.upper(),
                "category": path[0],
                "hierarchy_path": [skill_name.title() if s_clean not in ["aws", "gcp", "k8s"] else skill_name.upper()] + path
            }

        # 2. Check general normalizer ALIASES & HIERARCHY
        norm_res = skill_normalizer.normalize(skill_name)
        if norm_res["category"] != "Other":
            # Convert normalizer path into our 3-4 tier format
            path = norm_res["hierarchy_path"]
            return {
                "name": skill_name,
                "normalized_name": norm_res["normalized_name"],
                "category": norm_res["category"],
                "hierarchy_path": [norm_res["normalized_name"]] + path
            }

        # 3. Semantic fallback
        semantic_key = await self._get_closest_taxonomy_match(skill_name)
        if semantic_key:
            path = self.TAXONOMY[semantic_key]
            return {
                "name": skill_name,
                "normalized_name": skill_name.title(),
                "category": path[0],
                "hierarchy_path": [skill_name.title()] + path
            }

        # 4. Final Fallback
        return {
            "name": skill_name,
            "normalized_name": skill_name.strip(),
            "category": "Other",
            "hierarchy_path": [skill_name.strip(), "General Tech Stack"]
        }

skill_classifier = SkillClassificationEngine()
