import time
import os
import psutil
from typing import Any, Dict, List
from app.services.agents.base import BaseAgent
from app.database.repositories.job import JobRepository
from app.database.repositories.candidate import CandidateRepository
from app.database.repositories.ranking import RankingRepository
from app.database.repositories.explanation import ExplanationRepository
from app.database.repositories.candidate_intelligence import CandidateIntelligenceRepository
from app.database.repositories.candidate_evidence import CandidateEvidenceRepository
from app.database.models.explanation import JobCandidateExplanation
from app.api.v1.routers.dataset import map_entity_to_profile
from app.services.explainability.analyzers import (
    StrengthAnalyzer, WeaknessAnalyzer, TransferableSkillsFinder,
    MissingSkillsEngine, InterviewRecommendationEngine, HiringNarrativeGenerator
)
from app.core.logging.logging import logger

class ExplainabilityAgent(BaseAgent):
    """
    Explainability Agent.
    Transforms raw matching scores, profiles and evidence graphs into recruiter explanation packages.
    """

    def __init__(self):
        self._initialized = False
        self._strengths_analyzer = None
        self._weakness_analyzer = None
        self._transferable_finder = None
        self._missing_engine = None
        self._interview_engine = None
        self._narrative_generator = None

    async def initialize(self) -> None:
        self._initialized = True
        self._strengths_analyzer = StrengthAnalyzer()
        self._weakness_analyzer = WeaknessAnalyzer()
        self._transferable_finder = TransferableSkillsFinder()
        self._missing_engine = MissingSkillsEngine()
        self._interview_engine = InterviewRecommendationEngine()
        self._narrative_generator = HiringNarrativeGenerator()
        logger.info("explainability_agent_initialized")

    async def validate(self, input_data: Any) -> bool:
        if not input_data:
            return False
        if isinstance(input_data, str) and len(input_data.strip()) > 0:
            return True
        if isinstance(input_data, dict) and ("job_id" in input_data or "id" in input_data):
            return True
        return False

    def explain(self) -> str:
        return (
            "ExplainabilityAgent translates quantitative ranking metrics into recruiter decision insights, "
            "highlighting strengths, gaps, transferable capabilities, and custom interview focus areas."
        )

    async def health(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "initialized": self._initialized,
            "components": {
                "strengths_analyzer": "ready",
                "weakness_analyzer": "ready",
                "transferable_finder": "ready",
                "missing_engine": "ready",
                "interview_engine": "ready",
                "narrative_generator": "ready"
            }
        }

    def version(self) -> str:
        return "1.0.0"

    def supported_inputs(self) -> List[str]:
        return ["job_id", "id"]

    def supported_outputs(self) -> List[str]:
        return ["job_id", "explanations", "trace"]

    async def execute(self, input_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes Candidate Explainability pipeline.
        """
        agent_trace = []
        start_cpu = psutil.cpu_percent(interval=None)
        process = psutil.Process(os.getpid())
        start_mem = process.memory_info().rss / (1024 * 1024)
        start_time = time.perf_counter()

        def record_step(step_name: str, status: str = "SUCCESS", details: Any = None):
            agent_trace.append({
                "step": step_name,
                "status": status,
                "details": details,
                "timestamp": time.time()
            })

        # 1. Resolve Job ID
        job_id = None
        if isinstance(input_data, str):
            job_id = input_data
        elif isinstance(input_data, dict):
            job_id = input_data.get("job_id") or input_data.get("id")

        if not job_id:
            raise ValueError("Explainability Agent failed: job_id is required.")

        db = context.get("db")
        if not db:
            raise ValueError("Explainability Agent failed: db is required in context.")

        record_step("Job ID Resolved", details={"job_id": job_id})

        # 2. Fetch Job Candidate Rankings
        ranking_repo = RankingRepository(db)
        ranking_record = await ranking_repo.get_ranking(job_id)
        if not ranking_record or not ranking_record.rankings:
            # Fallback/Lazy ranking invocation if rankings are not generated
            logger.info("lazy_ranking_invocation", job_id=job_id)
            from app.services.agents.ranking_agent import ranking_agent
            await ranking_agent.initialize()
            rank_output = await ranking_agent.execute(job_id, context)
            rankings = rank_output["rankings"]
        else:
            rankings = ranking_record.rankings

        record_step("Rankings Loaded", details={"candidates_count": len(rankings)})

        # 3. Load other repositories
        cand_repo = CandidateRepository(db)
        intel_repo = CandidateIntelligenceRepository(db)
        ev_repo = CandidateEvidenceRepository(db)
        exp_repo = ExplanationRepository(db)

        # 4. Generate Explanations for each ranked candidate
        explanations_list = []
        target_cand_ids = context.get("candidate_ids")

        for rank_item in rankings:
            cid = rank_item["candidate_id"]
            if target_cand_ids and cid not in target_cand_ids:
                continue

            cand = await cand_repo.get_candidate_profile(cid)
            if not cand:
                continue
            
            cand_profile = map_entity_to_profile(cand)
            intel = await intel_repo.get_candidate_intelligence(cid)
            evidence = await ev_repo.get_candidate_evidence(cid)

            # A. Run Strength Analyzer
            strengths = self._strengths_analyzer.analyze(cand_profile, intel, evidence, rank_item)
            
            # B. Run Weakness Analyzer
            weaknesses = self._weakness_analyzer.analyze(cand_profile, intel, evidence, rank_item)

            # C. Run Transferable Skills
            missing_skills = rank_item.get("missing_skills", [])
            cand_skills_list = [s.name for s in cand_profile.skills]
            transferable = self._transferable_finder.find(missing_skills, cand_skills_list)

            # D. Categorize Missing Skills
            missing_categories = self._missing_engine.analyze(missing_skills, transferable)

            # E. Run Interview plan generator
            interview_plan = self._interview_engine.generate(rank_item, strengths, weaknesses)

            # F. Generate Narrative
            narrative = self._narrative_generator.generate(cand_profile, rank_item, strengths, weaknesses)

            # Create explanation package payload
            highlights = []
            if intel:
                highlights = intel.career_intelligence.get("career_progression", {}).get("role_evolution", [])

            explanation_package = {
                "candidate_id": cid,
                "overall_summary": narrative,
                "match_percentage": float(rank_item["overall_score"]),
                "hiring_confidence": float(rank_item["hiring_confidence"]),
                "strengths": strengths,
                "weaknesses": weaknesses,
                "missing_skills": missing_categories,
                "transferable_skills": transferable,
                "career_highlights": highlights,
                "evidence_summary": rank_item.get("evidence_summary", ""),
                "risk_summary": rank_item.get("risk_summary", ""),
                "interview_recommendation": interview_plan.get("interview_focus_areas", []),
                "improvement_suggestions": [m["actionable_suggestion"] for m in missing_categories["nice_to_have_missing"]]
            }

            # Map breakdown from rank scores
            match_breakdown = rank_item.get("scoring_dimensions", {})

            # Compile Audit Trail
            weights_applied = context.get("weights")
            if not weights_applied:
                from app.services.agents.ranking_agent import ranking_agent
                weights_applied = ranking_agent.DEFAULT_WEIGHTS

            audit_trail = {
                "job_id": job_id,
                "candidate_id": cid,
                "overall_score": float(rank_item["overall_score"]),
                "hiring_confidence": float(rank_item["hiring_confidence"]),
                "recommendation": rank_item["recommendation"],
                "weights_applied": weights_applied,
                "penalties_applied": float(match_breakdown.get("risk", {}).get("raw_score", 100.0) - 100.0),
                "evidence_anchors": {
                    "experiences_count": len(cand_profile.experiences),
                    "projects_count": len(cand_profile.projects),
                    "certifications_count": len(cand_profile.certifications),
                    "skills_count": len(cand_profile.skills)
                }
            }

            # Save to Database
            exp_model = JobCandidateExplanation(
                job_id=job_id,
                candidate_id=cid,
                explanation_package=explanation_package,
                match_breakdown=match_breakdown,
                audit_trail=audit_trail,
                trace=agent_trace
            )
            await exp_repo.upsert_explanation(exp_model)
            
            explanations_list.append(explanation_package)

        end_cpu = psutil.cpu_percent(interval=None)
        end_mem = process.memory_info().rss / (1024 * 1024)
        end_time = time.perf_counter()

        details = {
            "duration_sec": float(round(end_time - start_time, 4)),
            "cpu_delta": float(end_cpu - start_cpu),
            "mem_delta_mb": float(round(end_mem - start_mem, 2)),
            "explanations_generated": len(explanations_list)
        }
        
        record_step("Explainability Compiled", details=details)

        # Update context
        context["explanations"] = explanations_list
        context["explainability_trace"] = agent_trace

        return {
            "job_id": job_id,
            "explanations": explanations_list,
            "trace": agent_trace
        }

explainability_agent = ExplainabilityAgent()
# Register automatically with orchestrator
from app.services.agents.orchestrator import orchestrator
orchestrator.register_agent("explainability", explainability_agent)
