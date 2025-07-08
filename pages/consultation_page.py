"""
pages/consultation_page.py

상담 이력 관리 페이지
"""

import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime

# 상위 디렉토리를 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from database.operations import (
    get_consultations_data, 
    insert_consultation_batch, 
    insert_new_consultation,
    clear_all_caches
)
from components.autocomplete import (
    company_name_selector,
    customer_name_selector
)
from components.data_grid import display_data_with_stats
from utils.validators import validate_consultation_content


def show_page(conn):
    """상담 이력 관리 페이지 표시"""
    st.header("📞 상담 이력 관리")
    
    tab1, tab2, tab3 = st.tabs(["엑셀 업로드", "직접 입력", "상담 이력 조회"])
    
    with tab1:
        show_upload_section(conn)
    
    with tab2:
        show_direct_input_section(conn)
    
    with tab3:
        show_current_consultations(conn)


def show_upload_section(conn):
    """엑셀 업로드 섹션"""
    st.subheader("상담 이력 엑셀 업로드")
    consultation_file = st.file_uploader(
        "상담 이력 엑셀 파일을 업로드하세요",
        type=['xlsx', 'xls'],
        key="consultation_upload"
    )
    
    if consultation_file is not None:
        try:
            df = pd.read_excel(consultation_file)
            st.success("✅ 파일을 성공적으로 읽었습니다!")
            
            st.subheader("업로드된 데이터 미리보기")
            st.dataframe(df, use_container_width=True)
            
            # 컬럼 매핑
            st.subheader("컬럼 매핑")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**필수 매핑**")
                company_name_col = st.selectbox("기업명 컬럼", df.columns, key="consult_company_mapping")
                content_col = st.selectbox("상담내역 컬럼", df.columns, key="consult_content_mapping")
            
            with col2:
                st.write("**선택 매핑**")
                customer_col = st.selectbox("고객명 컬럼", ["선택안함"] + list(df.columns), key="consult_customer_mapping")
                date_col = st.selectbox("날짜 컬럼", ["선택안함"] + list(df.columns), key="consult_date_mapping")
                project_col = st.selectbox("프로젝트 컬럼", ["선택안함"] + list(df.columns), key="consult_project_mapping")
            
            if st.button("상담 이력 저장", type="primary"):
                consultations_data = []
                
                for _, row in df.iterrows():
                    company_name = row[company_name_col]
                    consultation_content = row[content_col]
                    
                    if pd.isna(company_name) or pd.isna(consultation_content) or company_name == "" or consultation_content == "":
                        continue
                    
                    # 유효성 검사
                    content_valid, content_error = validate_consultation_content(consultation_content)
                    if not content_valid:
                        st.warning(f"행 {len(consultations_data)+1}: {content_error}")
                        continue
                    
                    # 상담 정보 준비
                    customer_name = row[customer_col] if customer_col != "선택안함" and not pd.isna(row[customer_col]) else None
                    consultation_date = row[date_col] if date_col != "선택안함" and not pd.isna(row[date_col]) else None
                    project_name = row[project_col] if project_col != "선택안함" and not pd.isna(row[project_col]) else None
                    
                    consultation_data = {
                        'company_name': company_name,
                        'customer_name': customer_name,
                        'consultation_date': consultation_date,
                        'consultation_content': consultation_content,
                        'project_name': project_name
                    }
                    consultations_data.append(consultation_data)
                
                # 일괄 저장
                success, message = insert_consultation_batch(conn, consultations_data)
                
                if success:
                    st.success(f"✅ {message}")
                    clear_all_caches()
                else:
                    st.error(f"저장 중 오류 발생: {message}")
                        
        except Exception as e:
            st.error(f"파일 읽기 오류: {str(e)}")


