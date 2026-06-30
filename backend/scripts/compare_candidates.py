import sys
import os
import argparse
import asyncio
import json

# Fix sys.path to run script from backend folder or scripts folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import async_session_factory
from app.database.repositories.job import JobRepository
from app.database.repositories.candidate import CandidateRepository
from app.database.repositories.explanation import ExplanationRepository
from app.services.explainability.comparison import CandidateComparisonEngine, DecisionIntelligenceEngine
from app.services.agents.explainability_agent import explainability_agent
from app.services.agents.orchestrator import orchestrator

async def main():
    parser = argparse.ArgumentParser(description="Compare two or more candidates side-by-side under a job description.")
    parser.add_argument("--job_id", help="Job Description ID. If omitted, takes first job in DB.")
    parser.add_argument("--candidates", required=True, help="Comma-separated list of candidate IDs to compare.")
    parser.add_argument("--output", help="Optional path to output the comparison results as JSON.")

    args = parser.parse_args()
    job_id = args.job_id
    cand_ids = [cid.strip() for cid in args.candidates.split(",") if cid.strip()]

    if len(cand_ids) < 2:
        print("Error: Please provide at least two candidate IDs to compare.")
        sys.exit(1)

    async with async_session_factory() as session:
        job_repo = JobRepository(session)
        cand_repo = CandidateRepository(session)
        exp_repo = ExplanationRepository(session)

        # 1. Resolve Job ID
        if not job_id:
            all_jobs = await job_repo.get_all()
            if not all_jobs:
                print("Error: No jobs in database.")
                sys.exit(1)
            job_id = all_jobs[0].id
            print(f"No Job ID specified. Defaulting to first job: ID '{job_id}' ({all_jobs[0].title})\n")
        else:
            job = await job_repo.get_by_id(job_id)
            if not job:
                print(f"Error: Job description '{job_id}' not found.")
                sys.exit(1)

        # Ensure explanation packages exist for each candidate
        print(f"Ensuring explanation packages are built for job {job_id}...")
        await explainability_agent.initialize()
        context = {"db": session, "candidate_ids": cand_ids}
        await orchestrator.execute_pipeline(
            pipeline=["explainability"],
            initial_input=job_id,
            context=context
        )
        await session.commit()

        # 2. Fetch packages
        packages = []
        for cid in cand_ids:
            exp = await exp_repo.get_explanation(job_id, cid)
            if exp:
                cand_profile = await cand_repo.get_candidate_profile(cid)
                pkg = dict(exp.explanation_package)
                pkg["match_breakdown"] = exp.match_breakdown
                pkg["overall_score"] = exp.audit_trail.get("overall_score", 50.0)
                pkg["recommendation"] = exp.audit_trail.get("recommendation", "Interview")
                pkg["personal_info"] = {"first_name": cand_profile.first_name, "last_name": cand_profile.last_name} if cand_profile else {}
                packages.append(pkg)

        if len(packages) < len(cand_ids):
            print(f"Warning: Only found/generated explanations for {len(packages)} out of {len(cand_ids)} requested candidates.")

        if not packages:
            print("Error: Could not retrieve/generate explanations for any specified candidates.")
            sys.exit(1)

        # 3. Generate side-by-side matrix
        comp_engine = CandidateComparisonEngine()
        comparison_res = comp_engine.compare(packages)
        matrix = comparison_res["comparison_matrix"]

        # 4. Generate decision intelligence
        di_engine = DecisionIntelligenceEngine()
        di_res = None
        if len(packages) >= 2:
            di_res = di_engine.generate_differentiators(packages[0], packages[1])

        # 5. Output comparison results
        print("\n" + "=" * 80)
        print(f"CANDIDATE COMPARISON MATRIX - JOB DESCRIPTION: {job_id}")
        print("=" * 80)
        
        # Headers
        header_row = f"{'Metric':<25}"
        for cid in cand_ids:
            if cid in matrix:
                header_row += f" | {matrix[cid]['name'][:20]:<20}"
        print(header_row)
        print("-" * 80)

        # Base attributes
        rows = [
            ("Overall Score", lambda m: f"{m['overall_score']:.1f}%"),
            ("Hiring Confidence", lambda m: f"{m['hiring_confidence']*100:.0f}%"),
            ("Recommendation", lambda m: m["recommendation"]),
            ("Semantic Match", lambda m: f"{m['scores']['semantic_match']:.1f}%"),
            ("Skills Match", lambda m: f"{m['scores']['skills_match']:.1f}%"),
            ("Career Match", lambda m: f"{m['scores']['career_match']:.1f}%"),
            ("Leadership Match", lambda m: f"{m['scores']['leadership_match']:.1f}%"),
            ("Projects Match", lambda m: f"{m['scores']['projects_match']:.1f}%"),
            ("Potential Match", lambda m: f"{m['scores']['potential_match']:.1f}%"),
            ("Risk Penalty", lambda m: f"{m['scores']['risk_penalty']:.1f}%"),
            ("Key Strengths", lambda m: ", ".join(m["strengths"][:3])),
            ("Identified Gaps", lambda m: ", ".join(m["weaknesses"][:2]) if m["weaknesses"] else "None"),
            ("Missing Skills", lambda m: ", ".join(m["missing_skills"][:3]) if m["missing_skills"] else "None"),
        ]

        for label, extractor in rows:
            line = f"{label:<25}"
            for cid in cand_ids:
                if cid in matrix:
                    line += f" | {extractor(matrix[cid])[:20]:<20}"
            print(line)

        print("-" * 80)

        if di_res:
            print("\nDECISION INTELLIGENCE: RANKING DIFFERENTIATORS")
            print(f"Comparing Candidate A ({matrix[cand_ids[0]]['name']}) vs Candidate B ({matrix[cand_ids[1]]['name']})")
            print(f"Score Gap: {di_res['score_gap']}%")
            print("Primary Reasons:")
            for i, diff in enumerate(di_res["differentiators"], 1):
                print(f"  {i}. {diff}")
        print("=" * 80)

        # 6. Save JSON if output argument provided
        if args.output:
            output_data = {
                "job_id": job_id,
                "comparison": matrix,
                "decision_intelligence": di_res
            }
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2)
            print(f"\nComparison JSON exported to: {os.path.abspath(args.output)}")

if __name__ == "__main__":
    asyncio.run(main())
