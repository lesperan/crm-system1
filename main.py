import streamlit as st
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 페이지 설정
st.set_page_config(
    page_title="기업 상담 관리 시스템",
    page_icon="🏢",
    layout="wide"
)

# 데이터베이스 초기화
try:
    from database.connection import init_database, check_database_health
    conn = init_database()
    
    # 데이터베이스 상태 확인
    health = check_database_health(conn)
    if health['status'] != 'healthy':
        st.error(f"데이터베이스 상태: {health['status']}")
except Exception as e:
    st.error(f"데이터베이스 연결 오류: {str(e)}")
    st.stop()

# 페이지 import
try:
    from pages import company_page, contact_page, consultation_page, integration_page
except ImportError as e:
    st.error(f"페이지 모듈 import 오류: {str(e)}")
    st.stop()

# 사이드바 메뉴
st.sidebar.title("📋 메뉴")
menu = st.sidebar.selectbox(
    "작업을 선택하세요",
    ["기업 목록 관리", "고객 연락처 관리", "상담 이력 관리", "통합 데이터 조회", "데이터 다운로드"]
)

# 메인 타이틀
st.title("🏢 기업 상담 관리 시스템")
st.markdown("---")

# 페이지 라우팅
if menu == "기업 목록 관리":
    company_page.show_page(conn)
elif menu == "고객 연락처 관리":
    contact_page.show_page(conn)
elif menu == "상담 이력 관리":
    consultation_page.show_page(conn)
elif menu == "통합 데이터 조회":
    integration_page.show_page(conn)
elif menu == "데이터 다운로드":
    integration_page.show_download_page(conn)

# 사이드바 시스템 정보
st.sidebar.markdown("---")
st.sidebar.subheader("📈 시스템 현황")

try:
    # 현재 데이터 통계
    companies_count = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    contacts_count = conn.execute("SELECT COUNT(*) FROM customer_contacts").fetchone()[0]
    consultations_count = conn.execute("SELECT COUNT(*) FROM consultations").fetchone()[0]
    
    st.sidebar.metric("등록된 기업 수", companies_count)
    st.sidebar.metric("등록된 연락처 수", contacts_count)
    st.sidebar.metric("등록된 상담 건수", consultations_count)
    
    # 데이터베이스 파일 정보
    db_size = os.path.getsize('crm_database.db') if os.path.exists('crm_database.db') else 0
    st.sidebar.metric("DB 파일 크기", f"{db_size / 1024:.1f} KB")
    
except Exception as e:
    st.sidebar.error("시스템 정보를 불러올 수 없습니다.")

st.sidebar.markdown("---")
st.sidebar.info("""
**사용법:**
1. 기업 목록을 먼저 업로드하세요
2. 고객 연락처와 상담 이력을 추가하세요
3. 통합 데이터에서 전체 현황을 확인하세요
4. 필요한 데이터를 엑셀로 다운로드하세요
""")

# 환영 메시지 (처음 접속 시에만 표시)
if 'first_visit' not in st.session_state:
    st.session_state.first_visit = True
    st.balloons()
    st.success("""
    🎉 **기업 상담 관리 시스템에 오신 것을 환영합니다!**
    
    이 시스템으로 다음 작업을 수행할 수 있습니다:
    - 📋 기업 목록 관리 (엑셀 업로드/수정)
    - 👥 고객 연락처 관리
    - 📞 상담 이력 기록 및 관리
    - 📊 통합 데이터 조회 및 분석
    - 💾 데이터 백업 및 엑셀 다운로드
    
    **시작하려면 왼쪽 메뉴에서 원하는 기능을 선택하세요!**
    """)

# CSS 스타일
st.markdown("""
<style>
.main-header {
    text-align: center;
    padding: 1rem;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 10px;
    margin-bottom: 2rem;
}
.metric-card {
    background: white;
    padding: 1rem;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.success-message {
    background: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
    padding: 1rem;
    border-radius: 5px;
    margin: 1rem 0;
}
.warning-message {
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    color: #856404;
    padding: 1rem;
    border-radius: 5px;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)
