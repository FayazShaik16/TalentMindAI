import sys
import os
import argparse
import asyncio

# Fix sys.path to run script from backend folder or scripts folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.agents.orchestrator import orchestrator
from app.services.agents.evidence_agent import evidence_verification_agent
from app.database.session import async_session_factory
from app.database.repositories.candidate import CandidateRepository

async def main():
    parser = argparse.ArgumentParser(description="Generate and display chronological technology adoption timelines.")
    parser.add_argument("--id", help="Candidate ID. If omitted, takes the first candidate in database.")

    args = parser.parse_args()
    candidate_id = args.id

    async with async_session_factory() as session:
        cand_repo = CandidateRepository(session)
        
        if not candidate_id:
            all_cands = await cand_repo.get_all()
            if not all_cands:
                print("Error: No candidates found in database.")
                sys.exit(1)
            candidate_id = all_cands[0].id
            print(f"No candidate ID provided. Defaulting to first candidate in database: ID '{candidate_id}'\n")

        print(f"Generating Career & Technology Analysis for Candidate ID: {candidate_id}")
        print("=" * 60)

        # Ensure Agent is loaded
        await evidence_verification_agent.initialize()
        context = {"db": session, "candidate_id": candidate_id}

        final_output, _, _ = await orchestrator.execute_pipeline(
            pipeline=["evidence_verification"],
            initial_input=candidate_id,
            context=context
        )

        timeline_data = final_output["timeline"]
        progression = timeline_data["career_progression"]
        chrono_timeline = timeline_data["chronological_tech_timeline"]

        print(f"CAREER TIMELINE ANALYSIS FOR CANDIDATE: {candidate_id}")
        print("-" * 60)
        
        print("CHRONOLOGICAL TECHNOLOGY TIMELINE:")
        for year in sorted(chrono_timeline.keys()):
            techs = ", ".join(chrono_timeline[year])
            print(f"  Year {year} : {techs}")
        print("-" * 60)

        print("\nCAREER PROGRESSION METRICS:")
        print(f"  - Consistency Index       : {progression['career_consistency']}")
        print(f"  - Promotion History Count  : {progression['promotion_history_count']} title updates")
        print(f"  - Career Specialization    : {progression['role_specialization']}")
        print(f"  - Career Resilience        : {progression['career_resilience']}")
        print(f"  - Technology Evolution     : {progression['technology_evolution_acceleration']}")
        print(f"  - Career Stagnation Alert  : {progression['stagnation_detected']}")
        print(f"  - Evolution Trail          : {progression['timeline_analysis']}")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