def show_direct_input_section(conn):
    """직접 입력 섹션"""
    st.subheader("상담 이력 직접 입력")
    st.info("💡 **빠른 상담 이력 추가:** 기존 고객사와 담당자 정보를 활용하여 신속하게 상담 이력을 추가할 수 있습니다.")
    
    with st.form("consultation_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**기본 정보**")
            company_name = company_name_selector("consultation_form")
            customer_name = customer_name_selector("consultation_form")
            consultation_date = st.date_input("상담 날짜", value=datetime.now().date())
            project_name = st.text_input("프로젝트명 (선택)")
        
        with col2:
            st.write("**상담 내용**")
            consultation_content = st.text_area(
                "상담 내역 (필수)",
                height=200,
                placeholder="상담 내용을 자세히 입력하세요...",
                help="최소 5자 이상, 최대 2000자까지 입력 가능합니다."
            )
        
        submitted = st.form_submit_button("📞 상담 이력 저장", type="primary")
        
        if submitted:
            # 필수 필드 검증
            if not company_name or not consultation_content:
                st.error("기업명과 상담 내역은 필수입니다.")
                return
            
            # 상담 내용 유효성 검사
            content_valid, content_error = validate_consultation_content(consultation_content)
            if not content_valid:
                st.error(f"상담 내용 오류: {content_error}")
                return
            
            # 상담 이력 저장
            consultation_data = {
                '기업명': company_name,
                '고객명': customer_name if customer_name else None,
                '상담날짜': consultation_date.strftime("%Y.%m.%d"),
                '상담내역': consultation_content,
                '프로젝트명': project_name if project_name else None
            }
            
            success, message = insert_new_consultation(conn, consultation_data)
            
            if success:
                st.success(f"✅ {message}")
                clear_all_caches()
                st.rerun()
            else:
                st.error(f"저장 실패: {message}")


def show_current_consultations(conn):
    """현재 상담 이력 섹션"""
    try:
        consultations_df = get_consultations_data(conn)
        
        if not consultations_df.empty:
            # 최근 상담 이력 강조 표시
            st.subheader("📋 상담 이력 조회")
            
            # 필터링 옵션
            with st.expander("🔍 필터링 옵션"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # 기업별 필터
                    companies = ["전체"] + list(consultations_df['기업명'].unique())
                    selected_company = st.selectbox("기업 선택", companies)
                
                with col2:
                    # 날짜 범위 필터
                    date_filter = st.selectbox(
                        "기간 선택", 
                        ["전체", "최근 1주일", "최근 1개월", "최근 3개월", "최근 6개월"]
                    )
                
                with col3:
                    # 프로젝트별 필터
                    projects = ["전체"] + [p for p in consultations_df['프로젝트명'].dropna().unique() if p]
                    selected_project = st.selectbox("프로젝트 선택", projects)
            
            # 필터 적용
            filtered_df = consultations_df.copy()
            
            if selected_company != "전체":
                filtered_df = filtered_df[filtered_df['기업명'] == selected_company]
            
            if date_filter != "전체":
                from datetime import timedelta
                today = datetime.now().date()
                
                if date_filter == "최근 1주일":
                    cutoff_date = today - timedelta(days=7)
                elif date_filter == "최근 1개월":
                    cutoff_date = today - timedelta(days=30)
                elif date_filter == "최근 3개월":
                    cutoff_date = today - timedelta(days=90)
                elif date_filter == "최근 6개월":
                    cutoff_date = today - timedelta(days=180)
                
                # 날짜 컬럼을 datetime으로 변환 후 필터링
                try:
                    filtered_df['상담날짜_datetime'] = pd.to_datetime(filtered_df['상담날짜'], errors='coerce')
                    filtered_df = filtered_df[filtered_df['상담날짜_datetime'].dt.date >= cutoff_date]
                    filtered_df = filtered_df.drop('상담날짜_datetime', axis=1)
                except:
                    pass  # 날짜 변환 실패 시 필터링 건너뛰기
            
            if selected_project != "전체":
                filtered_df = filtered_df[filtered_df['프로젝트명'] == selected_project]
            
            # 결과 표시
            if not filtered_df.empty:
                st.write(f"**총 {len(filtered_df)}건의 상담 이력**")
                display_data_with_stats(filtered_df, "", "consultations")
                
                # 최근 상담 내용 미리보기
                if len(filtered_df) > 0:
                    with st.expander("📝 최근 상담 내용 미리보기"):
                        recent_consultation = filtered_df.iloc[0]
                        st.write(f"**기업:** {recent_consultation['기업명']}")
                        st.write(f"**고객:** {recent_consultation['고객명']}")
                        st.write(f"**날짜:** {recent_consultation['상담날짜']}")
                        st.write(f"**프로젝트:** {recent_consultation['프로젝트명']}")
                        st.write("**상담 내용:**")
                        st.write(recent_consultation['상담내역'])
            else:
                st.info("선택한 조건에 해당하는 상담 이력이 없습니다.")
        else:
            st.info("저장된 상담 이력이 없습니다.")
            
    except Exception as e:
        st.error(f"상담 이력 데이터 조회 오류: {str(e)}")
