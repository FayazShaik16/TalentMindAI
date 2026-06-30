import sys
import os
import argparse
import asyncio

# Fix sys.path to run script from backend folder or scripts folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.providers.ranking.local import LocalRankingProvider
from app.database.session import async_session_factory
from app.database.repositories.job import JobRepository
from app.database.repositories.candidate import CandidateRepository
from app.database.repositories.candidate_intelligence import CandidateIntelligenceRepository
from app.core.config.config import settings

async def main():
    parser = argparse.ArgumentParser(description="Test second-stage Cross-Encoder reranking.")
    parser.add_argument("--job_id", help="Job ID to use as query text.")
    parser.add_argument("--limit", type=int, default=5, help="Limit number of candidate documents to rerank.")
    
    args = parser.parse_args()
    job_id = args.job_id
    limit = args.limit

    async with async_session_factory() as session:
        job_repo = JobRepository(session)
        cand_repo = CandidateRepository(session)
        intel_repo = CandidateIntelligenceRepository(session)

        # 1. Resolve Job ID & query text
        if not job_id:
            all_jobs = await job_repo.get_all()
            if not all_jobs:
                print("Error: No jobs found in database.")
                sys.exit(1)
            job_id = all_jobs[0].id
            job_obj = all_jobs[0]
        else:
            job_obj = await job_repo.get_by_id(job_id)
            if not job_obj:
                print(f"Error: Job ID '{job_id}' not found.")
                sys.exit(1)

        query_text = job_obj.raw_text
        print(f"Reranking against Job ID: {job_id} (Title: '{job_obj.title}')")
        print(f"Query text snippet: {query_text[:150]}...")
        print("=" * 70)

        # 2. Get candidates
        candidates = await cand_repo.get_all()
        if not candidates:
            print("Error: No candidates in database.")
            sys.exit(1)

        documents = []
        for cand in candidates[:limit]:
            intel = await intel_repo.get_candidate_intelligence(cand.id)
            summary = intel.professional_summary if intel else "Dev software engineer."
            documents.append({
                "candidate_id": cand.id,
                "first_name": cand.first_name,
                "last_name": cand.last_name,
                "professional_summary": f"{cand.first_name} {cand.last_name} is a software engineer. Summary: {summary}"
            })

        print(f"Preparing to rerank {len(documents)} candidates...")
        for doc in documents:
            print(f"  - ID: {doc['candidate_id']} | Name: {doc['first_name']} {doc['last_name']}")
        print("-" * 70)

        # 3. Load provider & Rerank
        provider = LocalRankingProvider()
        start_time = asyncio.get_event_loop().time()
        
        reranked = await provider.rerank(query=query_text, documents=documents)
        
        elapsed = asyncio.get_event_loop().time() - start_time
        print(f"\nRERANKED RESULTS (Rerank Latency: {elapsed:.4f} seconds):")
        for i, doc in enumerate(reranked):
            print(f"  Rank {i+1} | ID: {doc['candidate_id']} | {doc['first_name']} {doc['last_name']}")
            print(f"    Cross-Encoder Score: {doc['rerank_score']:.4f}")
            print(f"    Summary Snippet    : {doc['professional_summary'][:120]}...")
            print("    -" * 35)
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
