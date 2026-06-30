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
    parser = argparse.ArgumentParser(description="Construct and display Candidate Evidence Graph relationships.")
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

        print(f"Building Evidence Graph for Candidate ID: {candidate_id}")
        print("=" * 60)

        # Ensure Agent is loaded
        await evidence_verification_agent.initialize()
        context = {"db": session, "candidate_id": candidate_id}

        final_output, _, _ = await orchestrator.execute_pipeline(
            pipeline=["evidence_verification"],
            initial_input=candidate_id,
            context=context
        )

        graph = final_output["evidence_graph"]
        nodes = graph["nodes"]
        edges = graph["edges"]

        print(f"EVIDENCE RELATIONSHIP GRAPH:")
        print(f"  Total Nodes: {len(nodes)}")
        print(f"  Total Edges: {len(edges)}")
        print("-" * 60)

        print("\nGRAPH NODES BY type:")
        node_types = {}
        for n in nodes:
            node_types[n["type"]] = node_types.get(n["type"], []) + [n["label"]]

        for type_name, labels in node_types.items():
            print(f"  Type: {type_name} ({len(labels)} nodes)")
            for label in labels[:6]:
                print(f"    - {label}")
            if len(labels) > 6:
                print(f"    - ... and {len(labels) - 6} more")
        print("-" * 60)

        print("\nRELATIONSHIP EDGES:")
        edge_types = {}
        for e in edges:
            edge_types[e["type"]] = edge_types.get(e["type"], 0) + 1

        for type_name, count in edge_types.items():
            print(f"  {type_name}: {count} relations")

        print("\nQueryable Relationships List:")
        for edge in edges[:20]:
            src_node = next((n for n in nodes if n["id"] == edge["source"]), None)
            tgt_node = next((n for n in nodes if n["id"] == edge["target"]), None)
            
            src_label = src_node["label"] if src_node else edge["source"]
            tgt_label = tgt_node["label"] if tgt_node else edge["target"]
            
            print(f"  - [{src_label}] --({edge['type']})--> [{tgt_label}]")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
