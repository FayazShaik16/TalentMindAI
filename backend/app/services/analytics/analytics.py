from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, List
import numpy as np

from app.database.models.ranking import JobCandidateRanking
from app.database.models.job import JobDescription
from app.database.models.candidate import Candidate
from app.database.models.explanation import JobCandidateExplanation
from app.database.models.candidate_intelligence import CandidateIntelligence

class AnalyticsEngine:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate_hiring_analytics(self, job_id: str | None = None) -> Dict[str, Any]:
        """
        Generates aggregate candidate matching, distribution, skill, and recommendation analytics.
        """
        # Fetch rankings
        stmt = select(JobCandidateRanking)
        if job_id:
            stmt = stmt.where(JobCandidateRanking.job_id == job_id)
        result = await self.session.execute(stmt)
        rankings_records = result.scalars().all()

        total_candidates = 0
        overall_scores = []
        confidences = []
        recommendations = {"Strong Hire": 0, "Hire": 0, "Interview": 0, "Consider": 0, "Not Recommended": 0}
        missing_skills_freq = {}
        risk_warnings_freq = {}

        for rec in rankings_records:
            for rank_item in rec.rankings:
                total_candidates += 1
                overall_scores.append(float(rank_item.get("overall_score", 0.0)))
                confidences.append(float(rank_item.get("hiring_confidence", 0.0)))
                
                rec_val = rank_item.get("recommendation", "Interview")
                if rec_val in recommendations:
                    recommendations[rec_val] += 1
                else:
                    recommendations["Interview"] += 1
                
                for ms in rank_item.get("missing_skills", []):
                    missing_skills_freq[ms] = missing_skills_freq.get(ms, 0) + 1
                
                risk_summary = rank_item.get("risk_summary", "")
                if risk_summary:
                    risk_warnings_freq[risk_summary] = risk_warnings_freq.get(risk_summary, 0) + 1

        # Fetch candidate profiles for tech, experience, certification and domain distribution
        cand_stmt = select(Candidate)
        cand_result = await self.session.execute(cand_stmt)
        candidates = cand_result.scalars().all()

        experience_dist = {"0-3 years": 0, "3-5 years": 0, "5-8 years": 0, "8+ years": 0}
        tech_freq = {}
        cert_freq = {}
        domain_freq = {}

        for c in candidates:
            # Experience distribution
            years = 0.0
            if c.features:
                years = float(c.features.years_experience)

            if years < 3:
                experience_dist["0-3 years"] += 1
            elif years < 5:
                experience_dist["3-5 years"] += 1
            elif years < 8:
                experience_dist["5-8 years"] += 1
            else:
                experience_dist["8+ years"] += 1

            # Technologies
            if isinstance(c.skills, list):
                for skill in c.skills:
                    sname = skill.name if hasattr(skill, "name") else (skill.get("name") if isinstance(skill, dict) else None)
                    if sname:
                        tech_freq[sname] = tech_freq.get(sname, 0) + 1

            # Certifications
            if isinstance(c.certifications, list):
                for cert in c.certifications:
                    cname = cert.name if hasattr(cert, "name") else (cert.get("name") if isinstance(cert, dict) else None)
                    if cname:
                        cert_freq[cname] = cert_freq.get(cname, 0) + 1

        # Fetch candidate intelligence records for domain distributions
        intel_stmt = select(CandidateIntelligence)
        intel_result = await self.session.execute(intel_stmt)
        intels = intel_result.scalars().all()
        for intel in intels:
            domains = intel.domain_intelligence.get("detected_domains", {}) if intel.domain_intelligence else {}
            for d in domains.keys():
                domain_freq[d] = domain_freq.get(d, 0) + 1

        # Sort frequencies
        top_missing_skills = sorted(missing_skills_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        top_technologies = sorted(tech_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        top_certifications = sorted(cert_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        top_domains = sorted(domain_freq.items(), key=lambda x: x[1], reverse=True)[:10]

        # Calculate percentages for recommendations (funnel)
        funnel_pct = {}
        for k, v in recommendations.items():
            funnel_pct[k] = float(round((v / total_candidates * 100), 1)) if total_candidates > 0 else 0.0

        avg_score = float(round(np.mean(overall_scores), 1)) if overall_scores else 0.0
        avg_confidence = float(round(np.mean(confidences), 3)) if confidences else 0.0

        return {
            "total_evaluated": total_candidates,
            "average_match_score": avg_score,
            "average_hiring_confidence": avg_confidence,
            "hiring_funnel": {
                "counts": recommendations,
                "percentages": funnel_pct
            },
            "top_missing_skills": [{"skill": k, "count": v} for k, v in top_missing_skills],
            "top_technologies": [{"technology": k, "count": v} for k, v in top_technologies],
            "top_certifications": [{"certification": k, "count": v} for k, v in top_certifications],
            "distributions": {
                "experience": experience_dist,
                "domains": [{"domain": k, "count": v} for k, v in top_domains]
            }
        }
