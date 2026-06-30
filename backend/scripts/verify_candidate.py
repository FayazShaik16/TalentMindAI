import sys
import os
import argparse
import asyncio

# Fix sys.path to run script from backend folder or scripts folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.agents.orchestrator import orchestrator
from app.services.agents.evidence_agent import evidence_verification_agent  # Import ensures registration
from app.database.session import async_session_factory
from app.database.repositories.candidate import CandidateRepository
from app.database.repositories.candidate_evidence import CandidateEvidenceRepository
from app.database.models.candidate_evidence import CandidateEvidence
from app.api.v1.routers.candidate_intelligence import sanitize_for_json

async def main():
    parser = argparse.ArgumentParser(description="Run the AI Orchestrator to verify candidate skills and CV risk profiles.")
    parser.add_argument("--id", help="Candidate ID to analyze. If omitted, takes the first candidate in database.")
    parser.add_argument("--save", action="store_true", help="Save the resulting verification profile to the database.")

    args = parser.parse_args()
    candidate_id = args.id

    async with async_session_factory() as session:
        cand_repo = CandidateRepository(session)
        
        # 1. Fetch Candidate
        if not candidate_id:
            all_cands = await cand_repo.get_all()
            if not all_cands:
                print("Error: No candidates found in database.")
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

        # 2. Run Evidence verification agent pipeline
        await evidence_verification_agent.initialize()
        context = {"db": session, "candidate_id": candidate_id}

        final_output, updated_context, trace = await orchestrator.execute_pipeline(
            pipeline=["evidence_verification"],
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

        print("\nSKILLS EVIDENCE VERIFICATION MATRIX:")
        for skill, v_data in final_output["skill_verification"].items():
            print(f"  - {skill}: Status: {v_data['status']} | Duration: {v_data['duration_years']} yrs | Projects: {v_data['project_count']} | Score: {v_data['evidence_score']}/100")
            if v_data["contradictions"]:
                print(f"    WARNING Contradictions: {', '.join(v_data['contradictions'])}")
            print(f"    Sources: {', '.join(v_data['evidence_sources'])}")
        print("-" * 60)

        print("\nCANDIDATE POTENTIAL INDEX:")
        p_data = final_output["potential_metrics"]
        print(f"  - Growth Potential      : {p_data['potentials']['growth_potential']*100}%")
        print(f"  - Innovation Capacity   : {p_data['potentials']['innovation_potential']*100}%")
        print(f"  - Adaptability Score    : {p_data['potentials']['adaptability']*100}%")
        print(f"  - Upskilling Velocity   : {p_data['learning_velocity']['technology_adoption_speed']}")
        print(f"  - Continuous Learning   : {p_data['learning_velocity']['continuous_learning_score']*100}%")
        print("-" * 60)

        print("\nCV RISKS & CONTRA-INDICATIONS:")
        r_data = final_output["risk_analysis"]
        print(f"  Risk Severity Level     : {r_data['risk_level']}")
        print(f"  Total Risk Score        : {r_data['risk_score']}/100")
        print("  Flagged Anomaly Explanations:")
        if r_data["explanations"]:
            for explanation in r_data["explanations"]:
                print(f"    - {explanation}")
        else:
            print("    - None detected. CV profile is consistent with industry benchmarks.")
        print("-" * 60)

        print("\nROLE READINESS MATRIX:")
        ready = p_data["role_readiness"]
        for role, confidence in ready.items():
            print(f"  - {role.replace('_', ' ').title()}: Readiness Confidence {confidence*100}%")
        print("=" * 60)

        # 3. Save if requested
        if args.save:
            print("\nSaving verification results to database...")
            clean_output = sanitize_for_json(final_output)
            ev_model = CandidateEvidence(
                candidate_id=clean_output["candidate_id"],
                skill_verification=clean_output["skill_verification"],
                timeline=clean_output["timeline"],
                potential_metrics=clean_output["potential_metrics"],
                risk_analysis=clean_output["risk_analysis"],
                evidence_graph=clean_output["evidence_graph"],
                trace=clean_output["trace"],
                confidence_scores=clean_output["confidence_scores"]
            )
            ev_repo = CandidateEvidenceRepository(session)
            await ev_repo.upsert_candidate_evidence(ev_model)
            await session.commit()
            print("Candidate Evidence Verification saved successfully.")

if __name__ == "__main__":
    asyncio.run(main())
