import pytest
from app.services.intent_parser import intent_parser
from app.services.skill_classifier import skill_classifier
from app.services.hidden_requirements import hidden_detector
from app.services.job_feature_engineer import job_feature_extractor
from app.services.intent_graph import intent_graph_builder
from app.services.agents.job_agent import job_agent

SAMPLE_JD = (
    "Job Title: Lead AI Engineer\n"
    "Department: Analytics and Machine Learning\n"
    "Location: Bangalore, India (Remote)\n"
    "We are looking for a Lead AI Engineer with 8+ years of experience.\n"
    "You will take ownership of PyTorch machine learning models and scale our cloud services.\n"
    "You will mentor junior engineers and coordinate cross-functional teams.\n"
    "Required Tech: Python, PyTorch, AWS, Kubernetes, Docker, SQL, Git.\n"
    "Salary: $140,000 - $170,000 yearly"
)

@pytest.mark.anyio
async def test_recruiter_intent_parser():
    parsed = await intent_parser.parse(SAMPLE_JD)
    profile = parsed["profile"]
    confidences = parsed["confidence_scores"]
    
    assert profile["title"] == "Lead AI Engineer"
    assert "Analytics" in profile["department"]
    assert profile["seniority"] == "Lead"
    assert profile["experience_required_years"] == 8.0
    assert profile["remote_compatibility"] == "Remote"
    assert "Python" in profile["skills"]["primary_skills"]
    assert "AWS" in profile["skills"]["cloud_platforms"]
    assert "Pytorch" in profile["skills"]["frameworks"]
    assert profile["salary"]["min"] == 140000.0
    assert profile["salary"]["max"] == 170000.0
    
    assert confidences["title"] > 0.8
    assert confidences["experience_required_years"] > 0.8

@pytest.mark.anyio
async def test_skill_classification_engine():
    res = await skill_classifier.classify("python")
    assert res["normalized_name"] == "Python"
    assert res["category"] == "Programming Language"
    assert "AI Ecosystem" in res["hierarchy_path"]

    res_k8s = await skill_classifier.classify("kubernetes")
    assert res_k8s["normalized_name"] == "Kubernetes"
    assert res_k8s["category"] == "DevOps"
    assert "Cloud Infrastructure" in res_k8s["hierarchy_path"]

@pytest.mark.anyio
async def test_hidden_requirement_detector():
    res = await hidden_detector.detect(SAMPLE_JD)
    
    assert "Ownership" in res
    assert "Mentorship" in res
    assert "Scalability" in res
    assert "Leadership" in res
    
    assert res["Ownership"]["confidence_score"] > 0.70
    assert "mentor" in res["Mentorship"]["evidence"].lower()

@pytest.mark.anyio
async def test_job_feature_extractor():
    parsed = await intent_parser.parse(SAMPLE_JD)
    profile = parsed["profile"]
    hidden_reqs = await hidden_detector.detect(SAMPLE_JD)
    
    features = job_feature_extractor.extract_features(profile, hidden_reqs)
    
    assert features["required_experience"] == 8.0
    assert features["preferred_experience"] == 10.0
    assert features["ai_experience"] is True
    assert features["cloud_experience"] is True
    assert features["management_exposure"] is True
    assert features["remote_compatibility"] == "Remote"

@pytest.mark.anyio
async def test_intent_graph_builder():
    parsed = await intent_parser.parse(SAMPLE_JD)
    profile = parsed["profile"]
    hidden_reqs = await hidden_detector.detect(SAMPLE_JD)
    
    graph = intent_graph_builder.build_graph(profile, hidden_reqs)
    
    nodes = {n["id"]: n for n in graph["nodes"]}
    assert "role_0" in nodes
    assert nodes["role_0"]["label"] == "Lead AI Engineer"
    
    # Check that edges exist linking role to experience and industry
    edges = [(e["source"], e["target"], e["relation"]) for e in graph["edges"]]
    assert any(ed[0] == "role_0" and ed[2] == "requires_experience" for ed in edges)
    assert any(ed[2] == "requires_behavior" for ed in edges)

@pytest.mark.anyio
async def test_job_intelligence_agent_execution():
    await job_agent.initialize()
    context = {}
    
    res = await job_agent.execute(SAMPLE_JD, context)
    
    assert res["title"] == "Lead AI Engineer"
    assert len(res["trace"]) > 0
    assert "overall" in res["intent_profile"]["engineered_features"] or "required_experience" in res["intent_profile"]["engineered_features"]
    assert res["job_id"] == context["job_id"]
