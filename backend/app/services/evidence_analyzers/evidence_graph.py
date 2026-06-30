from typing import Any, Dict, List
from app.schemas.candidate import CandidateProfile

class EvidenceGraphBuilder:
    """
    Constructs the Evidence Graph showing links:
    Candidate -> Evidence -> Projects -> Experience -> Technologies -> Leadership -> Certifications -> Timeline.
    """

    def build_graph(
        self,
        profile: CandidateProfile,
        skills_verification: Dict[str, Any],
        timeline: Dict[int, List[str]],
        potentials: Dict[str, Any],
        risks: Dict[str, Any]
    ) -> Dict[str, Any]:
        nodes = []
        edges = []

        cand_id = profile.id
        cand_name = f"{profile.personal_info.first_name} {profile.personal_info.last_name}"

        # 1. Candidate Node (Root)
        nodes.append({
            "id": cand_id,
            "type": "Candidate",
            "label": cand_name
        })

        # 2. Evidence anchor node
        evidence_anchor_id = f"ev_anchor_{cand_id}"
        nodes.append({
            "id": evidence_anchor_id,
            "type": "Evidence",
            "label": f"Verification Report (Score: {potentials['potentials']['growth_potential']*100}%, Risk: {risks['risk_level']})"
        })
        edges.append({
            "source": cand_id,
            "target": evidence_anchor_id,
            "type": "HAS_EVIDENCE_RECORD"
        })

        # 3. Verified Skills
        for skill_name, ver in skills_verification.items():
            skill_node_id = f"v_skill_{skill_name.replace(' ', '_')}"
            nodes.append({
                "id": skill_node_id,
                "type": "VerifiedSkill",
                "label": f"{skill_name} ({ver['status']} - {ver['evidence_score']}%)"
            })
            edges.append({
                "source": evidence_anchor_id,
                "target": skill_node_id,
                "type": "VERIFIES_SKILL"
            })

            # Link verified skill to candidate as well
            edges.append({
                "source": cand_id,
                "target": skill_node_id,
                "type": "HAS_VERIFIED_SKILL"
            })

        # 4. Timeline (Years and Techs)
        for year, techs in timeline.items():
            year_node_id = f"year_{year}"
            nodes.append({
                "id": year_node_id,
                "type": "TimelineYear",
                "label": f"Active Year {year}"
            })
            edges.append({
                "source": cand_id,
                "target": year_node_id,
                "type": "ACTIVE_IN_YEAR"
            })

            for t in techs:
                tech_node_id = f"tech_{t.replace(' ', '_')}"
                if not any(n["id"] == tech_node_id for n in nodes):
                    nodes.append({
                        "id": tech_node_id,
                        "type": "Technology",
                        "label": t
                    })
                edges.append({
                    "source": year_node_id,
                    "target": tech_node_id,
                    "type": "USED_TECHNOLOGY"
                })

        # 5. Projects & Experiences
        for p in profile.projects:
            proj_node_id = f"proj_{p.name.replace(' ', '_')}"
            nodes.append({
                "id": proj_node_id,
                "type": "Project",
                "label": p.name
            })
            edges.append({
                "source": evidence_anchor_id,
                "target": proj_node_id,
                "type": "PROVES_VIA_PROJECT"
            })

        for exp in profile.experiences:
            exp_node_id = f"exp_{exp.company_name.replace(' ', '_')}_{exp.job_title.replace(' ', '_')}"
            nodes.append({
                "id": exp_node_id,
                "type": "Experience",
                "label": f"{exp.job_title} at {exp.company_name}"
            })
            edges.append({
                "source": evidence_anchor_id,
                "target": exp_node_id,
                "type": "PROVES_VIA_EXPERIENCE"
            })

        # Clean duplicates
        unique_nodes = []
        seen_nodes = set()
        for node in nodes:
            if node["id"] not in seen_nodes:
                seen_nodes.add(node["id"])
                unique_nodes.append(node)

        unique_edges = []
        seen_edges = set()
        for edge in edges:
            edge_key = (edge["source"], edge["target"], edge["type"])
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                unique_edges.append(edge)

        return {
            "nodes": unique_nodes,
            "edges": unique_edges
        }

evidence_graph_builder = EvidenceGraphBuilder()
