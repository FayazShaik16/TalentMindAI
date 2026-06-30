import sys
import os
import argparse
import asyncio
import json

# Fix sys.path to run script from backend folder or scripts folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.agents.orchestrator import orchestrator
from app.services.agents.explainability_agent import explainability_agent  # Import ensures registration
from app.database.session import async_session_factory
from app.database.repositories.job import JobRepository
from app.database.repositories.candidate import CandidateRepository
from app.database.repositories.explanation import ExplanationRepository

async def main():
    parser = argparse.ArgumentParser(description="Explain a candidate's match and score disaggregation.")
    parser.add_argument("--job_id", help="Job Description ID. If omitted, takes the first job in the database.")
    parser.add_argument("--candidate_id", help="Candidate ID to explain. If omitted, explains the top ranked candidate.")
    
    args = parser.parse_args()
    job_id = args.job_id
    candidate_id = args.candidate_id

    async with async_session_factory() as session:
        job_repo = JobRepository(session)
        cand_repo = CandidateRepository(session)
        exp_repo = ExplanationRepository(session)

        # Resolve Job ID
        if not job_id:
            all_jobs = await job_repo.get_all()
            if not all_jobs:
                print("Error: No jobs found in database. Ingest a job first.")
                sys.exit(1)
            job_id = all_jobs[0].id
            print(f"No job ID provided. Defaulting to: '{all_jobs[0].title}' (ID: {job_id})")
        else:
            job = await job_repo.get_by_id(job_id)
            if not job:
                print(f"Error: Job description with ID '{job_id}' not found.")
                sys.exit(1)

        # Run ranking and explainability pipeline lazily to ensure data exists
        print(f"\n[AI Orchestrator] Running Explainability Agent for Job ID: {job_id}...")
        context = {"db": session}
        if candidate_id:
            context["candidate_ids"] = [candidate_id]
            
        await explainability_agent.initialize()
        await orchestrator.execute_pipeline(
            pipeline=["explainability"],
            initial_input=job_id,
            context=context
        )
        await session.commit()

        # Fetch explanations
        exps = await exp_repo.get_all_for_job(job_id)
        if not exps:
            print("Error: No explanations generated.")
            sys.exit(1)

        # Resolve target candidate
        target_exp = None
        if candidate_id:
            for e in exps:
                if e.candidate_id == candidate_id:
                    target_exp = e
                    break
            if not target_exp:
                print(f"Error: Explanation not found for Candidate ID '{candidate_id}' under Job ID '{job_id}'.")
                sys.exit(1)
        else:
            # Default to the candidate with the highest match percentage
            exps_sorted = sorted(exps, key=lambda x: x.explanation_package.get("match_percentage", 0.0), reverse=True)
            target_exp = exps_sorted[0]
            candidate_id = target_exp.candidate_id

        cand_profile = await cand_repo.get_candidate_profile(candidate_id)
        cand_name = f"{cand_profile.first_name} {cand_profile.last_name}" if cand_profile else "Unknown Candidate"

        pkg = target_exp.explanation_package
        breakdown = target_exp.match_breakdown
        audit = target_exp.audit_trail

        print("\n" + "=" * 80)
        print(f"RECRUITER DECISION INTELLIGENCE REPORT: {cand_name} (ID: {candidate_id})")
        print("=" * 80)
        print(f"Overall Match  : {pkg.get('match_percentage', 0.0):.1f}%")
        print(f"Confidence     : {pkg.get('hiring_confidence', 0.0)*100:.0f}%")
        print(f"Recommendation : {audit.get('recommendation', 'Interview')}")
        print("-" * 80)
        print("MATCH NARRATIVE:")
        print(pkg.get("overall_summary", "No summary generated."))
        print("-" * 80)

        print("DISAGGREGATED SCORE BREAKDOWN:")
        dimensions = [
            ("Semantic Match", breakdown.get("semantic", {}).get("normalized_score")),
            ("Career Match", breakdown.get("career", {}).get("normalized_score")),
            ("Skill Match", breakdown.get("skills", {}).get("normalized_score")),
            ("Project Match", breakdown.get("projects", {}).get("normalized_score")),
            ("Leadership", breakdown.get("leadership", {}).get("normalized_score")),
            ("Potential", breakdown.get("potential", {}).get("normalized_score")),
            ("Risk Penalty", breakdown.get("risk", {}).get("penalty_applied", 0.0))
        ]
        for label, val in dimensions:
            if val is not None:
                if "Penalty" in label:
                    print(f"  - {label:<20}: {val:.1f}%")
                else:
                    print(f"  - {label:<20}: {val:.1f}%")
            else:
                print(f"  - {label:<20}: N/A")
        print("-" * 80)

        print("TOP VERIFIED STRENGTHS:")
        for i, s in enumerate(pkg.get("strengths", []), 1):
            print(f"  {i}. [{s.get('category')}] {s.get('name')} (Impact: {s.get('impact')})")
            print(f"     Evidence: {s.get('evidence')}")
        print("-" * 80)

        print("IDENTIFIED GAPS & WEAKNESSES:")
        weaks = pkg.get("weaknesses", [])
        if weaks:
            for i, w in enumerate(weaks, 1):
                print(f"  {i}. [{w.get('category')}] {w.get('name')} (Severity: {w.get('severity')})")
                print(f"     Evidence: {w.get('evidence')}")
        else:
            print("  No major weaknesses or gaps detected.")
        print("-" * 80)

        print("TRANSFERABLE SKILLS DETECTED:")
        trans = pkg.get("transferable_skills", [])
        if trans:
            for t in trans:
                print(f"  - Lacks '{t.get('missing_skill')}' -> Transferable: '{t.get('transferable_skill')}'")
                print(f"    Explanation: {t.get('explanation')}")
        else:
            print("  No direct transferable skills detected for missing tech stack requirements.")
        print("-" * 80)

        print("MISSING SKILLS & LEARNING EFFORT:")
        missing = pkg.get("missing_skills", {})
        for severity in ["critical_missing", "important_missing", "nice_to_have_missing"]:
            items = missing.get(severity, [])
            if items:
                print(f"  {severity.replace('_', ' ').upper()}:")
                for item in items:
                    print(f"    - {item.get('name')} | Est. Effort: {item.get('learning_effort')}")
                    print(f"      Suggestion: {item.get('actionable_suggestion')}")
        print("-" * 80)

        print("INTERVIEW FOCUS RECOMMENDATIONS:")
        focus_areas = pkg.get("interview_recommendation", [])
        if focus_areas:
            for i, area in enumerate(focus_areas, 1):
                print(f"  Focus Area {i}: {area.get('topic')}")
                for q in area.get("questions", []):
                    print(f"    - Q: {q}")
        else:
            print("  No custom interview recommendations generated.")
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
