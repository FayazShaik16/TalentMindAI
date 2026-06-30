import sys
import os
import argparse
import asyncio

# Fix sys.path to run script from backend folder or scripts folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.agents.orchestrator import orchestrator
from app.services.agents.candidate_agent import candidate_agent
from app.database.session import async_session_factory
from app.database.repositories.candidate import CandidateRepository

async def main():
    parser = argparse.ArgumentParser(description="Generate and display a Candidate Career Intelligence Executive Summary.")
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

        print(f"Generating Executive Summary for Candidate ID: {candidate_id}")
        print("=" * 60)

        # Ensure Candidate agent is loaded
        await candidate_agent.initialize()
        context = {"db": session, "candidate_id": candidate_id}

        final_output, _, _ = await orchestrator.execute_pipeline(
            pipeline=["candidate_intelligence"],
            initial_input=candidate_id,
            context=context
        )

        c_intel = final_output["career_intelligence"]
        p_intel = final_output["project_intelligence"]
        l_intel = final_output["leadership_intelligence"]
        t_intel = final_output["technical_intelligence"]
        g_intel = final_output["career_growth"]

        # Formatted output
        print(f"EXECUTIVE SUMMARY FOR: {c_intel['career_progression']['role_evolution'][-1] if c_intel['career_progression']['role_evolution'] else 'Candidate'}")
        print("-" * 60)
        print(f"PROFESSIONAL SUMMARY:")
        print(f"  {final_output['professional_summary']}")
        print("\nSPECIALIZATIONS & ROLES:")
        print(f"  {', '.join(final_output['specializations'])}")
        print("\nKEY CAREER METRICS:")
        print(f"  - Total Years of Experience : {c_intel['career_progression']['total_years_experience']} yrs")
        print(f"  - Promotion Rate            : {g_intel.get('promotion_rate', 0.0) * 100}%")
        print(f"  - Growth Velocity Score     : {g_intel.get('growth_velocity', 0.0) * 100}%")
        print(f"  - Stability Index           : {c_intel['career_stability']['stability_score']}%")
        print(f"  - Average Tenure (per role) : {c_intel['career_stability']['average_tenure_years']} yrs")
        print(f"  - Distinct Companies        : {c_intel['career_stability']['distinct_companies_count']}")
        print(f"  - Consulting vs Product     : {c_intel['work_environment']['consulting_vs_product']}")
        print(f"  - Firm Size Profile         : {c_intel['work_environment']['startup_vs_enterprise']}")
        print(f"  - Remote Experience         : {c_intel['geographic_exposure']['remote_experience']} ({c_intel['geographic_exposure']['remote_roles_count']} roles)")
        print(f"  - International Exposure    : {c_intel['geographic_exposure']['international_exposure']}")
        print("\nKEY TECHNICAL STACK EXPOSURE:")
        top_skills = []
        for cat in ["programming_languages", "frameworks", "cloud_platforms", "databases"]:
            for item in t_intel.get(cat, []):
                if item["proficiency_level"] in ["Expert", "Advanced"]:
                    top_skills.append(f"{item['name']} ({item['proficiency_level']})")
        print(f"  - High Proficiency Techs    : {', '.join(top_skills[:8]) if top_skills else 'None registered'}")
        print(f"  - Technical Breadth (Count) : {c_intel['technical_profile']['breadth_count']} unique tech assets")
        print(f"  - Technical Depth Score     : {c_intel['technical_profile']['estimated_depth_score']}/5 (project concentration)")
        print("\nPROJECT METRICS:")
        print(f"  - Evaluated Projects Count  : {len(p_intel['projects'])}")
        print(f"  - Average Project Rating    : {p_intel['average_project_score']}/100")
        print("\nLEADERSHIP METRICS:")
        print(f"  - Team Leadership Exposure  : {l_intel['team_leadership']['level']}")
        print(f"  - Mentoring Exposure        : {l_intel['mentoring']['level']}")
        print(f"  - Architecture Ownership    : {l_intel['architecture_ownership']['level']}")
        print(f"  - Overall Leadership Score  : {l_intel['overall_leadership_score']}/100")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
