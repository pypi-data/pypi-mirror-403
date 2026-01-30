import sys
from naver_blog_seo.core import NaverSEO

def main():
    """Simple CLI to verify skill loading."""
    print("🔍 Checking Naver Blog SEO Skills...")
    seo = NaverSEO()
    
    try:
        blog_len = len(seo.get_blog_instruction())
        audit_len = len(seo.get_audit_instruction())
        
        print(f"✅ Blog Optimizer Skill: Loaded ({blog_len} characters)")
        print(f"✅ Blog Audit Skill: Loaded ({audit_len} characters)")
        print("\n🚀 Naver SEO Wrapper is ready for use!")
        
    except Exception as e:
        print(f"❌ Error loading skills: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
