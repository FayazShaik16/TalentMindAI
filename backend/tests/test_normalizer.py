import pytest
from app.services.normalizer import skill_normalizer

def test_normalize_standard_aliases():
    """
    Test that standard aliases resolve to their correct normalized names, categories, and paths.
    """
    # Test JS -> Javascript (titled)
    js_norm = skill_normalizer.normalize("JS")
    assert js_norm["normalized_name"] == "Javascript"
    assert js_norm["category"] == "Programming Language"
    assert "Frontend" in js_norm["hierarchy_path"]

    # Test py -> Python
    py_norm = skill_normalizer.normalize("  py  ")
    assert py_norm["normalized_name"] == "Python"
    assert py_norm["category"] == "Programming Language"
    assert "AI / Data Science" in py_norm["hierarchy_path"]

    # Test ml -> Machine Learning
    ml_norm = skill_normalizer.normalize("ml")
    assert ml_norm["normalized_name"] == "Machine Learning"
    assert ml_norm["category"] == "AI / Data Science"

    # Test k8s -> Kubernetes
    k8s_norm = skill_normalizer.normalize("k8s")
    assert k8s_norm["normalized_name"] == "Kubernetes"
    assert k8s_norm["category"] == "DevOps / Infrastructure"

    # Test AWS
    aws_norm = skill_normalizer.normalize("AWS")
    assert aws_norm["normalized_name"] == "AWS"
    assert aws_norm["category"] == "Cloud Platform"

def test_normalize_untracked_skills():
    """
    Test that skills not present in the dictionary resolve gracefully to a fallback 'Other' category.
    """
    untracked = "COBOL"
    norm = skill_normalizer.normalize(untracked)
    assert norm["name"] == untracked
    assert norm["normalized_name"] == untracked
    assert norm["category"] == "Other"
    assert norm["hierarchy_path"] == ["Other", untracked]

def test_case_insensitivity_and_whitespace():
    """
    Test that inputs are normalized regardless of case and surrounding whitespace.
    """
    res1 = skill_normalizer.normalize("   PyThOn   ")
    res2 = skill_normalizer.normalize("python")
    assert res1["normalized_name"] == "Python"
    assert res1["normalized_name"] == res2["normalized_name"]
    assert res1["category"] == res2["category"]
    assert res1["hierarchy_path"] == res2["hierarchy_path"]
