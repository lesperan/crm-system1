"""
pages/integration_page.py

통합 데이터 조회 및 편집 페이지
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
    get_integrated_data, 
    get_companies_data,
    get_contacts_data,
    get_consultations_data,
    insert_new_consultation,
    clear_all_caches
)
from components.data_grid import (
    editable_companies_grid,
    simple_company_editor,
    display_data_with_stats
)
from components.autocomplete import (
    company_name_selector,
    customer_name_selector
)
from utils.file_handlers import create_excel_file, generate_download_filename


def show_page(conn):
    """통합 데이터 조회 및 편집 페이지 표시"""
    st.header("📊 통합 데이터 조회 및 편집")
    
    # 편집 모드 선택
    edit_mode = st.radio(
        "모드 선택",
        ["조회만", "편집 모드", "새 상담 추가"],
        horizontal=True
    )
    
    if edit_mode == "조회만":
        show_view_only_mode(conn)
    elif edit_mode == "편집 모드":
        show_edit_mode(conn)
    elif edit_mode == "새 상담 추가":
        show_quick_consultation_mode(conn)


def show_view_only_mode(conn):
    """조회 전용 모드"""
    st.subheader("통합 데이터 조회")
    
    try:
        integrated_df = get_integrated_data(conn)
        
        if not integrated_df.empty:
            # 요약 통계
            st.subheader("📈 요약 통계")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("총 기업 수", integrated_df['기업명'].nunique())
            with col2:
                st.metric("총 연락처 수", integrated_df['고객명'].count())
            with col3:
                st.metric("총 상담 건수", integrated_df['상담내역'].count())
            with col4:
                if not integrated_df['매출액_2024'].isna().all():
                    avg_revenue = integrated_df['매출액_2024'].mean()
                    st.metric("평균 매출액", f"{avg_revenue:,.0f}" if not pd.isna(avg_revenue) else "N/A")
            
            # 데이터 표시
            display_data_with_stats(integrated_df, "통합 데이터", "integrated")
            
        else:
            st.info("통합할 데이터가 없습니다.")
            
    except Exception as e:
        st.error(f"데이터 조회 오류: {str(e)}")


def show_edit_mode(conn):
    """편집 모드"""
    st.subheader("📝 기업 정보 편집")
    st.info("💡 **기업 정보만 편집 가능합니다.** 연락처와 상담 이력은 각각의 메뉴에서 관리하세요.")
    
    # 편집 방식 선택
    edit_style = st.radio(
        "편집 방식 선택",
        ["그리드 편집 (고급)", "개별 편집 (안전)"],
        help="그리드 편집: 여러 기업을 한 번에 편집 | 개별 편집: 한 기업씩 안전하게 편집"
    )
    
    try:
        companies_df = get_companies_data(conn)
        
        if not companies_df.empty:
            if edit_style == "그리드 편집 (고급)":
                # 고급 그리드 편집
                editable_companies_grid(companies_df, conn)
            else:
                # 단순 개별 편집
                simple_company_editor(companies_df, conn)
                
                # 새 기업 추가 섹션
                show_add_new_company_section(conn)
        else:
            st.info("편집할 기업 데이터가 없습니다. 먼저 기업 목록을 추가해주세요.")
            
    except Exception as e:
        st.error(f"편집 모드 오류: {str(e)}")
    
    # 최근 상담 이력 표시
    show_recent_consultations(conn)


def show_add_new_company_section(conn):
    """새 기업 추가 섹션"""
    st.markdown("---")
    st.subheader("➕ 새 기업 추가")
    
    with st.form("add_company_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            add_company_name = st.text_input("기업명 *")
            add_revenue = st.number_input("매출액 (2024)", min_value=0.0)
            add_industry = st.text_input("업종")
            add_employee_count = st.number_input("종업원수", min_value=0)
        
        with col2:
            add_address = st.text_area("주소")
            add_products = st.text_area("상품/서비스")
            add_category = st.selectbox("고객구분", options=["", "신규", "기존", "잠재", "VIP"])
        
        if st.form_submit_button("➕ 새 기업 추가", type="secondary"):
            if add_company_name.strip():
                try:
                    from database.connection import generate_company_code
                    new_code = generate_company_code()
                    
                    conn.execute('''
                        INSERT INTO companies 
                        (company_code, company_name, revenue_2024, industry, employee_count, address, products, customer_category)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        new_code,
                        add_company_name,
                        add_revenue if add_revenue > 0 else None,
                        add_industry if add_industry else None,
                        add_employee_count if add_employee_count > 0 else None,
                        add_address if add_address else None,
                        add_products if add_products else None,
                        add_category if add_category else None
                    ))
                    conn.commit()
                    st.success("✅ 새 기업이 성공적으로 추가되었습니다!")
                    clear_all_caches()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 추가 실패: {str(e)}")
            else:
                st.error("기업명은 필수입니다.")


def show_quick_consultation_mode(conn):
    """빠른 상담 추가 모드"""
    st.subheader("📞 새 상담 이력 추가")
    st.info("💡 **빠른 상담 이력 추가:** 기존 고객사와 담당자 정보를 활용하여 신속하게 상담 이력을 추가할 수 있습니다.")
    
    try:
        from database.operations import get_company_names
        company_names = get_company_names()
        
        if company_names:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**기업 정보**")
                company_name = company_name_selector("quick")
                customer_name = customer_name_selector("quick")
                consultation_date = st.date_input("상담 날짜", key="quick_date")
                project_name = st.text_input("프로젝트명 (선택)", key="quick_project")
            
            with col2:
                st.write("**상담 내용**")
                consultation_content = st.text_area(
                    "상담 내역 (필수)",
                    height=300,
                    placeholder="상담 내용을 자세히 입력하세요...",
                    key="quick_content"
                )
            
            # 저장 버튼
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button("💾 상담 이력 저장", type="primary"):
                    if consultation_content.strip() and company_name.strip():
                        consultation_data = {
                            '기업명': company_name,
                            '고객명': customer_name if customer_name else None,
                            '상담날짜': consultation_date.strftime("%Y.%m.%d"),
                            '상담내역': consultation_content,
                            '프로젝트명': project_name if project_name else None
                        }
                        
                        success, message = insert_new_consultation(conn, consultation_data)
                        if success:
                            st.success(message)
                            clear_all_caches()
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("기업명과 상담 내역은 필수 입력 사항입니다.")
            
            with col2:
                if st.button("🔄 입력 초기화"):
                    st.rerun()
            
            with col3:
                st.write("**💡 팁:** 기존에 등록된 기업명이나 고객명을 선택하면 자동으로 연결됩니다.")
        
        else:
            st.warning("⚠️ 등록된 기업이 없습니다. 먼저 '기업 목록 관리'에서 기업을 등록해주세요.")
            
    except Exception as e:
        st.error(f"상담 추가 모드 오류: {str(e)}")
    
    # 최근 상담 이력 표시
    show_recent_consultations(conn)


def show_recent_consultations(conn, limit=10):
    """최근 상담 이력 표시"""
    st.markdown("---")
    st.subheader(f"📋 최근 상담 이력 (최근 {limit}건)")
    
    try:
        recent_consultations = pd.read_sql_query(f'''
            SELECT 
                c.company_name as 기업명,
                con.customer_name as 고객명,
                con.consultation_date as 상담날짜,
                con.consultation_content as 상담내역,
                con.project_name as 프로젝트명,
                con.created_at as 등록일시
            FROM consultations con
            JOIN companies c ON con.company_code = c.company_code
            ORDER BY con.created_at DESC
            LIMIT {limit}
        ''', conn)
        
        if not recent_consultations.empty:
            st.dataframe(recent_consultations, use_container_width=True)
        else:
            st.info("최근 상담 이력이 없습니다.")
            
    except Exception as e:
        st.error(f"최근 상담 이력 조회 오류: {str(e)}")


def show_download_page(conn):
    """데이터 다운로드 페이지"""
    st.header("💾 데이터 다운로드")
    
    # 다운로드 옵션
    download_option = st.selectbox(
        "다운로드할 데이터 선택",
        ["통합 데이터", "기업 목록", "고객 연락처", "상담 이력"]
    )
    
    try:
        if download_option == "통합 데이터":
            show_integrated_download(conn)
        elif download_option == "기업 목록":
            show_companies_download(conn)
        elif download_option == "고객 연락처":
            show_contacts_download(conn)
        elif download_option == "상담 이력":
            show_consultations_download(conn)
        
        # 전체 데이터 백업
        show_full_backup_download(conn)
        
    except Exception as e:
        st.error(f"다운로드 준비 중 오류: {str(e)}")


def show_integrated_download(conn):
    """통합 데이터 다운로드"""
    st.subheader("📊 통합 데이터 다운로드")
    
    integrated_df = get_integrated_data(conn)
    
    if not integrated_df.empty:
        st.dataframe(integrated_df.head(), use_container_width=True)
        st.info(f"총 {len(integrated_df)}개의 레코드가 있습니다.")
        
        excel_data = create_excel_file({"통합데이터": integrated_df})
        
        st.download_button(
            label="📥 통합 데이터 엑셀 다운로드",
            data=excel_data,
            file_name=generate_download_filename("통합데이터"),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("다운로드할 데이터가 없습니다.")


def show_companies_download(conn):
    """기업 목록 다운로드"""
    st.subheader("🏢 기업 목록 다운로드")
    
    companies_df = get_companies_data(conn)
    
    if not companies_df.empty:
        st.dataframe(companies_df.head(), use_container_width=True)
        st.info(f"총 {len(companies_df)}개의 기업이 있습니다.")
        
        excel_data = create_excel_file({"기업목록": companies_df})
        
        st.download_button(
            label="📥 기업 목록 엑셀 다운로드",
            data=excel_data,
            file_name=generate_download_filename("기업목록"),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("다운로드할 기업 목록이 없습니다.")


def show_contacts_download(conn):
    """고객 연락처 다운로드"""
    st.subheader("👥 고객 연락처 다운로드")
    
    contacts_df = get_contacts_data(conn)
    
    if not contacts_df.empty:
        st.dataframe(contacts_df.head(), use_container_width=True)
        st.info(f"총 {len(contacts_df)}개의 연락처가 있습니다.")
        
        excel_data = create_excel_file({"고객연락처": contacts_df})
        
        st.download_button(
            label="📥 고객 연락처 엑셀 다운로드",
            data=excel_data,
            file_name=generate_download_filename("고객연락처"),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("다운로드할 연락처가 없습니다.")


def show_consultations_download(conn):
    """상담 이력 다운로드"""
    st.subheader("📞 상담 이력 다운로드")
    
    consultations_df = get_consultations_data(conn)
    
    if not consultations_df.empty:
        st.dataframe(consultations_df.head(), use_container_width=True)
        st.info(f"총 {len(consultations_df)}개의 상담 이력이 있습니다.")
        
        excel_data = create_excel_file({"상담이력": consultations_df})
        
        st.download_button(
            label="📥 상담 이력 엑셀 다운로드",
            data=excel_data,
            file_name=generate_download_filename("상담이력"),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("다운로드할 상담 이력이 없습니다.")


def show_full_backup_download(conn):
    """전체 데이터 백업 다운로드"""
    st.markdown("---")
    st.subheader("💾 전체 데이터 백업")
    st.write("모든 데이터를 하나의 엑셀 파일로 다운로드합니다.")
    
    if st.button("전체 데이터 백업 다운로드"):
        try:
            # 모든 테이블 데이터 가져오기
            companies_df = get_companies_data(conn)
            contacts_df = get_contacts_data(conn)
            consultations_df = get_consultations_data(conn)
            integrated_df = get_integrated_data(conn)
            
            # 다중 시트 엑셀 파일 생성
            backup_data = {
                "통합데이터": integrated_df,
                "기업목록": companies_df,
                "고객연락처": contacts_df,
                "상담이력": consultations_df
            }
            
            excel_backup = create_excel_file(backup_data)
            
            st.download_button(
                label="📥 전체 데이터 백업 다운로드",
                data=excel_backup,
                file_name=generate_download_filename("CRM_전체백업"),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        except Exception as e:
            st.error(f"백업 생성 중 오류: {str(e)}")
