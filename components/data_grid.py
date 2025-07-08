"""
components/data_grid.py

편집 가능한 데이터 그리드 컴포넌트들
"""

import streamlit as st
import pandas as pd
import sys
import os

# 상위 디렉토리를 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from database.operations import get_industries, save_edited_companies, clear_all_caches
from database.connection import test_write_permission


def editable_companies_grid(companies_df, conn):
    """
    편집 가능한 기업 데이터 그리드
    
    Args:
        companies_df (pd.DataFrame): 기업 데이터
        conn: 데이터베이스 연결
        
    Returns:
        bool: 저장 성공 여부
    """
    if companies_df.empty:
        st.info("편집할 기업 데이터가 없습니다. 먼저 기업 목록을 추가해주세요.")
        return False
    
    # 쓰기 권한 확인
    if not test_write_permission():
        st.error("⚠️ 데이터베이스 쓰기 권한이 없습니다. 관리자에게 문의하세요.")
        return False
    
    # 자동완성 데이터 준비
    industries = get_industries()
    
    # 컬럼 설정 (편집 가능한 컬럼 지정)
    column_config = {
        "업체코드": st.column_config.TextColumn(
            "업체코드",
            disabled=True,  # 업체코드는 편집 불가
            help="자동 생성된 업체코드 (편집 불가)"
        ),
        "기업명": st.column_config.TextColumn(
            "기업명",
            required=True,
            help="기업명을 입력하세요"
        ),
        "매출액_2024": st.column_config.NumberColumn(
            "매출액 (2024)",
            format="%.0f",
            help="2024년 매출액 (단위: 원)"
        ),
        "업종": st.column_config.SelectboxColumn(
            "업종",
            options=[""] + industries,
            help="업종을 선택하거나 새로 입력하세요"
        ),
        "종업원수": st.column_config.NumberColumn(
            "종업원수",
            format="%.0f",
            min_value=0,
            help="전체 종업원 수"
        ),
        "주소": st.column_config.TextColumn(
            "주소",
            help="기업 주소"
        ),
        "상품": st.column_config.TextColumn(
            "상품/서비스",
            help="주요 상품이나 서비스"
        ),
        "고객구분": st.column_config.SelectboxColumn(
            "고객구분",
            options=["", "신규", "기존", "잠재", "VIP"],
            help="고객 구분"
        )
    }
    
    # 편집 가능한 데이터 에디터
    edited_df = st.data_editor(
        companies_df,
        column_config=column_config,
        use_container_width=True,
        num_rows="dynamic",  # 행 추가/삭제 가능
        key="companies_editor"
    )
    
    # 변경사항 저장 버튼
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("💾 변경사항 저장", type="primary"):
            try:
                success, changes_count, errors = save_edited_companies(conn, edited_df, companies_df)
                
                if success:
                    if changes_count > 0:
                        st.success(f"✅ {changes_count}개의 변경사항이 저장되었습니다!")
                        clear_all_caches()
                        st.rerun()
                    else:
                        st.info("변경사항이 없습니다.")
                
                if errors:
                    st.error("❌ 다음 오류가 발생했습니다:")
                    for error in errors:
                        st.write(f"- {error}")
                
                return success and changes_count > 0
                
            except Exception as e:
                st.error(f"저장 중 전체 오류 발생: {str(e)}")
                return False
    
    with col2:
        if st.button("🔄 새로고침"):
            st.rerun()
    
    with col3:
        st.write("**사용법:** 셀을 클릭하여 직접 편집하거나, 맨 아래 행에서 새 기업을 추가할 수 있습니다.")
    
    return False


