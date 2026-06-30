from typing import Dict, Any, List

class JobFeatureExtractor:
    """
    Engineers high-fidelity recruiter feature objects from raw job profile details.
    Produces reusable feature objects for matching pipelines.
    """

    def extract_features(
        self,
        profile: Dict[str, Any],
        hidden_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Processes parsed parameters and hidden expectations into boolean/numeric features.
        """
        # Required vs Preferred Experience
        req_exp = float(profile.get("experience_required_years", 0.0))
        # Preferred is usually a bit higher or matches preferred seniority indications
        pref_exp = req_exp + 2.0 if req_exp > 0 else 2.0

        # Skills checklist for scanning
        skills_dict = profile.get("skills", {})
        all_skills = [s.lower() for s in (
            skills_dict.get("primary_skills", []) + 
            skills_dict.get("secondary_skills", []) +
            skills_dict.get("programming_languages", []) +
            skills_dict.get("frameworks", []) +
            skills_dict.get("tools", [])
        )]

        # AI Experience check
        ai_keywords = ["pytorch", "tensorflow", "scikit-learn", "machine learning", "deep learning", "ai", "llm", "nlp", "keras", "transformers"]
        ai_exp = any(kw in all_skills for kw in ai_keywords) or any("ai" in s or "learning" in s for s in all_skills)

        # Cloud Experience check
        cloud_keywords = ["aws", "gcp", "azure", "cloud", "oracle cloud", "digitalocean", "heroku"]
        cloud_exp = any(kw in all_skills for kw in cloud_keywords)

        # Blockchain check
        blockchain_keywords = ["blockchain", "solidity", "ethereum", "web3", "smart contract", "crypto"]
        blockchain_exp = any(kw in all_skills for kw in blockchain_keywords) or any(kw in profile.get("industry", "").lower() for kw in blockchain_keywords)

        # Cybersecurity check
        cyber_keywords = ["cybersecurity", "security", "cissp", "ceh", "cryptography", "penetration testing", "owasp"]
        cyber_exp = any(kw in all_skills for kw in cyber_keywords) or any("security" in s for s in all_skills)

        # Full Stack check
        fe_keywords = ["react", "angular", "vue", "frontend", "javascript", "typescript", "html", "css"]
        be_keywords = ["python", "go", "java", "backend", "fastapi", "django", "spring boot", "node.js"]
        has_fe = any(kw in all_skills for kw in fe_keywords)
        has_be = any(kw in all_skills for kw in be_keywords)
        full_stack = has_fe and has_be

        # Leadership & Management Exposure
        lead_conf = hidden_requirements.get("Leadership", {}).get("confidence_score", 0.0)
        mentor_conf = hidden_requirements.get("Mentorship", {}).get("confidence_score", 0.0)
        
        leadership_required = lead_conf >= 0.60
        management_exposure = lead_conf >= 0.75 or mentor_conf >= 0.70

        # Startup and Enterprise Preferences
        startup_pref = hidden_requirements.get("Startup Experience", {}).get("confidence_score", 0.0) >= 0.60
        enterprise_pref = hidden_requirements.get("Enterprise Experience", {}).get("confidence_score", 0.0) >= 0.60

        # Remote compatibility
        remote_comp = profile.get("remote_compatibility", "Onsite")

        return {
            "required_experience": float(req_exp),
            "preferred_experience": float(pref_exp),
            "leadership_required": bool(leadership_required),
            "ai_experience": bool(ai_exp),
            "cloud_experience": bool(cloud_exp),
            "blockchain_experience": bool(blockchain_exp),
            "cybersecurity_experience": bool(cyber_exp),
            "full_stack_experience": bool(full_stack),
            "management_exposure": bool(management_exposure),
            "startup_preference": bool(startup_pref),
            "enterprise_preference": bool(enterprise_pref),
            "remote_compatibility": str(remote_comp)
        }

job_feature_extractor = JobFeatureExtractor()
