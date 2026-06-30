import re
from typing import Dict, Any, List, Optional
from app.services.skill_classifier import skill_classifier
from app.core.logging.logging import logger

class RecruiterIntentParser:
    """
    Parses unstructured Job Descriptions into a structured Recruiter Intent Profile.
    Extracts job title, department, seniority, skills categories, salary, location,
    remote types, and calculates evidence-backed confidence scores.
    """

    # Pre-defined catalogs for deterministic extraction
    PROGRAMMING_LANGUAGES = ["python", "javascript", "typescript", "java", "c++", "go", "rust", "ruby", "php", "swift", "kotlin", "scala", "sql", "c#", "bash", "html", "css"]
    CLOUD_PLATFORMS = ["aws", "gcp", "azure", "oracle", "digitalocean", "heroku", "aws cloud", "google cloud", "microsoft azure"]
    TOOLS = ["docker", "kubernetes", "git", "jenkins", "terraform", "ansible", "jira", "confluence", "postman", "prometheus", "grafana", "elk", "maven", "gradle"]
    FRAMEWORKS = ["fastapi", "flask", "django", "react", "angular", "vue", "spring boot", "pytorch", "tensorflow", "scikit-learn", "express", "nestjs", "numpy", "pandas", "spark", "hadoop", "keras"]
    SOFT_SKILLS = ["mentorship", "communication", "collaboration", "leadership", "ownership", "problem solving", "presentation", "teamwork", "adaptability", "critical thinking"]
    CERTIFICATIONS = ["aws certified", "solutions architect", "certified kubernetes administrator", "cka", "pmp", "cissp", "ceh", "scrum master", "csm", "itil"]
    INDUSTRIES = ["technology", "software", "finance", "healthcare", "e-commerce", "retail", "aerospace", "automotive", "telecommunications", "cybersecurity", "education"]

    def _extract_regex_match(self, text: str, patterns: List[str], default: Optional[str] = None) -> tuple[Optional[str], float]:
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip(), 0.90
        return default, 0.0

    def _extract_experience_years(self, text: str) -> tuple[Optional[float], float]:
        # Matches patterns like "5+ years", "3-5 years", "minimum of 8 years", "5 years of experience"
        patterns = [
            r"(\d+)\s*\+?\s*years?\s+(?:of\s+)?experience",
            r"experience\s+(?:of\s+)?(?:at\s+least\s+)?(\d+)\s*years?",
            r"(\d+)\s*(?:to|-)\s*(\d+)\s*years?",
            r"min(?:imum)?\s+(?:of\s+)?(\d+)\s*years?"
        ]
        
        for idx, pattern in enumerate(patterns):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) > 1 and groups[1] is not None:
                    # Range match: take average or max
                    val = float(groups[0])
                    return val, 0.85
                elif groups[0] is not None:
                    val = float(groups[0])
                    return val, 0.85
        return None, 0.0

    def _extract_salary(self, text: str) -> tuple[Optional[Dict[str, Any]], float]:
        # Matches patterns like "$120,000 - $160,000", "$150k-$200k", "120000 - 150000 USD"
        pattern = r"\$?\s*(\d{2,3}),?(\d{3})?\s*(?:k|K)?\s*(?:-|to)\s*\$?\s*(\d{2,3}),?(\d{3})?\s*(?:k|K)?\s*(?:USD|GBP|EUR|INR|yearly|annually|per year)?"
        match = re.search(pattern, text)
        if match:
            # Parse values
            raw_min = match.group(1)
            raw_max = match.group(3)
            # If 'k' or 'K' was used, or if length is short (e.g. 120 - 160)
            multiplier = 1
            if "k" in match.group(0).lower() or len(raw_min) <= 3:
                multiplier = 1000
                
            currency = "USD"
            if "₹" in text or "inr" in text.lower():
                currency = "INR"
            elif "£" in text or "gbp" in text.lower():
                currency = "GBP"
            elif "€" in text or "eur" in text.lower():
                currency = "EUR"

            try:
                min_val = float(raw_min) * multiplier
                max_val = float(raw_max) * multiplier
                return {
                    "currency": currency,
                    "min": min_val,
                    "max": max_val,
                    "period": "yearly"
                }, 0.90
            except ValueError:
                pass
        return None, 0.0

    def _extract_entities_from_catalog(self, text: str, catalog: List[str]) -> List[tuple[str, float]]:
        found = []
        for entity in catalog:
            # Word boundary check for safe matching
            pattern = rf"\b{re.escape(entity)}\b"
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if matches:
                # Confidence score scales with the frequency / presence
                confidence = 0.98 if len(matches) > 1 else 0.95
                # Return normalized title
                found.append((entity, confidence))
        return found

    async def parse(self, job_description: str) -> Dict[str, Any]:
        """
        Main entry point for parsing job descriptions.
        """
        logger.info("parsing_job_description_start")
        
        # 1. Job Title & Department
        # Try to extract the first line as job title if short, or look for keywords
        lines = [line.strip() for line in job_description.split("\n") if line.strip()]
        title = "Software Engineer" # Default
        title_conf = 0.50
        if lines and len(lines[0]) < 80:
            title = lines[0]
            title_conf = 0.85
            
        # Refine title if explicit title header found
        title_match = re.search(r"(?:Job Title|Role|Position):\s*([^\n]+)", job_description, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
            title_conf = 0.99

        # Department
        dept, dept_conf = self._extract_regex_match(
            job_description,
            [r"department:\s*([^\n]+)", r"team:\s*([^\n]+)", r"Engineering", r"Product", r"Sales", r"Marketing", r"Data Science", r"Finance"],
            default="Engineering"
        )

        # Seniority
        seniority, seniority_conf = self._extract_regex_match(
            job_description,
            [r"\bSenior\b", r"\bLead\b", r"\bPrincipal\b", r"\bJunior\b", r"\bStaff\b", r"\bMid-Level\b", r"\bAssociate\b"],
            default="Mid-Level"
        )

        # Employment Type
        emp_type, emp_type_conf = self._extract_regex_match(
            job_description,
            [r"full-time", r"part-time", r"contract", r"internship", r"full time", r"part time"],
            default="Full-time"
        )
        if "-" in emp_type:
            emp_type = emp_type.capitalize()
        else:
            emp_type = emp_type.title()

        # Experience Required
        exp_req, exp_req_conf = self._extract_experience_years(job_description)

        # Education
        education_matches = []
        edu_patterns = [r"\bBachelor's\b", r"\bMaster's\b", r"\bPh\.?D\b", r"\bB\.?S\b", r"\bM\.?S\b", r"\bDegree\b"]
        for pat in edu_patterns:
            match = re.search(pat, job_description, re.IGNORECASE)
            if match:
                education_matches.append(match.group(0).strip())
        
        education = education_matches if education_matches else ["Bachelor's Degree"]
        education_conf = 0.85 if education_matches else 0.50

        # Location & Remote Compatibility
        remote_type, remote_conf = self._extract_regex_match(
            job_description,
            [r"\bRemote\b", r"\bHybrid\b", r"\bOnsite\b", r"\bon-site\b"],
            default="Onsite"
        )
        if remote_type.lower() == "on-site":
            remote_type = "Onsite"
        else:
            remote_type = remote_type.capitalize()

        location, location_conf = self._extract_regex_match(
            job_description,
            [r"Location:\s*([^\n]+)", r"based in\s+([A-Z][a-zA-Z\s,]+)\b"],
            default="Unknown"
        )

        # Salary
        salary, salary_conf = self._extract_salary(job_description)

        # Industry
        industry_list = self._extract_entities_from_catalog(job_description, self.INDUSTRIES)
        industry = industry_list[0][0].title() if industry_list else "Technology"
        industry_conf = industry_list[0][1] if industry_list else 0.50

        # Skills catalogs
        prog_langs = self._extract_entities_from_catalog(job_description, self.PROGRAMMING_LANGUAGES)
        cloud_plats = self._extract_entities_from_catalog(job_description, self.CLOUD_PLATFORMS)
        tools = self._extract_entities_from_catalog(job_description, self.TOOLS)
        frameworks = self._extract_entities_from_catalog(job_description, self.FRAMEWORKS)
        soft_skills = self._extract_entities_from_catalog(job_description, self.SOFT_SKILLS)
        certs = self._extract_entities_from_catalog(job_description, self.CERTIFICATIONS)

        # Group and classify
        all_skills_flat = prog_langs + cloud_plats + tools + frameworks + soft_skills + certs
        
        # Primary skills are Programming Languages, Cloud Platforms, and key Frameworks
        # Secondary skills are Tools, Soft Skills, and Certifications
        primary_skills_list = prog_langs + cloud_plats + frameworks
        secondary_skills_list = tools + soft_skills + certs

        primary_skills = list(set([s[0].title() if s[0].lower() not in ["aws", "gcp", "k8s"] else s[0].upper() for s in primary_skills_list]))
        secondary_skills = list(set([s[0].title() if s[0].lower() not in ["aws", "gcp", "k8s"] else s[0].upper() for s in secondary_skills_list]))

        # Hierarchical classifications
        classified_skills = []
        for skill_name, conf in all_skills_flat:
            classified = await skill_classifier.classify(skill_name)
            classified_skills.append(classified)

        # Compile confidence scores map
        confidence_scores = {
            "title": title_conf,
            "department": dept_conf,
            "seniority": seniority_conf,
            "employment_type": emp_type_conf,
            "experience_required_years": exp_req_conf,
            "education": education_conf,
            "location": location_conf,
            "remote_compatibility": remote_conf,
            "salary": salary_conf,
            "industry": industry_conf
        }

        # Add entity-level confidences
        for entity_name, conf in all_skills_flat:
            confidence_scores[entity_name.title() if entity_name.lower() not in ["aws", "gcp", "k8s"] else entity_name.upper()] = conf

        profile = {
            "title": title,
            "department": dept,
            "seniority": seniority,
            "employment_type": emp_type,
            "experience_required_years": exp_req or 0.0,
            "education": education,
            "skills": {
                "primary_skills": primary_skills,
                "secondary_skills": secondary_skills,
                "programming_languages": [s[0].title() for s in prog_langs],
                "tools": [s[0].title() if s[0].lower() not in ["k8s"] else "Kubernetes" for s in tools],
                "frameworks": [s[0].title() for s in frameworks],
                "cloud_platforms": [s[0].upper() for s in cloud_plats],
                "soft_skills": [s[0].title() for s in soft_skills],
                "certifications": [s[0].title() for s in certs]
            },
            "industry": industry,
            "location": location,
            "remote_compatibility": remote_type,
            "salary": salary,
            "classified_skills": classified_skills
        }

        logger.info("parsing_job_description_complete", title=title, primary_skills_count=len(primary_skills))
        return {
            "profile": profile,
            "confidence_scores": confidence_scores
        }

intent_parser = RecruiterIntentParser()