def simple_company_editor(companies_df, conn):
    """
    단순한 기업 편집 인터페이스 (개별 기업 편집)
    
    Args:
        companies_df (pd.DataFrame): 기업 데이터
        conn: 데이터베이스 연결
        
    Returns:
        bool: 편집 성공 여부
    """
    if companies_df.empty:
        st.info("편집할 기업 데이터가 없습니다. 먼저 기업 목록을 추가해주세요.")
        return False
    
    # 편집할 기업 선택
    company_names = companies_df['기업명'].tolist()
    selected_company = st.selectbox("편집할 기업을 선택하세요:", company_names)
    
    if selected_company:
        # 선택된 기업의 현재 정보
        current_data = companies_df[companies_df['기업명'] == selected_company].iloc[0]
        
        # 편집 폼
        with st.form("edit_company_form"):
            st.write(f"**편집 중인 기업: {selected_company}**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                new_company_name = st.text_input("기업명", value=current_data['기업명'])
                new_revenue = st.number_input(
                    "매출액 (2024)", 
                    value=float(current_data['매출액_2024']) if current_data['매출액_2024'] else 0.0, 
                    min_value=0.0
                )
                new_industry = st.text_input("업종", value=current_data['업종'] if current_data['업종'] else "")
                new_employee_count = st.number_input(
                    "종업원수", 
                    value=int(current_data['종업원수']) if current_data['종업원수'] else 0, 
                    min_value=0
                )
            
            with col2:
                new_address = st.text_area("주소", value=current_data['주소'] if current_data['주소'] else "")
                new_products = st.text_area("상품/서비스", value=current_data['상품'] if current_data['상품'] else "")
                new_category = st.selectbox(
                    "고객구분", 
                    options=["", "신규", "기존", "잠재", "VIP"], 
                    index=0 if not current_data['고객구분'] else 
                          ["", "신규", "기존", "잠재", "VIP"].index(current_data['고객구분'])
                )
            
            # 저장 버튼
            if st.form_submit_button("💾 변경사항 저장", type="primary"):
                try:
                    conn.execute('''
                        UPDATE companies SET 
                        company_name = ?, revenue_2024 = ?, industry = ?, 
                        employee_count = ?, address = ?, products = ?, 
                        customer_category = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE company_code = ?
                    ''', (
                        new_company_name,
                        new_revenue if new_revenue > 0 else None,
                        new_industry if new_industry else None,
                        new_employee_count if new_employee_count > 0 else None,
                        new_address if new_address else None,
                        new_products if new_products else None,
                        new_category if new_category else None,
                        current_data['업체코드']
                    ))
                    conn.commit()
                    st.success("✅ 기업 정보가 성공적으로 업데이트되었습니다!")
                    clear_all_caches()
                    st.rerun()
                    return True
                except Exception as e:
                    st.error(f"❌ 업데이트 실패: {str(e)}")
                    return False
    
    return False


def display_data_with_stats(df, title, key_prefix=""):
    """
    데이터프레임을 통계와 함께 표시
    
    Args:
        df (pd.DataFrame): 표시할 데이터프레임
        title (str): 제목
        key_prefix (str): 위젯 키 접두사
    """
    st.subheader(title)
    
    if not df.empty:
        # 통계 정보 표시
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("총 레코드 수", len(df))
        
        with col2:
            if '기업명' in df.columns:
                st.metric("기업 수", df['기업명'].nunique())
        
        with col3:
            if '매출액_2024' in df.columns and not df['매출액_2024'].isna().all():
                avg_revenue = df['매출액_2024'].mean()
                st.metric("평균 매출액", f"{avg_revenue:,.0f}" if not pd.isna(avg_revenue) else "N/A")
        
        # 데이터 테이블 표시
        st.dataframe(df, use_container_width=True, key=f"{key_prefix}_dataframe")
        
        # 필터링 옵션 (선택사항)
        if len(df) > 10:
            with st.expander("🔍 데이터 필터링"):
                if '기업명' in df.columns:
                    company_filter = st.multiselect(
                        "기업 선택",
                        options=df['기업명'].unique(),
                        key=f"{key_prefix}_company_filter"
                    )
                    
                    if company_filter:
                        filtered_df = df[df['기업명'].isin(company_filter)]
                        st.write(f"필터링된 결과: {len(filtered_df)}개 레코드")
                        st.dataframe(filtered_df, use_container_width=True, key=f"{key_prefix}_filtered")
    else:
        st.info("표시할 데이터가 없습니다.")
