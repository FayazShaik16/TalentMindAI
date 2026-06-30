import sys
import os
import argparse
import asyncio
import json

# Fix sys.path to run script from backend folder or scripts folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.agents.orchestrator import orchestrator
from app.services.agents.candidate_agent import candidate_agent  # Import ensures registration
from app.database.session import async_session_factory
from app.database.repositories.candidate import CandidateRepository
from app.database.repositories.candidate_intelligence import CandidateIntelligenceRepository
from app.database.models.candidate_intelligence import CandidateIntelligence
from app.api.v1.routers.candidate_intelligence import sanitize_for_json

async def main():
    parser = argparse.ArgumentParser(description="Analyze a Candidate profile and extract structured career intelligence features.")
    parser.add_argument("--id", help="Candidate ID to analyze. If omitted, takes the first candidate in database.")
    parser.add_argument("--save", action="store_true", help="Save the resulting intelligence profile to the database.")

    args = parser.parse_args()

    candidate_id = args.id

    async with async_session_factory() as session:
        cand_repo = CandidateRepository(session)
        
        # 1. Fetch Candidate
        if not candidate_id:
            all_cands = await cand_repo.get_all()
            if not all_cands:
                print("Error: No candidates found in database. Please load candidates first.")
                sys.exit(1)
            candidate_id = all_cands[0].id
            print(f"No candidate ID provided. Defaulting to first candidate in database: ID '{candidate_id}'\n")
        else:
            cand = await cand_repo.get_candidate_profile(candidate_id)
            if not cand:
                print(f"Error: Candidate with ID '{candidate_id}' not found.")
                sys.exit(1)

        print(f"Analyzing Candidate ID: {candidate_id}")
        print("=" * 60)

        # 2. Run Candidate Agent Pipeline
        await candidate_agent.initialize()
        context = {"db": session, "candidate_id": candidate_id}

        final_output, updated_context, trace = await orchestrator.execute_pipeline(
            pipeline=["candidate_intelligence"],
            initial_input=candidate_id,
            context=context
        )

        print("PIPELINE TRACE SUMMARY:")
        for step in trace:
            status_icon = "[OK]" if step["status"] == "SUCCESS" else "[FAIL]"
            print(f"  {status_icon} {step['agent_name']} - Status: {step['status']}, Duration: {step['duration_sec']}s, Mem Delta: {step['memory_delta_mb']}MB")
        print("-" * 60)

        print("\nAGENT INTERNAL TRACE:")
        for step in final_output["trace"]:
            print(f"  - {step['step']}: {step['status']} ({step.get('details') or ''})")
        print("-" * 60)

        print(f"\nPROFESSIONAL SUMMARY:\n{final_output['professional_summary']}")
        print("-" * 60)

        print("\nSPECIALIZATIONS DETECTED:")
        print(f"  {', '.join(final_output['specializations'])}")
        print("-" * 60)

        print("\nCAREER INTELLIGENCE:")
        c_intel = final_output["career_intelligence"]["career_progression"]
        print(f"  Total Experience: {c_intel['total_years_experience']} years")
        print(f"  Promotions Count: {c_intel['promotions_count']}")
        print(f"  Role Evolution: {' -> '.join(c_intel['role_evolution'])}")
        print("-" * 60)

        print("\nTECHNICAL INTELLIGENCE PROFILE:")
        t_intel = final_output["technical_intelligence"]
        for cat in ["programming_languages", "frameworks", "cloud_platforms", "devops", "ai_ml", "databases"]:
            items = t_intel.get(cat, [])
            if items:
                print(f"  {cat.replace('_', ' ').title()}:")
                for item in items:
                    print(f"    - {item['name']}: {item['proficiency_level']} (Years used: {item['years_of_usage']}, Confidence: {item['confidence_score']*100}%)")
        print("-" * 60)

        print("\nPROJECT RATINGS & SCORE:")
        p_intel = final_output["project_intelligence"]
        print(f"  Average Project Score: {p_intel['average_project_score']}/100")
        for p in p_intel["projects"]:
            print(f"    - {p['project_name']}: Score {p['project_score']}/100, Complexity: {p['complexity']}, Scale: {p['scale']}, Ownership: {p['ownership']}")
        print("-" * 60)

        print("\nLEADERSHIP INFERENCES:")
        l_intel = final_output["leadership_intelligence"]
        print(f"  Overall Leadership Score: {l_intel['overall_leadership_score']}/100")
        for dim in ["team_leadership", "mentoring", "architecture_ownership", "technical_leadership"]:
            d_data = l_intel.get(dim, {})
            print(f"    - {dim.replace('_', ' ').title()}: Exposure: {d_data.get('has_exposure')}, Level: {d_data.get('level')}")
        print("-" * 60)

        print("\nCONFIDENCE SCORE ENGINE MATRIX:")
        for k, v in final_output["confidence_scores"].items():
            print(f"  - {k}: {v*100}%")
        print("=" * 60)

        # 3. Save if requested
        if args.save:
            print("\nSaving analysis results to database...")
            clean_output = sanitize_for_json(final_output)
            intel_model = CandidateIntelligence(
                candidate_id=clean_output["candidate_id"],
                professional_summary=clean_output["professional_summary"],
                career_intelligence=clean_output["career_intelligence"],
                technical_intelligence=clean_output["technical_intelligence"],
                leadership_intelligence=clean_output["leadership_intelligence"],
                project_intelligence=clean_output["project_intelligence"],
                domain_intelligence=clean_output["domain_intelligence"],
                career_growth=clean_output["career_growth"],
                specializations=clean_output["specializations"],
                knowledge_graph=clean_output["knowledge_graph"],
                trace=clean_output["trace"],
                confidence_scores=clean_output["confidence_scores"]
            )
            intel_repo = CandidateIntelligenceRepository(session)
            await intel_repo.upsert_candidate_intelligence(intel_model)
            await session.commit()
            print("Candidate Career Intelligence saved successfully.")

if __name__ == "__main__":
    asyncio.run(main())
