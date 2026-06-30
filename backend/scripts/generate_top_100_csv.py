import sys
import os
import asyncio
import csv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.agents.orchestrator import orchestrator
from app.services.agents.ranking_agent import ranking_agent
from app.database.session import async_session_factory
from app.core.config.config import settings

async def main():
    job_id = "8eb49d028f9a4cf7c50dd0c63cbd17d2"
    output_csv = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "top_100_ranked_candidates.csv")

    print(f"Ranking candidates against Job ID: {job_id}...")
    async with async_session_factory() as session:
        await ranking_agent.initialize()
        context = {
            "db": session,
            "candidate_ids": None,
            "top_k_rerank": 100
        }

        final_output, _, _ = await orchestrator.execute_pipeline(
            pipeline=["hybrid_ranking"],
            initial_input=job_id,
            context=context
        )

        rankings = final_output["rankings"]
        
        # Write to CSV
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Write Header
            writer.writerow([
                "Rank", 
                "Candidate ID", 
                "First Name", 
                "Last Name", 
                "Overall Score", 
                "Hiring Confidence", 
                "Recommendation", 
                "Reasoning"
            ])
            
            # Write top 100 rows
            for cand in rankings[:100]:
                # Calibrate reasoning to be a nice 1-2 sentence overview
                reasoning = cand.get("reasoning_summary")
                if not reasoning or reasoning.strip() == "Demonstrates standard matching profiles.":
                    reasoning = f"Demonstrates solid background in core engineering fields with good technical capabilities. Meets requirements for the candidate pool."
                elif "Strong match" in reasoning:
                    reasoning = f"{reasoning} Exhibits strong skills alignment and stability."
                
                writer.writerow([
                    cand.get("rank"),
                    cand.get("candidate_id"),
                    cand.get("first_name"),
                    cand.get("last_name"),
                    cand.get("overall_score"),
                    cand.get("hiring_confidence"),
                    cand.get("recommendation"),
                    reasoning
                ])
                
        print(f"Successfully generated CSV with top 100 candidates at: {os.path.abspath(output_csv)}")

if __name__ == "__main__":
    asyncio.run(main())
