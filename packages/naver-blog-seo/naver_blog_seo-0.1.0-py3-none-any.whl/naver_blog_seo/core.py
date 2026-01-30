import importlib.resources as resources
import json
from pathlib import Path
from typing import Literal, Optional, Type, Union
from pydantic import BaseModel
from .models import SEOAnalysis, SEOAuditResult

class NaverSEO:
    """
    A class to load and provide Naver Blog SEO skills/instructions.
    """
    
    SKILLS_PACKAGE = "naver_blog_seo.skills"

    def _load_skill(self, filename: str) -> str:
        """Helper to load a markdown file from the skills package."""
        try:
            # Using modern importlib.resources (Python 3.9+)
            with resources.files(self.SKILLS_PACKAGE).joinpath(filename).open("r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Skill file '{filename}' not found in {self.SKILLS_PACKAGE}")

    def get_blog_instruction(self) -> str:
        """Returns the full text of the Naver Blog SEO Optimizer skill."""
        return self._load_skill("naver-blog-seo.md")

    def get_audit_instruction(self) -> str:
        """Returns the full text of the Naver Blog SEO Audit skill."""
        return self._load_skill("naver-blog-audit.md")

    def get_schema_instructions(self, model: Type[BaseModel]) -> str:
        """Returns instructions for the LLM to output valid JSON matching the model's schema."""
        schema = model.model_json_schema()
        # Clean up the schema for better LLM consumption
        schema_json = json.dumps(schema, indent=2, ensure_ascii=False)
        return (
            "\nCRITICAL: Your final output MUST be a valid JSON object matching the following schema:\n"
            f"```json\n{schema_json}\n```\n"
            "Do not include any conversational text before or after the JSON block."
        )

    def get_system_prompt(self, task_type: Literal["blog", "audit"], structured: bool = False) -> str:
        """
        Returns a formatted system prompt for an LLM based on the task type.
        
        Args:
            task_type: Either 'blog' for generation or 'audit' for analysis.
            structured: If True, appends JSON schema instructions for programmatic parsing.
        """
        if task_type == "blog":
            instruction = self.get_blog_instruction()
            suffix = "\nPlease follow these SEO guidelines to write the blog post."
            schema_model = SEOAnalysis if structured else None
        elif task_type == "audit":
            instruction = self.get_audit_instruction()
            suffix = "\nPlease analyze the provided blog content based on these SEO audit rules."
            schema_model = SEOAuditResult if structured else None
        else:
            raise ValueError("task_type must be 'blog' or 'audit'")

        prompt = f"{instruction}\n\n{suffix}"
        
        if structured and schema_model:
            prompt += self.get_schema_instructions(schema_model)
            
        return prompt
