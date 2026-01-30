import unittest
import json
from pydantic import ValidationError
from naver_blog_seo import NaverSEO
from naver_blog_seo.models import SEOAuditResult, SEOAnalysis

class TestPydanticParsing(unittest.TestCase):
    def setUp(self):
        self.seo = NaverSEO()

    def test_audit_result_schema_generation(self):
        prompt = self.seo.get_system_prompt("audit", structured=True)
        self.assertIn("CRITICAL: Your final output MUST be a valid JSON object", prompt)
        self.assertIn('"title": "SEOAuditResult"', prompt)
        self.assertIn('"total_score"', prompt)

    def test_analysis_schema_generation(self):
        prompt = self.seo.get_system_prompt("blog", structured=True)
        self.assertIn('"title": "SEOAnalysis"', prompt)
        self.assertIn('"target_keyword"', prompt)

    def test_valid_audit_parsing(self):
        sample_json = {
            "total_score": 85,
            "grade": "Good",
            "content_length": {"score": 15, "max_score": 15, "details": "Great length"},
            "title_optimization": {"score": 15, "max_score": 20, "details": "Good but keep it shorter"},
            "structure": {"score": 20, "max_score": 20, "details": "Perfect structure"},
            "keyword_placement": {"score": 15, "max_score": 15, "details": "Well placed"},
            "content_quality": {"score": 15, "max_score": 20, "details": "Needs more experience points"},
            "cta_engagement": {"score": 5, "max_score": 10, "details": "Add more CTA"},
            "high_priority_fixes": ["Shorten title"],
            "medium_priority_recommendations": ["Add custom images"],
            "suggested_titles": ["Title 1", "Title 2"]
        }
        result = SEOAuditResult(**sample_json)
        self.assertEqual(result.total_score, 85)
        self.assertEqual(result.content_length.score, 15)

    def test_invalid_audit_parsing(self):
        invalid_json = {"total_score": "not a number"}
        with self.assertRaises(ValidationError):
            SEOAuditResult(**invalid_json)

if __name__ == "__main__":
    unittest.main()
