import time
import os
import psutil
from typing import Any, Dict, List
from app.services.agents.base import BaseAgent
from app.database.repositories.candidate import CandidateRepository
from app.api.v1.routers.dataset import map_entity_to_profile
from app.core.logging.logging import logger

# Import all sub-engines
from app.services.evidence_analyzers.skill_evidence import skill_evidence_engine
from app.services.evidence_analyzers.timeline_engine import timeline_engine
from app.services.evidence_analyzers.project_evidence import project_evidence_analyzer
from app.services.evidence_analyzers.potential_engine import potential_engine
from app.services.evidence_analyzers.risk_detector import risk_detector
from app.services.evidence_analyzers.evidence_graph import evidence_graph_builder

class EvidenceVerificationAgent(BaseAgent):
    """
    Evidence Verification Agent.
    Validates claimed software capabilities, aggregates technology usage timelines,
    uncovers resume anomalies/risks, maps Candidate Potential metrics, and outputs Evidence Graphs.
    """

    def __init__(self):
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info("evidence_verification_agent_initialized")

    async def validate(self, input_data: Any) -> bool:
        if not input_data:
            return False
        if isinstance(input_data, str) and len(input_data.strip()) > 0:
            return True
        if isinstance(input_data, dict) and ("candidate_id" in input_data or "id" in input_data):
            return True
        from app.schemas.candidate import CandidateProfile
        if isinstance(input_data, CandidateProfile):
            return True
        return False

    def explain(self) -> str:
        return (
            "EvidenceVerificationAgent serves as an evidence reasoning auditor. It checks "
            "candidate skills against job timelines and projects, identifies technology inflation "
            "and resume inconsistencies, measures Continuous Learning rates, maps readiness scores, "
            "and creates the Evidence Graph."
        )

    async def health(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "initialized": self._initialized,
            "components": {
                "skill_evidence_engine": "ready",
                "timeline_engine": "ready",
                "project_evidence_analyzer": "ready",
                "potential_engine": "ready",
                "risk_detector": "ready",
                "evidence_graph_builder": "ready"
            }
        }

    def version(self) -> str:
        return "1.0.0"

    def supported_inputs(self) -> List[str]:
        return ["candidate_id", "id", "profile"]

    def supported_outputs(self) -> List[str]:
        return [
            "candidate_id", "skill_verification", "timeline", "potential_metrics",
            "risk_analysis", "evidence_graph", "trace", "confidence_scores"
        ]

    async def execute(self, input_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes Candidate Evidence Verification pipeline.
        """
        agent_trace = []
        start_cpu = psutil.cpu_percent(interval=None)
        process = psutil.Process(os.getpid())
        start_mem = process.memory_info().rss / (1024 * 1024)

        def record_step(step_name: str, status: str = "SUCCESS", details: Any = None):
            agent_trace.append({
                "step": step_name,
                "status": status,
                "details": details,
                "timestamp": time.time()
            })

        # 1. Resolve & Load Candidate Profile
        candidate_id = None
        profile = None

        if isinstance(input_data, str):
            candidate_id = input_data
        elif isinstance(input_data, dict):
            candidate_id = input_data.get("candidate_id") or input_data.get("id")
        else:
            from app.schemas.candidate import CandidateProfile
            if isinstance(input_data, CandidateProfile):
                profile = input_data
                candidate_id = profile.id

        if not profile and candidate_id:
            db_session = context.get("db")
            if not db_session:
                raise ValueError("Database session ('db') is required in context to load candidate by ID.")
            repo = CandidateRepository(db_session)
            db_cand = await repo.get_candidate_profile(candidate_id)
            if not db_cand:
                raise ValueError(f"Candidate profile for ID {candidate_id} not found in database.")
            profile = map_entity_to_profile(db_cand)

        if not profile:
            raise ValueError("Failed to resolve candidate profile from input.")

        record_step("Candidate Loaded", details={"candidate_id": candidate_id, "name": f"{profile.personal_info.first_name} {profile.personal_info.last_name}"})

        # 2. Gather Evidence (Skills Verification)
        try:
            skills_verification = skill_evidence_engine.verify_skills(profile)
            record_step("Evidence Gathered", details={"skills_checked_count": len(skills_verification)})
        except Exception as e:
            record_step("Evidence Gathered", status="FAILED", details={"error": str(e)})
            raise e

        # 3. Skills Verified details
        verified_count = sum(1 for s in skills_verification.values() if s["status"] == "Verified")
        record_step("Skills Verified", details={"verified_skills_count": verified_count})

        # 4. Generate Chronological Tech Timeline
        try:
            tech_timeline = timeline_engine.generate_timeline(profile)
            career_progression = timeline_engine.analyze_progression(profile, tech_timeline)
            record_step("Timeline Generated", details={"years_covered": list(tech_timeline.keys())})
        except Exception as e:
            record_step("Timeline Generated", status="FAILED", details={"error": str(e)})
            raise e

        # 5. Evaluate Project Evidences
        try:
            projects_verification = project_evidence_analyzer.analyze_projects(profile)
        except Exception as e:
            logger.warning("projects_verification_failed", error=str(e))
            projects_verification = {"projects": [], "average_project_evidence_score": 50.0}

        # 6. Estimate Candidate Potential
        try:
            potentials_intel = potential_engine.analyze_potential(profile, career_progression, skills_verification, projects_verification["projects"])
            record_step("Potential Estimated", details={"learning_velocity_score": potentials_intel["learning_velocity"]["continuous_learning_score"]})
        except Exception as e:
            record_step("Potential Estimated", status="FAILED", details={"error": str(e)})
            raise e

        # 7. Run Risk Detector
        try:
            risk_report = risk_detector.detect_risks(profile, skills_verification)
            record_step("Risk Analysis", details={"risk_level": risk_report["risk_level"], "warnings_count": len(risk_report["explanations"])})
        except Exception as e:
            record_step("Risk Analysis", status="FAILED", details={"error": str(e)})
            raise e

        # 8. Build Evidence Graph
        try:
            evidence_graph = evidence_graph_builder.build_graph(profile, skills_verification, tech_timeline, potentials_intel, risk_report)
            record_step("Evidence Graph Built", details={"nodes_count": len(evidence_graph["nodes"]), "edges_count": len(evidence_graph["edges"])})
        except Exception as e:
            record_step("Evidence Graph Built", status="FAILED", details={"error": str(e)})
            evidence_graph = {"nodes": [], "edges": []}

        # 9. Confidence Calculated step
        overall_confidence = float(round((100.0 - risk_report["risk_score"]) / 100.0, 2))
        confidence_scores = {
            "overall_verification_confidence": float(max(0.10, overall_confidence)),
            "skills_verification_confidence": float(skills_verification.get("Python", {}).get("confidence_score", 0.85) if "Python" in skills_verification else 0.80),
            "timeline_confidence": float(0.90),
            "potential_score_confidence": float(potentials_intel["potentials"]["growth_potential"])
        }
        
        # Structure the chronological timeline to keep standard types for JSON (mapping keys to strings)
        timeline_dict = {str(k): v for k, v in tech_timeline.items()}

        record_step("Confidence Calculated")

        # Compile final structured verification report
        verification_profile = {
            "candidate_id": candidate_id,
            "skill_verification": skills_verification,
            "timeline": {
                "chronological_tech_timeline": timeline_dict,
                "career_progression": career_progression
            },
            "potential_metrics": potentials_intel,
            "risk_analysis": risk_report,
            "evidence_graph": evidence_graph,
            "confidence_scores": confidence_scores
        }

        # Track observability performance parameters
        end_cpu = psutil.cpu_percent(interval=None)
        end_mem = process.memory_info().rss / (1024 * 1024)

        record_step("Evidence Verification Profile Created", details={
            "verification_cpu_delta": float(end_cpu - start_cpu),
            "verification_mem_delta_mb": float(round(end_mem - start_mem, 2))
        })

        verification_profile["trace"] = agent_trace

        # Update context
        context["candidate_id"] = candidate_id
        context["verification_profile"] = verification_profile

        return verification_profile

evidence_verification_agent = EvidenceVerificationAgent()
# Auto register under the global orchestrator
from app.services.agents.orchestrator import orchestrator
orchestrator.register_agent("evidence_verification", evidence_verification_agent)
