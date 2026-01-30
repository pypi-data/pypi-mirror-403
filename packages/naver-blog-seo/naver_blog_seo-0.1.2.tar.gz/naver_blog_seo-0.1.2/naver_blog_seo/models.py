from pydantic import BaseModel, Field
from typing import List, Optional

class SEOAuditCategory(BaseModel):
    score: int = Field(..., description="Score for the category out of the max possible points")
    max_score: int = Field(..., description="Maximum possible points for this category")
    details: str = Field(..., description="Detailed explanation of the score and findings")

class SEOAuditResult(BaseModel):
    total_score: int = Field(..., description="Total SEO score out of 100")
    grade: str = Field(..., description="Grade (e.g., Optimal, Good, Needs Improvement, Rewrite Recommended)")
    
    # Category Breakdowns
    content_length: SEOAuditCategory
    title_optimization: SEOAuditCategory
    structure: SEOAuditCategory
    keyword_placement: SEOAuditCategory
    content_quality: SEOAuditCategory
    cta_engagement: SEOAuditCategory
    
    # Recommendations
    high_priority_fixes: List[str] = Field(..., description="List of essential fixes")
    medium_priority_recommendations: List[str] = Field(..., description="List of recommended improvements")
    suggested_titles: List[str] = Field(..., description="Improved title suggestions")

class SEOAnalysis(BaseModel):
    target_keyword: str
    longtail_keywords: List[str]
    intent: str
    blog_content: str
    meta_tags: List[str]
    audit_result: Optional[SEOAuditResult] = None
