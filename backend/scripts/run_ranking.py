import sys
import os
import argparse
import asyncio
import json

# Fix sys.path to run script from backend folder or scripts folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.agents.orchestrator import orchestrator
from app.services.agents.ranking_agent import ranking_agent  # Import ensures registration
from app.database.session import async_session_factory
from app.database.repositories.job import JobRepository
from app.core.config.config import settings

async def main():
    parser = argparse.ArgumentParser(description="Run the Hybrid Matching & Intelligent Ranking Engine.")
    parser.add_argument("--job_id", help="Job Description ID to rank candidates against. If omitted, takes the first job in the database.")
    parser.add_argument("--candidates", help="Comma-separated list of Candidate IDs to rank. If omitted, ranks all candidates.")
    parser.add_argument("--top_k", type=int, help="Number of top candidates to rerank using Cross-Encoder.")
    
    args = parser.parse_args()
    job_id = args.job_id
    top_k = args.top_k
    
    candidate_ids = None
    if args.candidates:
        candidate_ids = [cid.strip() for cid in args.candidates.split(",") if cid.strip()]

    async with async_session_factory() as session:
        job_repo = JobRepository(session)
        
        # 1. Fetch Job
        if not job_id:
            all_jobs = await job_repo.get_all()
            if not all_jobs:
                print("Error: No jobs found in database. Please ingest a job description first.")
                sys.exit(1)
            job_id = all_jobs[0].id
            print(f"No job ID provided. Defaulting to first job in database: ID '{job_id}' (Title: '{all_jobs[0].title}')\n")
        else:
            job = await job_repo.get_by_id(job_id)
            if not job:
                print(f"Error: Job Description with ID '{job_id}' not found.")
                sys.exit(1)

        print(f"Running Ranking Engine against Job ID: {job_id}")
        print("=" * 70)

        # 2. Run Hybrid Ranking Agent pipeline
        await ranking_agent.initialize()
        context = {
            "db": session,
            "candidate_ids": candidate_ids,
            "top_k_rerank": top_k if top_k is not None else settings.TOP_K_RERANK
        }

        final_output, updated_context, trace = await orchestrator.execute_pipeline(
            pipeline=["hybrid_ranking"],
            initial_input=job_id,
            context=context
        )

        await session.commit()

        print("RANKING PIPELINE EXECUTION TRACE:")
        for step in trace:
            status_icon = "[OK]" if step["status"] == "SUCCESS" else "[FAIL]"
            print(f"  {status_icon} {step['agent_name']} - Status: {step['status']}, Duration: {step['duration_sec']}s, Mem Delta: {step['memory_delta_mb']}MB")
        print("-" * 70)

        print("\nHYBRID RANKING AND RECOMMENDATION RESULTS:")
        rankings = final_output["rankings"]
        for cand in rankings:
            print(f"  Rank {cand['rank']} | ID: {cand['candidate_id']} | {cand['first_name']} {cand['last_name']}")
            print(f"    Overall Score   : {cand['overall_score']}/100 (Hiring Confidence: {cand['hiring_confidence']*100:.0f}%)")
            print(f"    Recommendation  : {cand['recommendation']} (Trust Score: {cand['trust_score']:.1f}/100)")
            print(f"    Summary         : {cand['reasoning_summary']}")
            print(f"    Missing Skills  : {', '.join(cand['missing_skills']) if cand['missing_skills'] else 'None'}")
            print(f"    Recommendation  : {cand['interview_recommendation']}")
            print("    -" * 35)
        print("=" * 70)

        print("\nBENCHMARKING & OBSERVABILITY METRICS:")
        stats = final_output["statistics"]
        print(f"  - Ranking Latency : {stats['ranking_latency_sec']:.4f} seconds")
        print(f"  - CPU Delta       : {stats['cpu_delta_percent']}%")
        print(f"  - Memory Delta    : {stats['memory_delta_mb']} MB")
        print(f"  - Avg Score Time  : {stats['average_score_time_sec']:.4f} seconds per candidate")
        print(f"  - Candidates/Sec  : {stats['candidates_per_second']} cand/sec")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
