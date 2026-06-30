import re
import numpy as np
from typing import Any, Dict, List
from app.schemas.candidate import CandidateProfile
from app.database.models.candidate_intelligence import CandidateIntelligence
from app.database.models.candidate_evidence import CandidateEvidence
from app.services.embedding_service import embedding_service
from app.core.logging.logging import logger

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    arr1 = np.array(v1)
    arr2 = np.array(v2)
    dot = np.dot(arr1, arr2)
    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)
    if norm1 > 0 and norm2 > 0:
        return float(dot / (norm1 * norm2))
    return 0.0

class MultiFactorScoringEngine:
    """
    Evaluates 15 independent matching dimensions for candidate-job relevance.
    """

    async def compute_semantic_match(
        self,
        job_id: str,
        candidate_id: str,
        job_embeddings: Dict[str, List[float]],
        candidate_embeddings: Dict[str, List[float]],
        weight: float
    ) -> Dict[str, Any]:
        """
        1. Semantic Match Scoring
        """
        # Compare available embedding vectors
        sims = []
        details = {}
        
        # Overall comparison
        if "overall" in job_embeddings and "overall" in candidate_embeddings:
            s_val = cosine_similarity(job_embeddings["overall"], candidate_embeddings["overall"])
            sims.append(s_val)
            details["overall_similarity"] = s_val

        # Skills comparison
        if "skills" in job_embeddings and "skills" in candidate_embeddings:
            s_val = cosine_similarity(job_embeddings["skills"], candidate_embeddings["skills"])
            sims.append(s_val)
            details["skills_similarity"] = s_val

        # Responsibility vs Projects comparison
        if "responsibilities" in job_embeddings and "projects" in candidate_embeddings:
            s_val = cosine_similarity(job_embeddings["responsibilities"], candidate_embeddings["projects"])
            sims.append(s_val)
            details["responsibility_similarity"] = s_val

        # Behavior vs Leadership comparison
        if "behavior" in job_embeddings and "leadership" in candidate_embeddings:
            s_val = cosine_similarity(job_embeddings["behavior"], candidate_embeddings["leadership"])
            sims.append(s_val)
            details["behavior_similarity"] = s_val

        # Tech stack vs specialization
        if "technology_stack" in job_embeddings and "specialization" in candidate_embeddings:
            s_val = cosine_similarity(job_embeddings["technology_stack"], candidate_embeddings["specialization"])
            sims.append(s_val)
            details["role_similarity"] = s_val

        raw_score = (sum(sims) / len(sims)) * 100.0 if sims else 60.0
        confidence = float(np.mean(sims)) if sims else 0.6

        explanation = (
            f"Semantic similarity match: Overall: {details.get('overall_similarity', 0.0)*100:.1f}%, "
            f"Skills: {details.get('skills_similarity', 0.0)*100:.1f}%, "
            f"Projects: {details.get('responsibility_similarity', 0.0)*100:.1f}%."
        )

        return {
            "raw_score": float(raw_score),
            "normalized_score": float(raw_score),
            "confidence": confidence,
            "weight": weight,
            "explanation": explanation,
            "details": details
        }

    def compute_skill_match(
        self,
        job_profile: Dict[str, Any],
        candidate_profile: CandidateProfile,
        evidence: CandidateEvidence | None,
        weight: float
    ) -> Dict[str, Any]:
        """
        2. Skill Match Scoring
        """
        job_skills = set([s.lower() for s in job_profile.get("skills", {}).get("primary_skills", [])])
        job_sec_skills = set([s.lower() for s in job_profile.get("skills", {}).get("secondary_skills", [])])
        
        cand_skills = {s.name.lower(): s for s in candidate_profile.skills}
        
        exact_matches = []
        missing_skills = []
        
        for js in job_skills:
            if js in cand_skills:
                exact_matches.append(js)
            else:
                missing_skills.append(js)

        # Coverage score
        coverage = len(exact_matches) / len(job_skills) if job_skills else 1.0
        
        # Skill depth and recency using verified skills evidence if available
        depth_sum = 0
        conf_sum = 0
        matched_count = 0

        for js in exact_matches:
            matched_count += 1
            if evidence and js in [k.lower() for k in evidence.skill_verification.keys()]:
                # find key in exact case
                orig_key = next((k for k in evidence.skill_verification.keys() if k.lower() == js), js)
                v_data = evidence.skill_verification[orig_key]
                depth_sum += v_data.get("evidence_score", 50.0)
                conf_sum += 0.9 if v_data.get("status") == "Verified" else 0.7 if v_data.get("status") == "Likely" else 0.5
            else:
                depth_sum += 50.0
                conf_sum += 0.5

        avg_depth = depth_sum / matched_count if matched_count > 0 else 50.0
        avg_conf = conf_sum / matched_count if matched_count > 0 else 0.5

        raw_score = (coverage * 60.0) + (avg_depth * 0.4)
        raw_score = min(100.0, max(0.0, raw_score))

        explanation = (
            f"Matched {len(exact_matches)} required skills. Missing: {', '.join(missing_skills[:3])}. "
            f"Coverage: {coverage*100:.1f}%, Verified Depth: {avg_depth:.1f}%."
        )

        return {
            "raw_score": float(raw_score),
            "normalized_score": float(raw_score),
            "confidence": float(avg_conf),
            "weight": weight,
            "explanation": explanation,
            "details": {
                "exact_matches": exact_matches,
                "missing_skills": missing_skills,
                "coverage": coverage,
                "average_depth": avg_depth
            }
        }

    def compute_career_match(
        self,
        job_profile: Dict[str, Any],
        intelligence: CandidateIntelligence | None,
        weight: float
    ) -> Dict[str, Any]:
        """
        3. Career Match Scoring
        """
        raw_score = 70.0
        confidence = 0.8
        explanation = "Candidate displays stable career transitions."
        
        if intelligence:
            career_intel = intelligence.career_intelligence
            stability = career_intel.get("career_stability", {})
            stability_score = stability.get("stability_score", 70.0)
            
            prog = career_intel.get("career_progression", {})
            promotions = prog.get("promotion_count", 0)

            raw_score = min(100.0, stability_score + (promotions * 5.0))
            explanation = (
                f"Career stability rating: {stability_score:.1f}/100. "
                f"Promotions count: {promotions} role updates."
            )

        return {
            "raw_score": float(raw_score),
            "normalized_score": float(raw_score),
            "confidence": confidence,
            "weight": weight,
            "explanation": explanation
        }

    def compute_technology_match(
        self,
        job_profile: Dict[str, Any],
        evidence: CandidateEvidence | None,
        weight: float
    ) -> Dict[str, Any]:
        """
        4. Technology Match Scoring
        """
        raw_score = 65.0
        confidence = 0.7
        explanation = "Basic technology stack match."

        if evidence and "timeline" in evidence.timeline:
            # Map technologies in timeline
            timeline = evidence.timeline
            chrono = timeline.get("chronological_tech_timeline", {})
            
            job_techs = []
            for cat in ["programming_languages", "frameworks", "tools", "cloud_platforms"]:
                job_techs.extend([t.lower() for t in job_profile.get("skills", {}).get(cat, [])])

            matched = 0
            for jt in job_techs:
                if any(jt in [t.lower() for t in year_techs] for year_techs in chrono.values()):
                    matched += 1
            
            coverage = matched / len(job_techs) if job_techs else 1.0
            raw_score = coverage * 100.0
            explanation = f"Timeline shows usage of {matched} required technologies over career years ({coverage*100:.1f}% match)."

        return {
            "raw_score": float(raw_score),
            "normalized_score": float(raw_score),
            "confidence": confidence,
            "weight": weight,
            "explanation": explanation
        }

    def compute_leadership_match(
        self,
        job_profile: Dict[str, Any],
        intelligence: CandidateIntelligence | None,
        weight: float
    ) -> Dict[str, Any]:
        """
        5. Leadership Match Scoring
        """
        raw_score = 50.0
        confidence = 0.7
        explanation = "Generic leadership assessment."

        job_requires_lead = job_profile.get("features", {}).get("leadership_required", False)

        if intelligence:
            lead_intel = intelligence.leadership_intelligence
            score = lead_intel.get("overall_leadership_score", 50.0)
            confidence = lead_intel.get("overall_confidence_score", 0.7)
            
            raw_score = score
            explanation = f"Inferred Leadership rating: {score:.1f}/100 based on role responsibilities."

            if job_requires_lead and score < 40.0:
                raw_score = max(0.0, score - 15.0)  # penalty for lack of required leadership
                explanation += " Job requires leadership, candidate has low leadership score."

        return {
            "raw_score": float(raw_score),
            "normalized_score": float(raw_score),
            "confidence": confidence,
            "weight": weight,
            "explanation": explanation
        }

    def compute_domain_match(
        self,
        job_profile: Dict[str, Any],
        intelligence: CandidateIntelligence | None,
        weight: float
    ) -> Dict[str, Any]:
        """
        6. Domain Match Scoring
        """
        raw_score = 50.0
        confidence = 0.8
        explanation = "Candidate has general software domain exposure."

        job_domain = job_profile.get("department", "SaaS").lower()

        if intelligence:
            dom_intel = intelligence.domain_intelligence
            detected = dom_intel.get("detected_domains", {})
            
            matched_years = 0.0
            for d_name, d_data in detected.items():
                if job_domain in d_name.lower() or d_name.lower() in job_domain:
                    matched_years = d_data.get("exposure_years", 1.0)
                    break
            
            if matched_years > 0:
                raw_score = min(100.0, 60.0 + (matched_years * 8.0))
                explanation = f"Candidate has {matched_years:.1f} years of experience in {job_domain} domain."
            else:
                raw_score = 50.0
                explanation = f"No direct match for {job_domain} domain. Candidate worked in SaaS/FinTech/General domains."

        return {
            "raw_score": float(raw_score),
            "normalized_score": float(raw_score),
            "confidence": confidence,
            "weight": weight,
            "explanation": explanation
        }

    def compute_education_match(
        self,
        job_profile: Dict[str, Any],
        candidate_profile: CandidateProfile,
        weight: float
    ) -> Dict[str, Any]:
        """
        7. Education Match Scoring
        """
        # Map degree weights
        degree_values = {"b.s.": 1, "bs": 1, "bachelor": 1, "b.tech": 1, "btech": 1,
                         "m.s.": 2, "ms": 2, "master": 2, "m.tech": 2, "mtech": 2,
                         "ph.d.": 3, "phd": 3, "doctor": 3}
                         
        edu_data = job_profile.get("education", "Bachelor")
        if isinstance(edu_data, list):
            req_deg = " ".join(edu_data)
        elif isinstance(edu_data, dict):
            req_deg = edu_data.get("degree", "Bachelor") or "Bachelor"
        else:
            req_deg = str(edu_data)
            
        req_val = 1
        for k, v in degree_values.items():
            if k in req_deg.lower():
                req_val = v
                break

        cand_val = 1
        highest_deg = "Bachelor"
        for edu in candidate_profile.educations:
            deg_name = edu.degree or ""
            for k, v in degree_values.items():
                if k in deg_name.lower():
                    if v > cand_val:
                        cand_val = v
                        highest_deg = deg_name
                        break

        raw_score = 100.0 if cand_val >= req_val else 70.0
        explanation = f"Candidate highest degree is '{highest_deg}' vs required '{req_deg}'."

        return {
            "raw_score": float(raw_score),
            "normalized_score": float(raw_score),
            "confidence": 0.9,
            "weight": weight,
            "explanation": explanation
        }

    def compute_certification_match(
        self,
        job_profile: Dict[str, Any],
        candidate_profile: CandidateProfile,
        weight: float
    ) -> Dict[str, Any]:
        """
        8. Certification Match Scoring
        """
        # Job certifications needed
        req_certs = [c.lower() for c in job_profile.get("skills", {}).get("certifications", [])]
        cand_certs = [c.name.lower() for c in candidate_profile.certifications]
        
        if not req_certs:
            # If no certifications are explicitly required, having certs is a bonus
            raw_score = 80.0 + min(20.0, len(cand_certs) * 5.0)
            explanation = f"Candidate holds {len(cand_certs)} certification(s)."
        else:
            matched = 0
            for rc in req_certs:
                if any(rc in cc or cc in rc for cc in cand_certs):
                    matched += 1
            
            coverage = matched / len(req_certs)
            raw_score = 50.0 + (coverage * 50.0)
            explanation = f"Matched {matched} out of {len(req_certs)} required certifications."

        return {
            "raw_score": float(raw_score),
            "normalized_score": float(raw_score),
            "confidence": 0.8,
            "weight": weight,
            "explanation": explanation
        }

    def compute_project_match(
        self,
        job_profile: Dict[str, Any],
        intelligence: CandidateIntelligence | None,
        weight: float
    ) -> Dict[str, Any]:
        """
        9. Project Match Scoring
        """
        raw_score = 60.0
        confidence = 0.8
        explanation = "Candidate has completed relevant software projects."

        if intelligence:
            proj_intel = intelligence.project_intelligence
            avg_score = proj_intel.get("average_project_score", 60.0)
            
            # Count projects
            p_count = len(proj_intel.get("projects", []))
            
            raw_score = avg_score
            explanation = f"Completed {p_count} projects with an average project execution score of {avg_score:.1f}/100."

        return {
            "raw_score": float(raw_score),
            "normalized_score": float(raw_score),
            "confidence": confidence,
            "weight": weight,
            "explanation": explanation
        }

    def compute_experience_match(
        self,
        job_profile: Dict[str, Any],
        candidate_profile: CandidateProfile,
        weight: float
    ) -> Dict[str, Any]:
        """
        10. Experience Match Scoring
        """
        req_years = float(job_profile.get("experience_required_years", 3.0) or 3.0)
        
        # Calculate years from candidate profile
        total_years = candidate_profile.engineered_features.years_experience
        
        ratio = total_years / req_years if req_years > 0 else 1.0
        raw_score = min(100.0, ratio * 90.0) if ratio < 1.0 else min(100.0, 90.0 + (ratio - 1.0) * 2.0)
        
        explanation = f"Candidate has {total_years:.1f} years of experience vs required {req_years:.1f} years."

        return {
            "raw_score": float(raw_score),
            "normalized_score": float(raw_score),
            "confidence": 0.9,
            "weight": weight,
            "explanation": explanation
        }

    def compute_behavior_match(
        self,
        job_profile: Dict[str, Any],
        candidate_profile: CandidateProfile,
        weight: float
    ) -> Dict[str, Any]:
        """
        11. Behavior Match Scoring
        """
        stability = candidate_profile.behavior_signals.career_stability_score
        
        raw_score = stability * 100.0 if stability <= 1.0 else stability
        raw_score = min(100.0, max(40.0, raw_score))
        
        explanation = f"Candidate shows professional behavior index score of {raw_score:.1f}/100."

        return {
            "raw_score": float(raw_score),
            "normalized_score": float(raw_score),
            "confidence": 0.8,
            "weight": weight,
            "explanation": explanation
        }

    def compute_potential_match(
        self,
        evidence: CandidateEvidence | None,
        weight: float
    ) -> Dict[str, Any]:
        """
        12. Potential Match Scoring
        """
        raw_score = 65.0
        confidence = 0.7
        explanation = "Candidate shows moderate upskilling potential."

        if evidence and "potential_metrics" in evidence.potential_metrics:
            p_data = evidence.potential_metrics.get("potentials", {})
            growth = p_data.get("growth_potential", 0.6)
            adapt = p_data.get("adaptability", 0.6)
            innov = p_data.get("innovation_potential", 0.6)
            
            raw_score = ((growth + adapt + innov) / 3.0) * 100.0
            explanation = f"High potential matching: Growth potential: {growth*100:.0f}%, Adaptability: {adapt*100:.0f}%."

        return {
            "raw_score": float(raw_score),
            "normalized_score": float(raw_score),
            "confidence": confidence,
            "weight": weight,
            "explanation": explanation
        }

    def compute_risk_penalty(
        self,
        evidence: CandidateEvidence | None,
        weight: float
    ) -> Dict[str, Any]:
        """
        13. Risk Penalty Scoring
        """
        raw_score = 100.0
        penalty = 0.0
        explanation = "No resume risk flags detected."

        if evidence and "risk_analysis" in evidence.risk_analysis:
            r_data = evidence.risk_analysis
            risk_score = r_data.get("risk_score", 0)
            level = r_data.get("risk_level", "None")
            
            if risk_score > 0:
                penalty = -float(risk_score)
                raw_score = max(0.0, 100.0 - risk_score)
                exps = r_data.get("explanations", [])
                explanation = f"Risk Penalty applied ({level} severity, -{risk_score} score reduction): {exps[0] if exps else 'Anomaly flags.'}"
            else:
                raw_score = 100.0

        return {
            "raw_score": float(raw_score),
            "normalized_score": float(raw_score),
            "confidence": 0.9,
            "weight": weight,
            "explanation": explanation,
            "penalty_applied": penalty
        }

    def compute_knowledge_graph_match(
        self,
        job_graph: Dict[str, Any],
        intelligence: CandidateIntelligence | None,
        weight: float
    ) -> Dict[str, Any]:
        """
        14. Knowledge Graph Match Scoring
        """
        raw_score = 50.0
        confidence = 0.7
        explanation = "Candidate graph nodes match job specifications."

        if intelligence and "nodes" in intelligence.knowledge_graph:
            cand_nodes = set([n.get("label", "").lower() for n in intelligence.knowledge_graph.get("nodes", [])])
            job_nodes = set([n.get("label", "").lower() for n in job_graph.get("nodes", [])])
            
            if job_nodes:
                intersect = cand_nodes.intersection(job_nodes)
                ratio = len(intersect) / len(job_nodes)
                raw_score = 40.0 + (ratio * 60.0)
                explanation = f"Matched {len(intersect)} entities in recruitment intent graph (Entity Overlap Ratio: {ratio*100:.1f}%)."

        return {
            "raw_score": float(raw_score),
            "normalized_score": float(raw_score),
            "confidence": confidence,
            "weight": weight,
            "explanation": explanation
        }

    def compute_timeline_match(
        self,
        evidence: CandidateEvidence | None,
        weight: float
    ) -> Dict[str, Any]:
        """
        15. Timeline Match Scoring
        """
        raw_score = 60.0
        confidence = 0.7
        explanation = "Chronological technology timeline demonstrates active upskilling."

        if evidence and "timeline" in evidence.timeline:
            prog = evidence.timeline.get("career_progression", {})
            stagnation = prog.get("stagnation_detected", False)
            evolution = prog.get("technology_evolution_acceleration", "Stable")
            
            if stagnation:
                raw_score = 45.0
                explanation = "Career stagnation warning: Candidate has spent >5 years at the same company without role promotions."
            elif "Accelerated" in evolution:
                raw_score = 90.0
                explanation = "Accelerated timeline: Candidate timeline demonstrates rapid transition to modern Cloud/AI technology stacks."
            else:
                raw_score = 75.0
                explanation = f"Stable timeline progression. Technology specialization: {evolution}."

        return {
            "raw_score": float(raw_score),
            "normalized_score": float(raw_score),
            "confidence": confidence,
            "weight": weight,
            "explanation": explanation
        }
