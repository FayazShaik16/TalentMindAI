from typing import Dict, Any, List

class RecruiterIntentGraphBuilder:
    """
    Constructs a semantic graph from the Recruiter Intent Profile and Hidden Expectations.
    Graph matches the path:
    Role -> Responsibilities -> Required Skills -> Preferred Skills -> Behavior -> Experience -> Industry -> Technology Stack
    """

    def build_graph(
        self,
        profile: Dict[str, Any],
        hidden_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Creates a list of nodes and edges representing the semantic relationships in the JD.
        """
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []

        # 1. Base Role node
        role_title = profile.get("title", "Software Engineer")
        role_node_id = "role_0"
        nodes.append({
            "id": role_node_id,
            "label": role_title,
            "type": "Role",
            "properties": {
                "seniority": profile.get("seniority"),
                "employment_type": profile.get("employment_type"),
                "remote_compatibility": profile.get("remote_compatibility")
            }
        })

        # 2. Experience node
        exp_val = profile.get("experience_required_years", 0.0)
        exp_node_id = "experience_0"
        nodes.append({
            "id": exp_node_id,
            "label": f"{exp_val} Years Experience",
            "type": "Experience",
            "properties": {
                "years": exp_val
            }
        })
        edges.append({
            "source": role_node_id,
            "target": exp_node_id,
            "relation": "requires_experience"
        })

        # 3. Industry node
        ind_val = profile.get("industry", "Technology")
        ind_node_id = "industry_0"
        nodes.append({
            "id": ind_node_id,
            "label": ind_val,
            "type": "Industry",
            "properties": {}
        })
        edges.append({
            "source": role_node_id,
            "target": ind_node_id,
            "relation": "belongs_to_industry"
        })

        # 4. Behavior Nodes (Hidden Expectations)
        for idx, (exp_name, exp_data) in enumerate(hidden_requirements.items()):
            node_id = f"behavior_{idx}"
            nodes.append({
                "id": node_id,
                "label": exp_name,
                "type": "Behavior",
                "properties": {
                    "confidence_score": exp_data.get("confidence_score"),
                    "evidence": exp_data.get("evidence")
                }
            })
            # Connect Role -> Behavior
            edges.append({
                "source": role_node_id,
                "target": node_id,
                "relation": "requires_behavior"
            })

        # 5. Required Skills (Primary) and Preferred Skills (Secondary) Nodes
        skills_data = profile.get("skills", {})
        primary_skills = skills_data.get("primary_skills", [])
        secondary_skills = skills_data.get("secondary_skills", [])
        
        # We also create a general Tech Stack grouping node
        stack_node_id = "tech_stack_0"
        nodes.append({
            "id": stack_node_id,
            "label": "Technology Stack",
            "type": "TechnologyStack",
            "properties": {}
        })
        edges.append({
            "source": role_node_id,
            "target": stack_node_id,
            "relation": "uses_stack"
        })

        # Responsibilities node(s)
        # We can map the evidence of hidden requirements as responsibilities
        resp_node_id = "responsibilities_0"
        evidence_snippets = [data["evidence"] for data in hidden_requirements.values() if data.get("evidence")]
        nodes.append({
            "id": resp_node_id,
            "label": "Core Responsibilities",
            "type": "Responsibilities",
            "properties": {
                "snippets": evidence_snippets[:3] # Keep top 3 for visualization clarity
            }
        })
        edges.append({
            "source": role_node_id,
            "target": resp_node_id,
            "relation": "performs"
        })

        # Connect Responsibilities -> Required Skills
        # Map primary skills
        for idx, skill in enumerate(primary_skills):
            node_id = f"required_skill_{idx}"
            nodes.append({
                "id": node_id,
                "label": skill,
                "type": "RequiredSkill",
                "properties": {}
            })
            # Role -> Required Skill
            edges.append({
                "source": role_node_id,
                "target": node_id,
                "relation": "requires_primary"
            })
            # Responsibilities -> Required Skill
            edges.append({
                "source": resp_node_id,
                "target": node_id,
                "relation": "requires_skill"
            })
            # Required Skill -> Tech Stack
            edges.append({
                "source": node_id,
                "target": stack_node_id,
                "relation": "part_of_stack"
            })

        # Map secondary skills
        for idx, skill in enumerate(secondary_skills):
            node_id = f"preferred_skill_{idx}"
            nodes.append({
                "id": node_id,
                "label": skill,
                "type": "PreferredSkill",
                "properties": {}
            })
            # Role -> Preferred Skill
            edges.append({
                "source": role_node_id,
                "target": node_id,
                "relation": "prefers_secondary"
            })
            # Preferred Skill -> Tech Stack
            edges.append({
                "source": node_id,
                "target": stack_node_id,
                "relation": "part_of_stack"
            })

        return {
            "nodes": nodes,
            "edges": edges
        }

intent_graph_builder = RecruiterIntentGraphBuilder()
