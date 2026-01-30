import unittest
from naver_blog_seo import NaverSEO

class TestNaverSEO(unittest.TestCase):
    def setUp(self):
        self.seo = NaverSEO()

    def test_get_blog_instruction(self):
        content = self.seo.get_blog_instruction()
        self.assertIn("Naver Blog SEO Optimizer Skill", content)
        self.assertGreater(len(content), 1000)

    def test_get_audit_instruction(self):
        content = self.seo.get_audit_instruction()
        self.assertIn("Naver Blog SEO Audit Skill", content)
        self.assertGreater(len(content), 1000)

    def test_get_system_prompt_blog(self):
        prompt = self.seo.get_system_prompt("blog")
        self.assertIn("Naver Blog SEO Optimizer Skill", prompt)
        self.assertIn("follow these SEO guidelines", prompt)

    def test_get_system_prompt_audit(self):
        prompt = self.seo.get_system_prompt("audit")
        self.assertIn("Naver Blog SEO Audit Skill", prompt)
        self.assertIn("analyze the provided blog content", prompt)

    def test_invalid_task_type(self):
        with self.assertRaises(ValueError):
            self.seo.get_system_prompt("invalid")

if __name__ == "__main__":
    unittest.main()
