"""
pages/company_page.py

기업 목록 관리 페이지
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

from database.operations import (
    get_companies_data, 
    insert_company_batch, 
    clear_all_caches,
    get_industries
)
from database.connection import parse_revenue, generate_company_code
from utils.file_handlers import process_excel_file


def show_page(conn):
    """기업 목록 관리 페이지 표시"""
    st.header("📋 기업 목록 관리")
    
    tab1, tab2 = st.tabs(["엑셀 업로드", "현재 기업 목록"])
    
    with tab1:
        show_upload_section(conn)
    
    with tab2:
        show_current_companies(conn)


def show_upload_section(conn):
    """엑셀 업로드 섹션"""
    st.subheader("기업 목록 엑셀 업로드")
    uploaded_file = st.file_uploader(
        "기업 목록 엑셀 파일을 업로드하세요",
        type=['xlsx', 'xls'],
        key="company_upload"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            st.success("✅ 파일을 성공적으로 읽었습니다!")
            
            # 데이터 미리보기
            st.subheader("업로드된 데이터 미리보기")
            st.dataframe(df, use_container_width=True)
            
            # 컬럼 매핑
            st.subheader("컬럼 매핑")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**필수 매핑**")
                company_name_col = st.selectbox("기업명 컬럼", df.columns, key="company_name_mapping")
            
            with col2:
                st.write("**선택 매핑**")
                revenue_col = st.selectbox("매출액 컬럼", ["선택안함"] + list(df.columns), key="revenue_mapping")
                industry_col = st.selectbox("업종 컬럼", ["선택안함"] + list(df.columns), key="industry_mapping")
                employee_col = st.selectbox("종업원수 컬럼", ["선택안함"] + list(df.columns), key="employee_mapping")
                address_col = st.selectbox("주소 컬럼", ["선택안함"] + list(df.columns), key="address_mapping")
                products_col = st.selectbox("상품 컬럼", ["선택안함"] + list(df.columns), key="products_mapping")
                category_col = st.selectbox("고객구분 컬럼", ["선택안함"] + list(df.columns), key="category_mapping")
            
            # 업체코드 처리
            st.subheader("업체코드 설정")
            code_option = st.radio(
                "업체코드 처리 방식",
                ["자동 생성", "파일에서 가져오기"]
            )
            
            if code_option == "파일에서 가져오기":
                code_col = st.selectbox("업체코드 컬럼", df.columns, key="code_mapping")
            
            # 데이터 저장
            if st.button("데이터베이스에 저장", type="primary"):
                companies_data = []
                
                for _, row in df.iterrows():
                    company_name = row[company_name_col]
                    if pd.isna(company_name) or company_name == "":
                        continue
                    
                    # 업체코드 결정
                    if code_option == "자동 생성":
                        company_code = None  # operations에서 자동 생성
                    else:
                        company_code = row[code_col] if not pd.isna(row[code_col]) else None
                    
                    # 데이터 준비
                    company_data = {
                        'company_code': company_code,
                        'company_name': company_name,
                        'revenue_2024': parse_revenue(row[revenue_col] if revenue_col != "선택안함" else None),
                        'industry': row[industry_col] if industry_col != "선택안함" and not pd.isna(row[industry_col]) else None,
                        'employee_count': int(row[employee_col]) if employee_col != "선택안함" and not pd.isna(row[employee_col]) else None,
                        'address': row[address_col] if address_col != "선택안함" and not pd.isna(row[address_col]) else None,
                        'products': row[products_col] if products_col != "선택안함" and not pd.isna(row[products_col]) else None,
                        'customer_category': row[category_col] if category_col != "선택안함" and not pd.isna(row[category_col]) else None
                    }
                    companies_data.append(company_data)
                
                # 일괄 저장
                success, message = insert_company_batch(conn, companies_data)
                
                if success:
                    st.success(f"✅ 처리 완료! {message}")
                    clear_all_caches()
                else:
                    st.error(f"저장 중 오류 발생: {message}")
                        
        except Exception as e:
            st.error(f"파일 읽기 오류: {str(e)}")


def show_current_companies(conn):
    """현재 기업 목록 섹션"""
    st.subheader("현재 저장된 기업 목록")
    
    try:
        companies_df = get_companies_data(conn)
        
        if not companies_df.empty:
            st.dataframe(companies_df, use_container_width=True)
            
            # 통계 정보
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("총 기업 수", len(companies_df))
            with col2:
                if '업종' in companies_df.columns:
                    st.metric("업종 수", companies_df['업종'].nunique())
            with col3:
                if '매출액_2024' in companies_df.columns:
                    avg_revenue = companies_df['매출액_2024'].mean()
                    st.metric("평균 매출액", f"{avg_revenue:,.0f}" if not pd.isna(avg_revenue) else "N/A")
        else:
            st.info("저장된 기업 목록이 없습니다.")
            
    except Exception as e:
        st.error(f"데이터 조회 오류: {str(e)}")
