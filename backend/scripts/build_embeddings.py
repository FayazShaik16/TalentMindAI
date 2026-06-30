import sys
import os
import argparse
import asyncio
import time
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config.config import settings
from app.database.session import get_db_session
from app.database.repositories.candidate import CandidateRepository
from app.api.v1.routers.semantic import index_candidate_profile
from app.providers.vector.faiss import FAISSProvider

async def run_build(force: bool = False, resume: bool = True):
    start_time = time.perf_counter()
    print(f"Initializing embedding generation pipeline (force_rebuild={force}, resume={resume})...")
    
    checkpoint_path = os.path.join(settings.VECTOR_INDEX_PATH, "checkpoint.json")
    completed_ids = set()

    if force:
        print("Clearing FAISS collections and embedding cache for clean rebuild...")
        from app.services.embedding_service import embedding_service
        embedding_service.clear_cache()
        provider = FAISSProvider()
        for col in ["summary", "career", "projects", "skills", "education"]:
            await provider.clear_collection(col)
        if os.path.exists(checkpoint_path):
            os.remove(checkpoint_path)
    elif resume and os.path.exists(checkpoint_path):
        try:
            with open(checkpoint_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                completed_ids = set(data.get("completed_ids", []))
                print(f"Resuming from checkpoint. Already completed: {len(completed_ids)} candidates.")
        except Exception as e:
            print(f"Warning: Failed to load checkpoint: {str(e)}")

    async for db in get_db_session():
        repo = CandidateRepository(db)
        candidates = await repo.get_all()
        
        # Filter candidates not completed yet
        todo_candidates = [c for c in candidates if c.id not in completed_ids]
        total_todo = len(todo_candidates)
        total_all = len(candidates)
        print(f"Total candidates in database: {total_all}. Candidates to process: {total_todo}.")
        
        provider = FAISSProvider()
        processed = 0
        failed = 0

        # Memory-efficient batching logic
        batch_size = 20  # Batch size for memory safety
        for i in range(0, total_todo, batch_size):
            batch = todo_candidates[i : i + batch_size]
            print(f"\nProcessing Batch {i//batch_size + 1} ({len(batch)} candidates)...")
            
            for idx, cand in enumerate(batch):
                cand_idx = i + idx + 1
                print(f"  [{cand_idx}/{total_todo}] Processing Candidate ID: {cand.id} ({cand.first_name} {cand.last_name})...")
                
                # Retry logic
                retries = 3
                success = False
                while retries > 0:
                    try:
                        await index_candidate_profile(cand, db, provider)
                        success = True
                        break
                    except Exception as e:
                        retries -= 1
                        print(f"    Warning: Error indexing candidate {cand.id} ({str(e)}). Retries left: {retries}")
                        if retries > 0:
                            await asyncio.sleep(1) # wait before retry

                if success:
                    processed += 1
                    completed_ids.add(cand.id)
                    # Persist checkpoint mapping
                    try:
                        with open(checkpoint_path, "w", encoding="utf-8") as f:
                            json.dump({"completed_ids": list(completed_ids)}, f, indent=2)
                    except Exception as e:
                        pass
                else:
                    failed += 1
                    print(f"    Error: Failed to process Candidate ID: {cand.id} after all retries.")

        await db.commit()
            
    duration = time.perf_counter() - start_time
    print(f"\nSuccess: Completed building embeddings in {duration:.2f} seconds.")
    print(f"  Processed: {processed} candidates successfully.")
    print(f"  Failed: {failed} candidates.")

def main():
    parser = argparse.ArgumentParser(description="Generate and store candidate vector embeddings.")
    parser.add_argument("--force", action="store_true", help="Force regenerate all embeddings and clear index.")
    parser.add_argument("--no-resume", action="store_false", dest="resume", help="Do not resume from checkpoint.")
    args = parser.parse_args()
    
    asyncio.run(run_build(force=args.force, resume=args.resume))

if __name__ == "__main__":
    main()
