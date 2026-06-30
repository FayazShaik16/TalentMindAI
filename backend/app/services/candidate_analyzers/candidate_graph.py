from typing import Any, Dict, List
from app.schemas.candidate import CandidateProfile

class CandidateGraphBuilder:
    """
    Constructs the Candidate Knowledge Graph showing relationships:
    Candidate -> Experience -> Projects -> Skills -> Companies -> Domains -> Certifications -> Education -> Leadership.
    """

    def build_graph(self, profile: CandidateProfile, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        nodes = []
        edges = []

        cand_id = profile.id
        cand_name = f"{profile.personal_info.first_name} {profile.personal_info.last_name}"

        # 1. Candidate Node (root)
        nodes.append({
            "id": cand_id,
            "type": "Candidate",
            "label": cand_name
        })

        # 2. Educations
        for edu in profile.educations:
            edu_id = f"edu_{edu.institution.replace(' ', '_')}_{edu.degree or 'deg'}"
            nodes.append({
                "id": edu_id,
                "type": "Education",
                "label": f"{edu.degree or 'Degree'} at {edu.institution}"
            })
            edges.append({
                "source": cand_id,
                "target": edu_id,
                "type": "HAS_EDUCATION"
            })

        # 3. Certifications
        for cert in profile.certifications:
            cert_id = f"cert_{cert.name.replace(' ', '_')}"
            nodes.append({
                "id": cert_id,
                "type": "Certification",
                "label": cert.name
            })
            edges.append({
                "source": cand_id,
                "target": cert_id,
                "type": "HAS_CERTIFICATION"
            })

        # 4. Experiences and Companies
        for exp in profile.experiences:
            exp_id = f"exp_{exp.company_name.replace(' ', '_')}_{exp.job_title.replace(' ', '_')}"
            nodes.append({
                "id": exp_id,
                "type": "Experience",
                "label": f"{exp.job_title} at {exp.company_name}"
            })
            edges.append({
                "source": cand_id,
                "target": exp_id,
                "type": "HAS_EXPERIENCE"
            })

            # Company Node
            comp_id = f"comp_{exp.company_name.replace(' ', '_')}"
            nodes.append({
                "id": comp_id,
                "type": "Company",
                "label": exp.company_name
            })
            edges.append({
                "source": exp_id,
                "target": comp_id,
                "type": "WORKED_AT"
            })

        # 5. Skills
        for s in profile.skills:
            skill_id = f"skill_{s.normalized_name or s.name}"
            nodes.append({
                "id": skill_id,
                "type": "Skill",
                "label": s.normalized_name or s.name
            })
            edges.append({
                "source": cand_id,
                "target": skill_id,
                "type": "HAS_SKILL"
            })

        # 6. Projects and Technologies
        for p in profile.projects:
            proj_id = f"proj_{p.name.replace(' ', '_')}"
            nodes.append({
                "id": proj_id,
                "type": "Project",
                "label": p.name
            })
            edges.append({
                "source": cand_id,
                "target": proj_id,
                "type": "HAS_PROJECT"
            })

            # Link projects to technologies
            for tech in p.technologies:
                tech_id = f"skill_{tech}"
                # If node does not exist, append it as Technology type
                if not any(n["id"] == tech_id for n in nodes):
                    nodes.append({
                        "id": tech_id,
                        "type": "Technology",
                        "label": tech
                    })
                edges.append({
                    "source": proj_id,
                    "target": tech_id,
                    "type": "USES_TECH"
                })

            # Link project to domain if exists
            if p.domain:
                dom_id = f"domain_{p.domain.replace(' ', '_')}"
                if not any(n["id"] == dom_id for n in nodes):
                    nodes.append({
                        "id": dom_id,
                        "type": "Domain",
                        "label": p.domain
                    })
                edges.append({
                    "source": proj_id,
                    "target": dom_id,
                    "type": "IN_DOMAIN"
                })

        # 7. Domains (from Domain Intelligence)
        detected_domains = analysis_results.get("domains", {}).get("detected_domains", {})
        for dom_name, dom_info in detected_domains.items():
            dom_id = f"domain_{dom_name.replace(' ', '_')}"
            if not any(n["id"] == dom_id for n in nodes):
                nodes.append({
                    "id": dom_id,
                    "type": "Domain",
                    "label": dom_name
                })
            edges.append({
                "source": cand_id,
                "target": dom_id,
                "type": "OPERATES_IN"
            })

        # 8. Leadership
        leadership_data = analysis_results.get("leadership", {})
        for dimension in ["team_leadership", "mentoring", "architecture_ownership", "technical_leadership"]:
            if leadership_data.get(dimension, {}).get("has_exposure", False):
                lead_id = f"leadership_{dimension}"
                nodes.append({
                    "id": lead_id,
                    "type": "Leadership",
                    "label": dimension.replace('_', ' ').title()
                })
                edges.append({
                    "source": cand_id,
                    "target": lead_id,
                    "type": "HAS_LEADERSHIP"
                })

        # Return unique nodes and edges lists
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

candidate_graph_builder = CandidateGraphBuilder()
