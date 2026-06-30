import re
from collections.abc import Sequence
from app.schemas.candidate import (
    ExperienceDetail, ProjectDetail, EducationDetail,
    SkillDetail, CertificationDetail, EngineeredFeatures
)

class FeatureEngineer:
    def determine_education_level(self, educations: Sequence[EducationDetail]) -> str | None:
        """
        Determines the highest education level achieved by looking at degree text keywords.
        """
        if not educations:
            return "High School / Associate"

        levels = {
            "phd": 4, "ph.d": 4, "doctor": 4, "master": 3, "ms": 3, "m.s": 3, "ma": 3, "m.a": 3, "mba": 3,
            "bachelor": 2, "bs": 2, "ba": 2, "b.s": 2, "b.a": 2, "degree": 1
        }

        max_level_val = 0
        max_level_name = "High School / Associate"

        for edu in educations:
            if not edu.degree:
                continue
            deg_clean = edu.degree.strip().lower()
            for key, val in levels.items():
                if key in deg_clean and val > max_level_val:
                    max_level_val = val
                    if val == 4:
                        max_level_name = "PhD"
                    elif val == 3:
                        max_level_name = "Master"
                    elif val == 2:
                        max_level_name = "Bachelor"
                    elif val == 1:
                        max_level_name = "Degree"

        return max_level_name

    def calculate_domain_score(self, texts: list[str], keywords: list[str]) -> int:
        """
        Scans all text snippets for keywords and returns a capped score between 0 and 5.
        """
        score = 0
        joined_text = " ".join(texts).lower()
        for kw in keywords:
            # Checks for word boundary matches to ensure exact scoring
            if re.search(r"\b" + re.escape(kw.lower()), joined_text):
                score += 1
        return min(5, score)

    def engineer_features(
        self,
        years_exp: float,
        distinct_comps: int,
        avg_tenure: float,
        stability: float,
        experiences: Sequence[ExperienceDetail],
        projects: Sequence[ProjectDetail],
        educations: Sequence[EducationDetail],
        skills: Sequence[SkillDetail],
        certifications: Sequence[CertificationDetail]
    ) -> EngineeredFeatures:
        """
        Assembles all numerical signals, tech counts, and domain scores into EngineeredFeatures.
        """
        # Calculate distinct tech keywords parsed
        tech_set = set()
        for p in projects:
            for t in p.technologies:
                tech_set.add(t.strip().lower())
        for s in skills:
            if s.normalized_name:
                tech_set.add(s.normalized_name.strip().lower())

        # Calculate project domain diversity
        domain_set = set()
        for p in projects:
            if p.domain:
                domain_set.add(p.domain.strip().lower())

        # Compile candidate written corpus
        experience_texts = [f"{e.job_title} {e.description or ''}" for e in experiences]
        project_texts = [f"{p.name} {p.description or ''} {' '.join(p.responsibilities)}" for p in projects]
        skill_texts = [s.name for s in skills]
        all_texts = experience_texts + project_texts + skill_texts

        # Extract domain experience metrics
        leadership_score = self.calculate_domain_score(
            all_texts, ["lead", "principal", "manager", "director", "head", "architect", "staff", "founder", "vp", "chief"]
        )
        cloud_score = self.calculate_domain_score(
            all_texts, ["aws", "gcp", "azure", "cloud", "terraform", "cgroups", "docker", "kubernetes", "infra", "s3", "ec2"]
        )
        ai_score = self.calculate_domain_score(
            all_texts, ["machine learning", "artificial intelligence", "nlp", "vision", "transformers", "llm", "pytorch", "tensorflow", "neural", "keras"]
        )
        blockchain_score = self.calculate_domain_score(
            all_texts, ["blockchain", "ethereum", "smart contract", "solidity", "web3", "cryptography", "hyperledger"]
        )
        cyber_score = self.calculate_domain_score(
            all_texts, ["security", "pentest", "vulnerability", "firewall", "seccomp", "sandbox", "isolation", "cryptography", "exploit"]
        )

        edu_level = self.determine_education_level(educations)

        return EngineeredFeatures(
            years_experience=years_exp,
            distinct_companies=distinct_comps,
            average_tenure=avg_tenure,
            career_stability=stability,
            project_count=len(projects),
            certification_count=len(certifications),
            education_level=edu_level,
            technology_diversity=len(tech_set),
            domain_diversity=len(domain_set),
            leadership_score=leadership_score,
            cloud_score=cloud_score,
            ai_score=ai_score,
            blockchain_score=blockchain_score,
            cybersecurity_score=cyber_score,
        )

feature_engineer = FeatureEngineer()
