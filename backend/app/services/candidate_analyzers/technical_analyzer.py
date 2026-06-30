import re
from datetime import date
from typing import Any, Dict, List, Set, Tuple
from app.schemas.candidate import CandidateProfile, ExperienceDetail, ProjectDetail
from app.services.extractor import parse_date

class TechnicalAnalyzer:
    """
    Analyzes candidate's technical skills and estimates proficiency levels (Beginner, Intermediate, Advanced, Expert)
    based on projects, years of usage, recent usage, career consistency, and tech combinations.
    """

    CATEGORIES = {
        "programming_languages": [
            r"\bpython\b", r"\bjavascript\b", r"\btypescript\b", r"\bjava\b", r"\bgo\b", r"\bgolang\b",
            r"\bc\+\+\b", r"\brust\b", r"\bc#\b", r"\bruby\b", r"\bphp\b", r"\bkotlin\b", r"\bswift\b",
            r"\bscala\b", r"\bbash\b", r"\bshell\b"
        ],
        "frameworks": [
            r"\breact\b", r"\bangular\b", r"\bvue\b", r"\bdjango\b", r"\bflask\b", r"\bfastapi\b",
            r"\bspring\b", r"\brails\b", r"\bexpress\b", r"\bnext\.js\b", r"\bnextjs\b", r"\bnestjs\b",
            r"\blaravel\b", r"\bflutter\b"
        ],
        "cloud_platforms": [
            r"\baws\b", r"\bamazon web services\b", r"\bgcp\b", r"\bgoogle cloud\b", r"\bazure\b",
            r"\bheroku\b", r"\bdigitalocean\b"
        ],
        "devops": [
            r"\bdocker\b", r"\bkubernetes\b", r"\bk8s\b", r"\bterraform\b", r"\bansible\b",
            r"\bjenkins\b", r"\bgitlab ci\b", r"\bgithub actions\b", r"\bhelm\b"
        ],
        "ai_ml": [
            r"\bpytorch\b", r"\btensorflow\b", r"\bscikit-learn\b", r"\bmachine learning\b",
            r"\bartificial intelligence\b", r"\bnlp\b", r"\bcomputer vision\b", r"\bdeep learning\b",
            r"\bllm\b", r"\bllms\b", r"\blangchain\b", r"\bgpt\b", r"\btransformers\b"
        ],
        "blockchain": [
            r"\bethereum\b", r"\bsolidity\b", r"\bweb3\b", r"\bhyperledger\b", r"\bsmart contract\b",
            r"\bblockchain\b", r"\bdapp\b"
        ],
        "cybersecurity": [
            r"\bcryptography\b", r"\bpentest\b", r"\boauth\b", r"\bjwt\b", r"\bfirewalls\b",
            r"\bcybersecurity\b", r"\bpenetration\b", r"\bvulnerability\b", r"\biam\b", r"\bssl\b",
            r"\bsaml\b", r"\bsecurity\b"
        ],
        "frontend": [
            r"\breact\b", r"\bangular\b", r"\bvue\b", r"\bfrontend\b", r"\bhtml\b", r"\bcss\b",
            r"\bsass\b", r"\btailwind\b", r"\bnext\.js\b", r"\bnextjs\b"
        ],
        "backend": [
            r"\bdjango\b", r"\bflask\b", r"\bfastapi\b", r"\bspring\b", r"\bbackend\b",
            r"\bexpress\b", r"\bnode\.js\b", r"\bnodejs\b", r"\bnestjs\b", r"\brails\b"
        ],
        "databases": [
            r"\bpostgresql\b", r"\bmysql\b", r"\bmongodb\b", r"\bredis\b", r"\bsql\b",
            r"\boracle\b", r"\bsqlite\b", r"\bcassandra\b", r"\bdynamodb\b"
        ],
        "distributed_systems": [
            r"\bkafka\b", r"\brabbitmq\b", r"\bgrpc\b", r"\bmicroservices\b", r"\bdistributed systems\b",
            r"\bconsensus\b", r"\bmessage queue\b"
        ],
        "system_design": [
            r"\bsystem design\b", r"\bhigh availability\b", r"\bload balancer\b", r"\bscalability\b"
        ],
        "architecture_experience": [
            r"\bmicroservices\b", r"\bevent-driven\b", r"\barchitecture\b", r"\bclean architecture\b",
            r"\bdesign patterns\b", r"\bmonolithic\b"
        ],
        "open_source": [
            r"\bopen source\b", r"\bgithub\b", r"\bpull request\b", r"\bcontributor\b"
        ],
        "api_development": [
            r"\bapi\b", r"\brest api\b", r"\bgraphql\b", r"\bgrpc\b", r"\bswagger\b", r"\bopenapi\b"
        ],
        "testing": [
            r"\bpytest\b", r"\bunittest\b", r"\bjest\b", r"\bcypress\b", r"\bselenium\b",
            r"\bmocha\b", r"\btdd\b", r"\bbdd\b", r"\btesting\b"
        ],
        "ci_cd": [
            r"\bjenkins\b", r"\bgithub actions\b", r"\bgitlab ci\b", r"\bcircleci\b",
            r"\bci/cd\b", r"\bpipeline\b"
        ],
        "infrastructure": [
            r"\bterraform\b", r"\bansible\b", r"\bcloudformation\b", r"\binfrastructure as code\b",
            r"\biac\b", r"\bbash\b"
        ]
    }

    def _get_exp_months(self, exp: ExperienceDetail) -> int:
        s_date = parse_date(exp.start_date)
        e_date = parse_date(exp.end_date) or date.today()
        if not s_date:
            return 12  # default fallback
        delta = (e_date.year - s_date.year) * 12 + (e_date.month - s_date.month)
        return max(3, delta)

    def analyze(self, profile: CandidateProfile) -> Dict[str, Any]:
        # Collect all unique technologies mentioned
        technologies_in_profile = set()
        for s in profile.skills:
            technologies_in_profile.add(s.normalized_name or s.name)
        for p in profile.projects:
            for t in p.technologies:
                technologies_in_profile.add(t)

        tech_data: Dict[str, Dict[str, Any]] = {}
        for tech in technologies_in_profile:
            tech_clean = tech.strip()
            if not tech_clean:
                continue

            # Check matches in experiences and projects
            tech_pattern = r"\b" + re.escape(tech_clean.lower()) + r"\b"
            
            project_evidence = []
            experience_evidence = []
            years_usage = 0.0
            recent_usage = False
            consistency_count = 0

            # 1. Projects search
            for p in profile.projects:
                p_text = f"{p.name} {p.description or ''} {' '.join(p.technologies)} {' '.join(p.responsibilities)}".lower()
                if re.search(tech_pattern, p_text) or any(tech_clean.lower() == t.strip().lower() for t in p.technologies):
                    project_evidence.append(p.name)
                    dur = (p.duration_months or 6) / 12.0
                    years_usage += dur

            # 2. Experiences search
            for idx, exp in enumerate(profile.experiences):
                exp_text = f"{exp.company_name} {exp.job_title} {exp.description or ''}".lower()
                if re.search(tech_pattern, exp_text):
                    dur_years = self._get_exp_months(exp) / 12.0
                    experience_evidence.append(exp.company_name)
                    years_usage += dur_years
                    consistency_count += 1
                    # Recency: current role or last experience (usually index 0 or len-1 depending on order)
                    if exp.is_current or idx == len(profile.experiences) - 1:
                        recent_usage = True

            # If years_usage is still 0 but they list it in skills, give it a baseline of 0.5 year
            if years_usage == 0.0:
                years_usage = 0.5

            years_usage = round(years_usage, 1)

            # Determine proficiency level
            # Experts: >= 4 years, >= 2 projects, recent usage, used in >= 2 companies/experiences
            if years_usage >= 4.0 and len(project_evidence) >= 2 and recent_usage and consistency_count >= 1:
                level = "Expert"
                score = 0.95
                confidence = 0.94
            elif years_usage >= 2.0 and (len(project_evidence) >= 1 or consistency_count >= 1):
                level = "Advanced"
                score = 0.80
                confidence = 0.88
            elif years_usage >= 1.0 or len(project_evidence) >= 1:
                level = "Intermediate"
                score = 0.60
                confidence = 0.75
            else:
                level = "Beginner"
                score = 0.35
                confidence = 0.60

            # Boost score/confidence based on combinations (e.g. Python + Django/FastAPI, JavaScript + React)
            boost = 0.0
            if tech_clean.lower() == "python" and any(fw in [t.lower() for t in technologies_in_profile] for fw in ["django", "flask", "fastapi"]):
                boost += 0.03
            if tech_clean.lower() in ["javascript", "typescript"] and any(fw in [t.lower() for t in technologies_in_profile] for fw in ["react", "angular", "vue"]):
                boost += 0.03

            confidence = min(0.99, confidence + boost)
            score = min(0.99, score + boost)

            tech_data[tech_clean] = {
                "name": tech_clean,
                "years_of_usage": float(years_usage),
                "proficiency_level": level,
                "score": float(score),
                "confidence_score": float(confidence),
                "recent_usage": bool(recent_usage),
                "projects": project_evidence,
                "companies": experience_evidence,
                "consistency": "High" if consistency_count > 1 else "Medium" if consistency_count == 1 else "Low"
            }

        # 3. Categorize tech items into Technical Intelligence sections
        results: Dict[str, Any] = {}
        for category, patterns in self.CATEGORIES.items():
            results[category] = []
            category_scores = []
            category_confidences = []

            for tech_name, data in tech_data.items():
                matched = False
                for pattern in patterns:
                    if re.search(pattern, tech_name.lower()):
                        matched = True
                        break
                if matched:
                    results[category].append(data)
                    category_scores.append(data["score"])
                    category_confidences.append(data["confidence_score"])

            # Compute category overall proficiency and confidence
            results[category + "_stats"] = {
                "count": len(results[category]),
                "average_score": round(sum(category_scores) / len(category_scores), 2) if category_scores else 0.0,
                "average_confidence": round(sum(category_confidences) / len(category_confidences), 2) if category_confidences else 0.0
            }

        results["all_tech_details"] = tech_data
        return results

technical_analyzer = TechnicalAnalyzer()
