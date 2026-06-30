from app.core.config.config import settings

class FeatureFlagManager:
    @staticmethod
    def is_enabled(flag_name: str) -> bool:
        """
        Verify if a given platform module is enabled via active configuration flags.
        """
        flag_map = {
            "semantic_search": settings.FLAG_SEMANTIC_SEARCH,
            "embedding_engine": settings.FLAG_EMBEDDING_ENGINE,
            "behavior_engine": settings.FLAG_BEHAVIOR_ENGINE,
            "evidence_engine": settings.FLAG_EVIDENCE_ENGINE,
            "analytics": settings.FLAG_ANALYTICS,
            "explainability": settings.FLAG_EXPLAINABILITY,
            "knowledge_graph": settings.FLAG_KNOWLEDGE_GRAPH,
            "authentication": settings.FLAG_AUTHENTICATION,
        }
        return flag_map.get(flag_name.lower(), False)

feature_flags = FeatureFlagManager()
