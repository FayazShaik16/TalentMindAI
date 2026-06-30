class SkillNormalizer:
    # Centralized alias mapping dictionary
    ALIASES = {
        "js": "javascript",
        "javascript": "javascript",
        "py": "python",
        "python": "python",
        "node": "node.js",
        "nodejs": "node.js",
        "node.js": "node.js",
        "ml": "machine learning",
        "machine learning": "machine learning",
        "ai": "artificial intelligence",
        "artificial intelligence": "artificial intelligence",
        "llm": "large language models",
        "large language models": "large language models",
        "k8s": "kubernetes",
        "kubernetes": "kubernetes",
        "docker": "docker",
        "react": "react",
        "reactjs": "react",
        "vue": "vue.js",
        "vuejs": "vue.js",
        "aws": "amazon web services",
        "amazon web services": "amazon web services",
        "gcp": "google cloud platform",
        "azure": "microsoft azure",
        "fastapi": "fastapi",
        "django": "django",
        "flask": "flask",
        "golang": "go",
        "rust": "rust",
        "cpp": "c++",
        "cplusplus": "c++",
    }

    # Centralized categories and hierarchy lists
    HIERARCHY = {
        "javascript": ("Programming Language", ["Programming Language", "Frontend", "Web Development"]),
        "python": ("Programming Language", ["Programming Language", "Backend", "AI / Data Science"]),
        "node.js": ("Backend Framework", ["Backend Framework", "JavaScript Runtime", "Backend Development"]),
        "machine learning": ("AI / Data Science", ["AI / Data Science", "Artificial Intelligence", "Advanced Analytics"]),
        "artificial intelligence": ("AI / Data Science", ["AI / Data Science", "Artificial Intelligence"]),
        "large language models": ("AI / Data Science", ["AI / Data Science", "Artificial Intelligence", "Generative AI"]),
        "kubernetes": ("DevOps / Infrastructure", ["DevOps / Infrastructure", "Container Orchestration", "Cloud Native"]),
        "docker": ("DevOps / Infrastructure", ["DevOps / Infrastructure", "Containerization"]),
        "react": ("Frontend Framework", ["Frontend Framework", "JavaScript Library", "Web Development"]),
        "amazon web services": ("Cloud Platform", ["Cloud Platform", "Infrastructure as Service"]),
        "google cloud platform": ("Cloud Platform", ["Cloud Platform", "Infrastructure as Service"]),
        "microsoft azure": ("Cloud Platform", ["Cloud Platform", "Infrastructure as Service"]),
        "fastapi": ("Backend Framework", ["Backend Framework", "Python Library", "Backend Development"]),
        "django": ("Backend Framework", ["Backend Framework", "Python Framework", "Backend Development"]),
        "go": ("Programming Language", ["Programming Language", "Backend", "Systems Programming"]),
        "rust": ("Programming Language", ["Programming Language", "Systems Programming", "Memory Safe"]),
        "c++": ("Programming Language", ["Programming Language", "Systems Programming", "High Performance"]),
    }

    def normalize(self, skill_name: str) -> dict:
        """
        Standardizes raw skill inputs into validated category and hierarchy keys.
        """
        s_clean = skill_name.strip().lower()
        norm_name = self.ALIASES.get(s_clean, skill_name.strip())
        norm_key = norm_name.lower()

        if norm_key in self.HIERARCHY:
            category, path = self.HIERARCHY[norm_key]
            # Standardize names nicely
            if norm_name in ["node.js", "c++", "k8s"]:
                nice_name = norm_name
            elif norm_name == "amazon web services":
                nice_name = "AWS"
            elif norm_name == "google cloud platform":
                nice_name = "GCP"
            else:
                nice_name = norm_name.title()
                
            return {
                "name": skill_name,
                "normalized_name": nice_name,
                "category": category,
                "hierarchy_path": path
            }

        # Fallback for untracked skills
        return {
            "name": skill_name,
            "normalized_name": skill_name.strip(),
            "category": "Other",
            "hierarchy_path": ["Other", skill_name.strip()]
        }

skill_normalizer = SkillNormalizer()
