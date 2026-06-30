import time
import os
import psutil
from typing import Any, Dict, List
from app.services.agents.base import BaseAgent
from app.database.repositories.candidate import CandidateRepository
from app.api.v1.routers.dataset import map_entity_to_profile
from app.services.embedding_service import embedding_service
from app.core.logging.logging import logger

# Import all analyzers
from app.services.candidate_analyzers.career_analyzer import career_analyzer
from app.services.candidate_analyzers.technical_analyzer import technical_analyzer
from app.services.candidate_analyzers.project_analyzer import project_analyzer
from app.services.candidate_analyzers.leadership_analyzer import leadership_analyzer
from app.services.candidate_analyzers.domain_analyzer import domain_analyzer
from app.services.candidate_analyzers.career_growth import career_growth_analyzer
from app.services.candidate_analyzers.specialization_engine import specialization_engine
from app.services.candidate_analyzers.candidate_graph import candidate_graph_builder

class CandidateIntelligenceAgent(BaseAgent):
    """
    Candidate Intelligence Agent.
    Transforms raw candidate profiles into deep career intelligence profiles,
    analyzing technical depth, growth trajectories, project scale, leadership evidence,
    mapping knowledge graphs, and generating multi-vector embeddings.
    """

    def __init__(self):
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info("candidate_intelligence_agent_initialized")

    async def validate(self, input_data: Any) -> bool:
        if not input_data:
            return False
        # Valid inputs: candidate_id (str), or dict with "candidate_id" or "id"
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
            "CandidateIntelligenceAgent acts as a career intelligence expert. It extracts "
            "career progression velocity, estimates tech proficiencies (Beginner to Expert) based on evidence, "
            "evaluates project ownership & complexity, detects leadership & mentoring exposure, determines "
            "specializations, maps a semantic knowledge graph, and builds 8 separate vector embeddings."
        )

    async def health(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "initialized": self._initialized,
            "components": {
                "career_analyzer": "ready",
                "technical_analyzer": "ready",
                "project_analyzer": "ready",
                "leadership_analyzer": "ready",
                "domain_analyzer": "ready",
                "growth_analyzer": "ready",
                "specialization_engine": "ready",
                "graph_builder": "ready"
            }
        }

    def version(self) -> str:
        return "1.0.0"

    def supported_inputs(self) -> List[str]:
        return ["candidate_id", "id", "profile"]

    def supported_outputs(self) -> List[str]:
        return [
            "candidate_id", "professional_summary", "career_intelligence",
            "technical_intelligence", "leadership_intelligence", "project_intelligence",
            "domain_intelligence", "career_growth", "specializations", "knowledge_graph",
            "embeddings", "confidence_scores", "trace"
        ]

    async def execute(self, input_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes Candidate Career Intelligence evaluation pipeline.
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

        # 2. Career Analyzer
        try:
            career_intel = career_analyzer.analyze(profile)
            record_step("Career Analyzed", details={"years_experience": career_intel["career_progression"]["total_years_experience"]})
        except Exception as e:
            record_step("Career Analyzed", status="FAILED", details={"error": str(e)})
            raise e

        # 3. Technical Analyzer (Skill Proficiency Engine)
        try:
            technical_intel = technical_analyzer.analyze(profile)
            record_step("Skills Classified", details={"skills_count": len(technical_intel.get("all_tech_details", {}))})
        except Exception as e:
            record_step("Skills Classified", status="FAILED", details={"error": str(e)})
            raise e

        # 4. Project Analyzer
        try:
            project_intel = project_analyzer.analyze(profile)
            record_step("Projects Evaluated", details={"projects_count": len(project_intel.get("projects", []))})
        except Exception as e:
            record_step("Projects Evaluated", status="FAILED", details={"error": str(e)})
            raise e

        # 5. Leadership Analyzer
        try:
            leadership_intel = leadership_analyzer.analyze(profile)
            record_step("Leadership Inferred", details={"overall_leadership_score": leadership_intel["overall_leadership_score"]})
        except Exception as e:
            record_step("Leadership Inferred", status="FAILED", details={"error": str(e)})
            raise e

        # 6. Domain Analyzer
        try:
            domain_intel = domain_analyzer.analyze(profile)
        except Exception as e:
            logger.warning("domain_analyzer_failed", error=str(e))
            domain_intel = {"detected_domains": {}, "overall_diversity_score": 0.0}

        # 7. Specialization Engine
        try:
            spec_intel = specialization_engine.analyze(profile)
            specializations = spec_intel["specializations"]
        except Exception as e:
            logger.warning("specialization_engine_failed", error=str(e))
            spec_intel = {"scores": {}, "specializations": ["Full Stack"]}
            specializations = ["Full Stack"]

        # 8. Career Growth Analyzer
        try:
            growth_intel = career_growth_analyzer.analyze(profile, career_intel, technical_intel)
        except Exception as e:
            logger.warning("career_growth_analyzer_failed", error=str(e))
            growth_intel = {}

        # 9. Knowledge Graph Builder
        try:
            kg_intel = candidate_graph_builder.build_graph(profile, {
                "domains": domain_intel,
                "leadership": leadership_intel
            })
            record_step("Knowledge Graph Built", details={"nodes_count": len(kg_intel["nodes"]), "edges_count": len(kg_intel["edges"])})
        except Exception as e:
            record_step("Knowledge Graph Built", status="FAILED", details={"error": str(e)})
            kg_intel = {"nodes": [], "edges": []}

        # 10. Generate Professional Summary
        summary = (
            f"{profile.personal_info.first_name} {profile.personal_info.last_name} is a highly accomplished "
            f"{', '.join(specializations)} with {career_intel['career_progression']['total_years_experience']} years of "
            f"experience. They demonstrate a strong growth trajectory classed as '{career_intel['growth_trajectory']['trajectory_class']}' "
            f"and an overall project execution rating of {project_intel['average_project_score']}/100."
        )

        # 11. Format texts for the 8 multi-vector embeddings
        overall_text = f"Candidate: {profile.personal_info.first_name} {profile.personal_info.last_name}. Summary: {summary}."
        
        career_text = (
            f"Candidate: {profile.personal_info.first_name} {profile.personal_info.last_name}. "
            f"Career Path: {' -> '.join(career_intel['career_progression']['role_evolution'])}. "
            f"Growth Velocity: {growth_intel.get('growth_velocity', 0.0)}. "
            f"Tenure Stability Score: {career_intel['career_stability']['stability_score']}."
        )

        proj_segments = []
        for p in project_intel["projects"]:
            proj_segments.append(
                f"Project: {p['project_name']} (Role: {p['ownership']}, Domain: {p['domain']}, Rating: {p['project_score']}). "
                f"Tech used: {', '.join(p['technologies'])}."
            )
        projects_text = " ".join(proj_segments) if proj_segments else "No projects recorded."

        skills_segments = []
        for tech, details in technical_intel.get("all_tech_details", {}).items():
            skills_segments.append(f"{tech} ({details['proficiency_level']} level, {details['years_of_usage']} years)")
        skills_text = f"Technical Skills: {', '.join(skills_segments)}."

        leadership_text = (
            f"Leadership evaluation: Team Management Level: {leadership_intel['team_leadership']['level']}. "
            f"Mentoring Level: {leadership_intel['mentoring']['level']}. "
            f"Architecture Ownership Level: {leadership_intel['architecture_ownership']['level']}. "
            f"Overall Leadership Rating: {leadership_intel['overall_leadership_score']}/100."
        )

        dom_segments = []
        for dom, details in domain_intel["detected_domains"].items():
            dom_segments.append(f"{dom} ({details['proficiency_level']}, {details['exposure_years']} years)")
        domains_text = f"Industry Vertical Experience: {', '.join(dom_segments)}" if dom_segments else "No specific vertical exposure detected."

        specialization_text = f"Candidate roles classification match scores: {str(spec_intel['scores'])}. Primary specializations: {', '.join(specializations)}."

        node_types = {}
        for node in kg_intel["nodes"]:
            node_types[node["type"]] = node_types.get(node["type"], 0) + 1
        kg_summary_text = (
            f"Knowledge Graph of candidate {profile.personal_info.first_name} {profile.personal_info.last_name}. "
            f"Nodes structure: {str(node_types)}. Connections count: {len(kg_intel['edges'])} relationships."
        )

        embedding_inputs = {
            "overall": overall_text,
            "career": career_text,
            "projects": projects_text,
            "skills": skills_text,
            "leadership": leadership_text,
            "domains": domains_text,
            "specialization": specialization_text,
            "knowledge_graph_summary": kg_summary_text
        }

        # Generate separate embeddings (incremental cache check is automatic)
        try:
            embeddings = await embedding_service.get_candidate_intelligence_embeddings(
                candidate_id=candidate_id,
                texts=embedding_inputs
            )
            record_step("Embeddings Generated", details={"keys": list(embeddings.keys())})
        except Exception as e:
            record_step("Embeddings Generated", status="FAILED", details={"error": str(e)})
            logger.warning("candidate_embeddings_failed_in_agent", error=str(e))
            embeddings = {}

        # 12. Compile Confidence Engine matrix (ensuring evidence-based inputs)
        # Gather top confidence metrics
        confidence_scores = {}
        # Python expert if present
        python_details = technical_intel.get("all_tech_details", {}).get("Python")
        if python_details:
            confidence_scores["Python Expert"] = float(python_details["confidence_score"])
        else:
            confidence_scores["Python Expert"] = 0.0

        confidence_scores["Leadership"] = float(leadership_intel["overall_confidence_score"])
        
        # Cloud confidence
        cloud_details = technical_intel.get("cloud_platforms_stats", {})
        confidence_scores["Cloud Experience"] = float(cloud_details.get("average_confidence", 0.85))

        # Backend Architecture confidence
        sys_details = technical_intel.get("system_design_stats", {})
        arch_details = technical_intel.get("architecture_experience_stats", {})
        confidence_scores["Backend Architecture"] = float(max(
            sys_details.get("average_confidence", 0.0),
            arch_details.get("average_confidence", 0.0),
            0.75  # fallback baseline
        ))

        # 13. Future-proofed Behavior placeholder
        behavior_placeholder = {
            "working_style_indicator": profile.behavior_signals.working_style or "Autonomous / High Ownership",
            "collaboration_readiness": bool(profile.behavior_signals.leadership_exposure or leadership_intel["cross_functional_collaboration"]["has_exposure"]),
            "tenure_commitment": float(profile.behavior_signals.average_tenure_years or career_intel["career_stability"]["average_tenure_years"]),
            "churn_risk_score": float(round(100.0 - career_intel["career_stability"]["stability_score"], 1))
        }

        # Create structured Candidate Intelligence Profile
        intelligence_profile = {
            "candidate_id": candidate_id,
            "professional_summary": summary,
            "career_intelligence": career_intel,
            "technical_intelligence": technical_intel,
            "leadership_intelligence": leadership_intel,
            "project_intelligence": project_intel,
            "domain_intelligence": domain_intel,
            "career_growth": growth_intel,
            "specializations": specializations,
            "behavior_placeholder": behavior_placeholder,
            "knowledge_graph": kg_intel,
            "confidence_scores": confidence_scores
        }

        # Track observability performance parameters
        end_cpu = psutil.cpu_percent(interval=None)
        end_mem = process.memory_info().rss / (1024 * 1024)
        
        # Final trace step
        record_step("Candidate Intelligence Profile Created", details={
            "inference_cpu_delta": float(end_cpu - start_cpu),
            "inference_mem_delta_mb": float(round(end_mem - start_mem, 2)),
            "specializations_detected": specializations
        })

        intelligence_profile["trace"] = agent_trace

        # Update context
        context["candidate_id"] = candidate_id
        context["candidate_profile"] = profile
        context["intelligence_profile"] = intelligence_profile

        return intelligence_profile

candidate_agent = CandidateIntelligenceAgent()
# Auto register under the global orchestrator
from app.services.agents.orchestrator import orchestrator
orchestrator.register_agent("candidate_intelligence", candidate_agent)
