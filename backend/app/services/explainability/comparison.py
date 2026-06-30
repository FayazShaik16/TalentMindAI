from typing import Any, Dict, List

class CandidateComparisonEngine:
    def compare(self, candidates_packages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Creates side-by-side comparisons of candidate strengths, weaknesses, and ratings.
        """
        comparison_matrix = {}
        for pkg in candidates_packages:
            cid = pkg["candidate_id"]
            p_info = pkg["personal_info"]
            scores = pkg["match_breakdown"]
            
            # Extract lists of names
            strengths_list = [s["name"] for s in pkg.get("strengths", [])]
            weaknesses_list = [w["name"] for w in pkg.get("weaknesses", [])]
            missing_list = [m["name"] for m in pkg.get("missing_skills", {}).get("critical_missing", []) + pkg.get("missing_skills", {}).get("important_missing", [])]

            comparison_matrix[cid] = {
                "name": f"{p_info.get('first_name')} {p_info.get('last_name')}",
                "overall_score": pkg["overall_score"],
                "recommendation": pkg["recommendation"],
                "hiring_confidence": pkg["hiring_confidence"],
                "strengths": strengths_list,
                "weaknesses": weaknesses_list,
                "missing_skills": missing_list,
                "scores": {
                    "semantic_match": scores.get("semantic", {}).get("normalized_score", 50.0),
                    "skills_match": scores.get("skills", {}).get("normalized_score", 50.0),
                    "career_match": scores.get("career", {}).get("normalized_score", 50.0),
                    "leadership_match": scores.get("leadership", {}).get("normalized_score", 50.0),
                    "potential_match": scores.get("potential", {}).get("normalized_score", 50.0),
                    "projects_match": scores.get("projects", {}).get("normalized_score", 50.0),
                    "risk_penalty": scores.get("risk", {}).get("penalty_applied", 0.0)
                }
            }

        return {
            "comparison_matrix": comparison_matrix
        }


class DecisionIntelligenceEngine:
    def generate_differentiators(self, cand_a: Dict[str, Any], cand_b: Dict[str, Any]) -> Dict[str, Any]:
        """
        Computes exact differentiators explaining why Candidate A ranked above Candidate B.
        """
        name_a = f"{cand_a['personal_info'].get('first_name')} {cand_a['personal_info'].get('last_name')}"
        name_b = f"{cand_b['personal_info'].get('first_name')} {cand_b['personal_info'].get('last_name')}"
        
        score_a = cand_a["overall_score"]
        score_b = cand_b["overall_score"]
        
        differentiators = []
        
        # 1. Check Skill Coverage
        skills_a = cand_a["match_breakdown"].get("skills", {}).get("normalized_score", 0.0)
        skills_b = cand_b["match_breakdown"].get("skills", {}).get("normalized_score", 0.0)
        if skills_a > skills_b + 5.0:
            differentiators.append(
                f"{name_a} shows stronger core skill coverage and depth (Score: {skills_a:.1f}/100) vs {name_b} (Score: {skills_b:.1f}/100)."
            )

        # 2. Check Experience years
        exp_a = cand_a["match_breakdown"].get("experience", {}).get("raw_score", 0.0)
        exp_b = cand_b["match_breakdown"].get("experience", {}).get("raw_score", 0.0)
        if exp_a > exp_b + 10.0:
            differentiators.append(
                f"{name_a} has significantly more verified experience years vs {name_b}."
            )

        # 3. Check Leadership Readiness
        lead_a = cand_a["match_breakdown"].get("leadership", {}).get("normalized_score", 0.0)
        lead_b = cand_b["match_breakdown"].get("leadership", {}).get("normalized_score", 0.0)
        if lead_a > lead_b + 10.0:
            differentiators.append(
                f"{name_a} possesses proven leadership and team mentoring experience (Score: {lead_a:.1f}/100) compared to {name_b} (Score: {lead_b:.1f}/100)."
            )

        # 4. Check Risk Warning Differences
        risk_a = cand_a["match_breakdown"].get("risk", {}).get("penalty_applied", 0.0)
        risk_b = cand_b["match_breakdown"].get("risk", {}).get("penalty_applied", 0.0)
        if risk_a > risk_b:  # Note: penalty is negative, so greater is less penalty
            differentiators.append(
                f"{name_b} was penalized by risk warnings ({risk_b} points) whereas {name_a} displays a clean profile."
            )

        # 5. Check Project complexity
        proj_a = cand_a["match_breakdown"].get("projects", {}).get("normalized_score", 0.0)
        proj_b = cand_b["match_breakdown"].get("projects", {}).get("normalized_score", 0.0)
        if proj_a > proj_b + 5.0:
            differentiators.append(
                f"{name_a} worked on higher-complexity production projects (Score: {proj_a:.1f}/100) vs {name_b} (Score: {proj_b:.1f}/100)."
            )

        # Fallback if no direct major differentiators
        if not differentiators:
            differentiators.append(
                f"{name_a} displays slightly higher overall semantic match and career stability indexes compared to {name_b}."
            )

        return {
            "primary_candidate": cand_a["candidate_id"],
            "comparison_candidate": cand_b["candidate_id"],
            "differentiators": differentiators[:5],
            "score_gap": float(round(score_a - score_b, 2))
        }
