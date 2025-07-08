"""
pages 패키지 초기화

CRM 애플리케이션의 페이지 모듈들
"""

# 페이지 모듈들을 import
try:
    from . import company_page
    from . import contact_page
    from . import consultation_page
    from . import integration_page
except ImportError:
    # 백업 import 방식
    import company_page
    import contact_page
    import consultation_page
    import integration_page

__all__ = [
    'company_page',
    'contact_page', 
    'consultation_page',
    'integration_page'
]
