import pytest
from app.services.feature_engineer import feature_engineer
from app.schemas.candidate import (
    ExperienceDetail, ProjectDetail, EducationDetail, SkillDetail, CertificationDetail
)

def test_determine_education_level():
    """
    Test that the highest education level is correctly determined from degree keywords.
    """
    # Empty
    assert feature_engineer.determine_education_level([]) == "High School / Associate"

    # Bachelor
    edu_bach = [EducationDetail(institution="Uni A", degree="Bachelor of Science", field_of_study="CS")]
    assert feature_engineer.determine_education_level(edu_bach) == "Bachelor"

    # Master overrides Bachelor
    edu_master = [
        EducationDetail(institution="Uni A", degree="Bachelor of Science", field_of_study="CS"),
        EducationDetail(institution="Uni B", degree="M.S. in Computer Science", field_of_study="CS")
    ]
    assert feature_engineer.determine_education_level(edu_master) == "Master"

    # PhD overrides Master
    edu_phd = [
        EducationDetail(institution="Uni B", degree="Master of Science", field_of_study="CS"),
        EducationDetail(institution="Uni C", degree="Doctor of Philosophy", field_of_study="CS")
    ]
    assert feature_engineer.determine_education_level(edu_phd) == "PhD"

def test_calculate_domain_score():
    """
    Test that domain scores are correctly extracted from texts based on keywords and capped at 5.
    """
    texts = ["I am a Senior Lead developer and manager.", "Experienced with cloud infrastructure and AWS."]
    
    # 2 matches: "lead", "manager" -> 2
    score = feature_engineer.calculate_domain_score(texts, ["lead", "manager", "chief"])
    assert score == 2

    # Capped at 5
    score_cap = feature_engineer.calculate_domain_score(
        ["lead principal manager director head architect vp chief"],
        ["lead", "principal", "manager", "director", "head", "architect", "vp", "chief"]
    )
    assert score_cap == 5

def test_engineer_features():
    """
    Test that candidate profiles map to full engineered features correctly.
    """
    experiences = [
        ExperienceDetail(company_name="Google", job_title="Staff AI Engineer", start_date="2020-01-01", description="Lead team on LLM and transformers")
    ]
    projects = [
        ProjectDetail(name="Project X", description="AWS backend service", technologies=["Python", "Docker"])
    ]
    skills = [
        SkillDetail(name="py", normalized_name="Python", category="Programming Language")
    ]
    educations = [
        EducationDetail(institution="Stanford", degree="PhD in AI")
    ]
    certifications = [
        CertificationDetail(name="AWS Solutions Architect")
    ]

    features = feature_engineer.engineer_features(
        years_exp=5.5,
        distinct_comps=1,
        avg_tenure=5.5,
        stability=100.0,
        experiences=experiences,
        projects=projects,
        educations=educations,
        skills=skills,
        certifications=certifications
    )

    assert features.years_experience == 5.5
    assert features.distinct_companies == 1
    assert features.average_tenure == 5.5
    assert features.career_stability == 100.0
    assert features.project_count == 1
    assert features.certification_count == 1
    assert features.education_level == "PhD"
    
    # Technology diversity should combine project technologies and skill normalized names
    # Project: Python, Docker; Skills: Python -> Python, Docker -> count 2
    assert features.technology_diversity == 2
    
    # Scores checking
    assert features.leadership_score > 0  # "Staff", "Lead"
    assert features.cloud_score > 0       # "AWS", "Docker"
    assert features.ai_score > 0          # "AI", "LLM", "transformers"
