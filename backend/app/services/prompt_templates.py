import json
from typing import Dict, Any

class PromptTemplateManager:
    """
    Manages provider-agnostic reusable prompt templates for LLM providers:
    - Local Transformers
    - Ollama
    - OpenRouter
    - HuggingFace
    """

    @staticmethod
    def get_extraction_system_prompt() -> str:
        return (
            "You are a Principal NLP and LLM Engineer specialized in Recruiter Intent Analysis.\n"
            "Your task is to parse an unstructured Job Description (JD) into a structured Recruiter Intent Profile.\n"
            "You must return ONLY a valid JSON object matching the requested schema. Do not write markdown blocks, explanations, or preface.\n"
            "Be precise, extract facts directly, and do not hallucinate."
        )

    @staticmethod
    def get_extraction_user_prompt(job_description: str) -> str:
        schema = {
            "title": "Software Engineer",
            "department": "Engineering / AI",
            "seniority": "Senior / Mid / Lead / Junior",
            "employment_type": "Full-time / Part-time / Contract",
            "experience_required_years": 5.0,
            "education": ["Bachelor's in CS or related field"],
            "skills": {
                "primary_skills": ["Python", "Machine Learning"],
                "secondary_skills": ["Git", "SQL"],
                "programming_languages": ["Python", "C++"],
                "tools": ["Docker", "Jira"],
                "frameworks": ["FastAPI", "PyTorch"],
                "cloud_platforms": ["AWS", "GCP"],
                "soft_skills": ["Mentorship", "Communication"],
                "certifications": ["AWS Certified Solutions Architect"]
            },
            "industry": "Technology / Finance / Healthcare",
            "location": "San Francisco, CA / Remote",
            "remote_compatibility": "Remote / Hybrid / Onsite",
            "salary": {
                "currency": "USD",
                "min": 120000,
                "max": 160000,
                "period": "yearly"
            }
        }
        return (
            f"Analyze the following Job Description and extract the structured recruiter intent profile.\n"
            f"Adhere strictly to this JSON format schema:\n"
            f"{json.dumps(schema, indent=2)}\n\n"
            f"Job Description:\n"
            f"\"\"\"\n{job_description}\n\"\"\""
        )

    @staticmethod
    def get_hidden_requirements_system_prompt() -> str:
        return (
            "You are a Principal AI Recruiter. You infer implied, hidden expectations that recruiters look for "
            "but often do not explicitly state in the job description text.\n"
            "For each inferred expectation, you must provide:\n"
            "1. An evidence snippet from the job description that supports this inference.\n"
            "2. A confidence score between 0.0 (low) and 1.0 (high).\n"
            "Provide output ONLY as a valid JSON dictionary mapping the inferred requirement name to a dictionary "
            "containing 'evidence' and 'confidence_score'."
        )

    @staticmethod
    def get_hidden_requirements_user_prompt(job_description: str) -> str:
        inferred_types = [
            "Leadership", "Ownership", "Mentorship", "System Design", "Scalability",
            "Customer Interaction", "Research", "Startup Experience", "Enterprise Experience",
            "Product Thinking", "Cross-functional Collaboration"
        ]
        return (
            f"Analyze the Job Description below and evaluate the following hidden expectations:\n"
            f"{', '.join(inferred_types)}\n\n"
            f"For each expectation, determine if there is implicit or explicit intent. If it is not implied at all, "
            f"give it a confidence_score of 0.0.\n"
            f"Return a JSON object in this format:\n"
            f"{{\n"
            f"  \"Leadership\": {{\n"
            f"    \"evidence\": \"Snippet indicating ownership or leading projects...\",\n"
            f"    \"confidence_score\": 0.85\n"
            f"  }}\n"
            f"}}\n\n"
            f"Job Description:\n"
            f"\"\"\"\n{job_description}\n\"\"\""
        )

    @staticmethod
    def format_provider_payload(
        provider: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """
        Format prompts for different downstream API providers.
        """
        prov_clean = provider.lower().strip()
        
        if prov_clean == "ollama":
            return {
                "model": "llama3",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "format": "json",
                "options": {"temperature": temperature}
            }
            
        elif prov_clean == "openrouter":
            return {
                "model": "meta-llama/llama-3-70b-instruct",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temperature,
                "response_format": {"type": "json_object"}
            }
            
        elif prov_clean == "huggingface":
            return {
                "inputs": f"<|system|>\n{system_prompt}\n<|user|>\n{user_prompt}\n<|assistant|>\n",
                "parameters": {"temperature": temperature, "return_full_text": False}
            }
            
        else:
            # Local Transformers default / generic OpenAI format
            return {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temperature
            }

prompt_templates = PromptTemplateManager()
