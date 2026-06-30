import uuid
import hashlib
from typing import Any, Dict, List
from app.services.agents.base import BaseAgent
from app.services.intent_parser import intent_parser
from app.services.hidden_requirements import hidden_detector
from app.services.job_feature_engineer import job_feature_extractor
from app.services.intent_graph import intent_graph_builder
from app.services.embedding_service import embedding_service
from app.core.logging.logging import logger

class JobIntelligenceAgent(BaseAgent):
    """
    Job Intelligence Agent (the 'brain' of recruiter intent parsing).
    Transforms unstructured JDs into structured profiles with semantic graphs,
    inferred requirements, features, multi-vector embeddings, and execution traces.
    """

    def __init__(self):
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info("job_intelligence_agent_initialized")

    async def validate(self, input_data: Any) -> bool:
        if not input_data:
            return False
        if isinstance(input_data, str) and len(input_data.strip()) > 20:
            return True
        if isinstance(input_data, dict) and ("raw_text" in input_data or "job_description" in input_data):
            text = input_data.get("raw_text") or input_data.get("job_description")
            if isinstance(text, str) and len(text.strip()) > 20:
                return True
        return False

    def explain(self) -> str:
        return (
            "JobIntelligenceAgent parses unstructured job descriptions, extracts explicit entities, "
            "infers hidden expectations, categorizes tech skills into hierarchies, engineers machine-learning features, "
            "creates a semantic relationship graph, and generates multi-vector embeddings for downstream candidate matching."
        )

    async def health(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "initialized": self._initialized,
            "components": {
                "intent_parser": "ready",
                "hidden_requirement_detector": "ready",
                "skill_classifier": "ready",
                "embedding_service": "ready"
            }
        }

    def version(self) -> str:
        return "1.0.0"

    def supported_inputs(self) -> List[str]:
        return ["raw_text", "job_description"]

    def supported_outputs(self) -> List[str]:
        return ["job_id", "title", "intent_profile", "intent_graph", "trace", "confidence_scores"]

    async def execute(self, input_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the analysis workflow.
        
        Args:
            input_data: Either a raw job description string or a dict.
            context: Shared dictionary from the orchestrator.
            
        Returns:
            A structured dict representing the Recruiter Intent Profile and trace metadata.
        """
        # Parse inputs
        if isinstance(input_data, str):
            raw_text = input_data
            job_id = context.get("job_id") or hashlib.md5(raw_text.encode("utf-8")).hexdigest()
        else:
            raw_text = input_data.get("raw_text") or input_data.get("job_description")
            job_id = input_data.get("id") or context.get("job_id") or hashlib.md5(raw_text.encode("utf-8")).hexdigest()

        # Context mapping
        context["job_id"] = job_id
        
        # Trace collection
        agent_trace = []

        def record_step(step_name: str, status: str = "SUCCESS", details: Any = None):
            agent_trace.append({
                "step": step_name,
                "status": status,
                "details": details
            })

        record_step("Input Received", details={"job_id": job_id, "size_chars": len(raw_text)})

        # 1. Parsing & Explicit Entity Extraction
        try:
            parsed_res = await intent_parser.parse(raw_text)
            profile = parsed_res["profile"]
            confidence_scores = parsed_res["confidence_scores"]
            record_step("Job Parsed", details={"title": profile.get("title")})
            record_step("Entities Extracted", details={"skills_count": len(profile.get("skills", {}).get("primary_skills", []))})
        except Exception as e:
            record_step("Job Parsed", status="FAILED", details={"error": str(e)})
            raise e

        # 2. Skill Classification Logging (already run inside parse, but we structure or log it here)
        record_step("Skills Classified", details={"classified_skills_count": len(profile.get("classified_skills", []))})

        # 3. Hidden expectation detection
        try:
            hidden_reqs = await hidden_detector.detect(raw_text)
            # Merge hidden requirement confidence scores
            for exp_name, exp_data in hidden_reqs.items():
                confidence_scores[exp_name] = exp_data.get("confidence_score", 0.0)
            record_step("Confidence Calculated")
        except Exception as e:
            logger.warning("hidden_requirements_failed_in_agent", error=str(e))
            hidden_reqs = {}
            record_step("Confidence Calculated", status="WARNING", details={"error": str(e)})

        # 4. Job Feature engineering
        try:
            engineered_features = job_feature_extractor.extract_features(profile, hidden_reqs)
            profile["engineered_features"] = engineered_features
        except Exception as e:
            logger.warning("feature_extraction_failed_in_agent", error=str(e))

        # 5. Graph construction
        try:
            intent_graph = intent_graph_builder.build_graph(profile, hidden_reqs)
            record_step("Intent Graph Built", details={"nodes_count": len(intent_graph["nodes"]), "edges_count": len(intent_graph["edges"])})
        except Exception as e:
            intent_graph = {"nodes": [], "edges": []}
            record_step("Intent Graph Built", status="FAILED", details={"error": str(e)})

        # 6. Generate multi-vector embeddings
        try:
            embeddings = await embedding_service.get_job_embeddings(job_id, profile, hidden_reqs, raw_text)
            record_step("Embeddings Generated", details={"keys": list(embeddings.keys())})
        except Exception as e:
            record_step("Embeddings Generated", status="FAILED", details={"error": str(e)})
            logger.warning("job_embeddings_failed_in_agent", error=str(e))

        # 7. Compile Structured Profile Produced
        record_step("Structured Profile Produced")
        
        # Package output
        result = {
            "job_id": job_id,
            "raw_text": raw_text,
            "title": profile["title"],
            "department": profile["department"],
            "seniority": profile["seniority"],
            "experience_required": profile["experience_required_years"],
            "employment_type": profile["employment_type"],
            "remote_type": profile["remote_compatibility"],
            "intent_profile": profile,
            "intent_graph": intent_graph,
            "trace": agent_trace,
            "confidence_scores": confidence_scores
        }
        
        # Save trace to context
        context["trace"] = agent_trace
        context["intent_profile"] = profile
        context["intent_graph"] = intent_graph
        context["confidence_scores"] = confidence_scores
        
        return result

job_agent = JobIntelligenceAgent()
# Register automatically with global orchestrator
from app.services.agents.orchestrator import orchestrator
orchestrator.register_agent("job_intelligence", job_agent)
