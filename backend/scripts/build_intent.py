import sys
import os
import argparse
import asyncio
import json

# Fix sys.path to run script from backend folder or scripts folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.agents.orchestrator import orchestrator
from app.services.agents.job_agent import job_agent  # Import ensures registration
from app.database.session import async_session_factory
from app.database.repositories.job import JobRepository
from app.database.models.job import JobDescription

async def main():
    parser = argparse.ArgumentParser(description="Run the AI Orchestrator to build structured Recruiter Intent Profile and Intent Graph.")
    parser.add_argument("--file", help="Path to the file containing the raw job description.")
    parser.add_argument("--save", action="store_true", help="Save the resulting profile to the database.")
    
    args = parser.parse_args()
    
    jd_text = ""
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File '{args.file}' not found.")
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            jd_text = f.read()
    else:
        # Default test job description
        jd_text = (
            "Job Title: Senior Software Engineer (AI & DevOps)\n"
            "Department: AI Platforms Team\n"
            "Location: Bangalore, India (Remote)\n"
            "Salary: $150,000 - $180,000 USD\n"
            "We are seeking a senior engineer with 6+ years of experience in modern python applications.\n"
            "You will take complete ownership of building container orchestration infrastructure using Kubernetes.\n"
            "Responsibilities include mentoring other engineers, designing distributed systems for scalability, and collaborating across product lines.\n"
            "Key tech stack: Python, Kubernetes, PyTorch, AWS, Docker, Git, Terraform.\n"
        )
        print("No input file provided. Running with a default sample Job Description...\n")

    print("Running AI Orchestrator Pipeline...")
    print("=" * 60)

    # Initialize the agent
    await job_agent.initialize()
    
    context = {"job_id": "cli_test_job_id"}
    
    # Execute through orchestrator
    final_output, updated_context, trace = await orchestrator.execute_pipeline(
        pipeline=["job_intelligence"],
        initial_input=jd_text,
        context=context
    )

    print("PIPELINE TRACE SUMMARY:")
    for step in trace:
        status_icon = "[OK]" if step["status"] == "SUCCESS" else "[FAIL]"
        print(f"  {status_icon} {step['agent_name']} - Status: {step['status']}, Duration: {step['duration_sec']}s, Mem Delta: {step['memory_delta_mb']}MB")
    print("-" * 60)

    print("\nAGENT INTERNAL TRACE STEPS:")
    for step in final_output["trace"]:
        print(f"  - {step['step']}: {step['status']} ({step.get('details') or ''})")
    print("-" * 60)

    print("\nCONFIDENCE SCORES:")
    for key, score in final_output["confidence_scores"].items():
        print(f"  - {key}: {score*100}%")
    print("-" * 60)

    print("\nINTENT GRAPH SUMMARY:")
    graph = final_output["intent_graph"]
    print(f"  Total Nodes: {len(graph['nodes'])}")
    print(f"  Total Edges: {len(graph['edges'])}")
    print("\nSample Edges:")
    for edge in graph["edges"][:5]:
        print(f"  - [{edge['source']}] --({edge['relation']})--> [{edge['target']}]")
    print("-" * 60)

    if args.save:
        print("\nSaving analysis results to database...")
        async with async_session_factory() as session:
            try:
                repo = JobRepository(session)
                job_model = JobDescription(
                    id=final_output["job_id"],
                    raw_text=final_output["raw_text"],
                    title=final_output["title"],
                    department=final_output["department"],
                    seniority=final_output["seniority"],
                    experience_required=final_output["experience_required"],
                    employment_type=final_output["employment_type"],
                    remote_type=final_output["remote_type"],
                    intent_profile=final_output["intent_profile"],
                    intent_graph=final_output["intent_graph"],
                    trace=trace,
                    confidence_scores=final_output["confidence_scores"]
                )
                await repo.upsert_job_description(job_model)
                await session.commit()
                print(f"Successfully saved Job ID: {final_output['job_id']}")
            except Exception as e:
                print(f"Database save failed: {str(e)}")
                await session.rollback()

if __name__ == "__main__":
    asyncio.run(main())
