import sys
import os
import argparse
import asyncio

# Fix sys.path to run script from backend folder or scripts folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.intent_parser import intent_parser
from app.services.hidden_requirements import hidden_detector
from app.services.job_feature_engineer import job_feature_extractor

async def main():
    parser = argparse.ArgumentParser(description="Analyze a Job Description and extract structured features.")
    parser.add_argument("--file", help="Path to the file containing the raw job description.")
    parser.add_argument("--text", help="Raw job description text directly.")
    
    args = parser.parse_args()
    
    jd_text = ""
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File '{args.file}' not found.")
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            jd_text = f.read()
    elif args.text:
        jd_text = args.text
    else:
        # Fallback default test job description if none provided
        jd_text = (
            "Job Title: Senior Python Developer\n"
            "Department: Core Platform engineering\n"
            "Location: San Francisco, CA (Hybrid)\n"
            "We are looking for a Senior Developer with 5+ years of experience in Python and FastAPI.\n"
            "You will mentor junior engineers and take full end-to-end ownership of backend service design.\n"
            "Required skills: Python, AWS, Docker, Kubernetes, SQL, PyTorch.\n"
            "Preferred: Bachelor's in CS, certifications in AWS are a plus.\n"
        )
        print("No input provided. Running with a default sample Job Description...\n")

    print("Analyzing Job Description...")
    print("=" * 60)
    
    # 1. Parse entities
    parsed = await intent_parser.parse(jd_text)
    profile = parsed["profile"]
    confidence_scores = parsed["confidence_scores"]
    
    # 2. Inferred hidden requirements
    hidden_reqs = await hidden_detector.detect(jd_text)
    
    # 3. Engineer features
    features = job_feature_extractor.extract_features(profile, hidden_reqs)
    
    # Print results
    print(f"TITLE:       {profile['title']} (Confidence: {confidence_scores.get('title', 0.0) * 100}%)")
    print(f"DEPARTMENT:  {profile['department']}")
    print(f"SENIORITY:   {profile['seniority']}")
    print(f"LOCATION:    {profile['location']}")
    print(f"REMOTE TYPE: {profile['remote_compatibility']}")
    print(f"EXPERIENCE:  {profile['experience_required_years']} years required")
    print("-" * 60)
    print("EXTRACTED SKILLS:")
    print(f"  Primary:   {', '.join(profile['skills']['primary_skills'])}")
    print(f"  Secondary: {', '.join(profile['skills']['secondary_skills'])}")
    print(f"  Cloud:     {', '.join(profile['skills']['cloud_platforms'])}")
    print(f"  Frameworks: {', '.join(profile['skills']['frameworks'])}")
    print("-" * 60)
    print("SKILLS CLASSIFICATION (HIERARCHY):")
    for s in profile.get("classified_skills", []):
        print(f"  - {s['normalized_name']}: {' -> '.join(s['hierarchy_path'])}")
    print("-" * 60)
    print("HIDDEN EXPECTATIONS INFERRED:")
    for key, val in hidden_reqs.items():
        print(f"  - {key}: Score {val['confidence_score']*100}%")
        print(f"    Evidence: \"{val['evidence']}\"")
    print("-" * 60)
    print("ENGINEERED JOB FEATURES:")
    for k, v in features.items():
        print(f"  - {k.replace('_', ' ').title()}: {v}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
