import sys
import os
import json
import argparse
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.search_engine import search_engine

async def run_search(query: str, collection: str, limit: int, filters_str: str | None):
    filters = None
    if filters_str:
        try:
            filters = json.loads(filters_str)
        except Exception as e:
            print(f"Error parsing filters JSON: {str(e)}")
            sys.exit(1)
            
    print(f"Searching collection '{collection}' for: '{query}'")
    if filters:
        print(f"Applying filters: {filters}")
        
    res = await search_engine.search(
        query=query,
        collection_name=collection,
        limit=limit,
        filter_metadata=filters
    )
    
    candidates = res["results"]
    trace = res["trace"]
    
    print("\n=== Similarity Query Trace ===")
    print(f"Active Model: {trace['embedding_model']}")
    print(f"Vector Metric: {trace['vector_search_metric']}")
    print(f"Embedding Gen Duration: {trace['timing_logs']['embedding_generation_sec']}s")
    print(f"Index Scan Duration: {trace['timing_logs']['vector_lookup_sec']}s")
    print(f"Total Execution Duration: {trace['timing_logs']['total_execution_sec']}s")
    print("\nExecution Steps:")
    for idx, step in enumerate(trace["execution_steps"]):
        print(f"  {idx+1}. {step}")
        
    print("\n=== Candidate Search Results ===")
    if not candidates:
        print("No candidates found matching the query/filter parameters.")
        return
        
    # Table header
    print(f"{'Rank':<5} | {'Candidate ID':<15} | {'Name':<20} | {'Location':<15} | {'Exp':<5} | {'Score':<8}")
    print("-" * 80)
    for rank, item in enumerate(candidates, 1):
        payload = item["payload"]
        name = f"{payload.get('first_name', '')} {payload.get('last_name', '')}"
        location = payload.get("location") or "Unknown"
        exp = payload.get("years_experience") or 0.0
        score = item["score"]
        print(f"{rank:<5} | {item['candidate_id']:<15} | {name:<20} | {location:<15} | {exp:<5} | {score:<8.4f}")

def main():
    parser = argparse.ArgumentParser(description="Query candidates semantically from the vector store.")
    parser.add_argument("--query", required=True, help="Semantic search query.")
    parser.add_argument("--collection", default="summary", help="Vector collection: summary, career, projects, skills, education.")
    parser.add_argument("--limit", type=int, default=10, help="Retrieval limit count.")
    parser.add_argument("--filter", help="JSON string representing metadata filters (e.g. '{\"location\": \"Boston\", \"years_experience\": 3.0}').")
    args = parser.parse_args()
    
    asyncio.run(run_search(args.query, args.collection, args.limit, args.filter))

if __name__ == "__main__":
    main()
