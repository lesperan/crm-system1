"""
pages/contact_page.py

고객 연락처 관리 페이지
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
    get_contacts_data, 
    insert_contact_batch, 
    clear_all_caches
)
from components.autocomplete import (
    company_name_selector,
    customer_name_selector,
    position_selector,
    acquisition_path_selector
)
from components.data_grid import display_data_with_stats
from utils.validators import validate_email, validate_phone


def show_page(conn):
    """고객 연락처 관리 페이지 표시"""
    st.header("👥 고객 연락처 관리")
    
    tab1, tab2, tab3, tab4 = st.tabs(["엑셀 업로드", "직접 입력", "현재 연락처 목록", "🛠️ 관리"])
    
    with tab1:
        show_upload_section(conn)
    
    with tab2:
        show_direct_input_section(conn)
    
    with tab3:
        show_current_contacts(conn)
    
    with tab4:
        show_management_section(conn)


def show_management_section(conn):
    """관리 섹션"""
    st.subheader("🛠️ 연락처 데이터 관리")
    
    # 현재 상태 표시
    try:
        total_contacts = conn.execute("SELECT COUNT(*) FROM customer_contacts").fetchone()[0]
        st.metric("현재 저장된 연락처 수", total_contacts)
        
        if total_contacts > 0:
            # 최근 5개 연락처 미리보기
            recent_contacts = pd.read_sql_query('''
                SELECT cc.customer_name as 고객명, c.company_name as 기업명, cc.phone as 전화
                FROM customer_contacts cc
                JOIN companies c ON cc.company_code = c.company_code
                ORDER BY cc.created_at DESC
                LIMIT 5
            ''', conn)
            
            st.write("**최근 연락처 5개:**")
            st.dataframe(recent_contacts, use_container_width=True)
        
    except Exception as e:
        st.error(f"데이터 조회 오류: {str(e)}")
    
    st.markdown("---")
    
    # 위험한 작업 섹션
    st.subheader("⚠️ 위험한 작업")
    st.warning("아래 작업들은 되돌릴 수 없습니다. 신중하게 실행하세요.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**모든 연락처 삭제**")
        if st.button("🗑️ 모든 연락처 삭제", type="secondary"):
            if 'confirm_delete_contacts' not in st.session_state:
                st.session_state.confirm_delete_contacts = False
            
            if not st.session_state.confirm_delete_contacts:
                st.session_state.confirm_delete_contacts = True
                st.error("⚠️ 정말로 삭제하시겠습니까? 버튼을 한 번 더 클릭하세요!")
                st.rerun()
            else:
                try:
                    deleted_count = conn.execute("SELECT COUNT(*) FROM customer_contacts").fetchone()[0]
                    conn.execute("DELETE FROM customer_contacts")
                    conn.commit()
                    st.success(f"✅ {deleted_count}개의 연락처가 모두 삭제되었습니다!")
                    st.session_state.confirm_delete_contacts = False
                    clear_all_caches()
                    st.rerun()
                except Exception as e:
                    st.error(f"삭제 실패: {str(e)}")
    
    with col2:
        st.write("**전체 데이터베이스 초기화**")
        if st.button("💥 전체 DB 초기화", type="secondary"):
            if 'confirm_delete_all' not in st.session_state:
                st.session_state.confirm_delete_all = False
            
            if not st.session_state.confirm_delete_all:
                st.session_state.confirm_delete_all = True
                st.error("⚠️ 모든 데이터(기업, 연락처, 상담이력)가 삭제됩니다! 한 번 더 클릭하세요!")
                st.rerun()
            else:
                try:
                    # 모든 테이블 데이터 삭제
                    tables = ['consultations', 'customer_contacts', 'companies']
                    total_deleted = 0
                    
                    for table in tables:
                        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                        conn.execute(f"DELETE FROM {table}")
                        total_deleted += count
                    
                    conn.commit()
                    st.success(f"✅ 전체 데이터베이스가 초기화되었습니다! (총 {total_deleted}개 레코드 삭제)")
                    st.session_state.confirm_delete_all = False
                    clear_all_caches()
                    st.rerun()
                except Exception as e:
                    st.error(f"초기화 실패: {str(e)}")
    
    # 초기화 후 안내
    if total_contacts == 0:
        st.info("📝 **다음 단계:** '엑셀 업로드' 탭에서 올바른 매핑으로 연락처를 다시 업로드하세요.")


def show_upload_section(conn):
    """파일 업로드 섹션"""
    st.subheader("고객 연락처 파일 업로드")
    contact_file = st.file_uploader(
        "고객 연락처 파일을 업로드하세요 (엑셀 또는 CSV)",
        type=['xlsx', 'xls', 'csv'],
        key="contact_upload",
        help="엑셀 파일(.xlsx, .xls) 또는 CSV 파일(.csv)을 업로드할 수 있습니다."
    )
    
    if contact_file is not None:
        try:
            # 파일 형식에 따른 처리
            file_extension = contact_file.name.split('.')[-1].lower()
            
            if file_extension in ['xlsx', 'xls']:
                try:
                    df = pd.read_excel(contact_file)
                except ImportError:
                    st.error("❌ 엑셀 파일을 읽기 위해서는 openpyxl 라이브러리가 필요합니다.")
                    st.info("**해결 방법:**")
                    st.code("pip install openpyxl", language="bash")
                    st.info("**또는** 엑셀 파일을 CSV로 변환하여 업로드해 주세요.")
                    return
            elif file_extension == 'csv':
                try:
                    try:
                        df = pd.read_csv(contact_file, encoding='utf-8')
                    except UnicodeDecodeError:
                        contact_file.seek(0)
                        df = pd.read_csv(contact_file, encoding='cp949')
                except Exception as e:
                    st.error(f"CSV 파일 읽기 오류: {str(e)}")
                    return
            else:
                st.error("지원되는 파일 형식: .xlsx, .xls, .csv")
                return
            
            st.success("✅ 파일을 성공적으로 읽었습니다!")
            
            st.subheader("업로드된 데이터 미리보기")
            st.dataframe(df, use_container_width=True)
            
            # 컬럼 매핑
            st.subheader("컬럼 매핑")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**필수 매핑**")
                company_name_col = st.selectbox("기업명 컬럼", df.columns, key="contact_company_mapping")
                customer_name_col = st.selectbox("고객명 컬럼", df.columns, key="contact_customer_mapping")
            
            with col2:
                st.write("**선택 매핑**")
                position_col = st.selectbox("직위 컬럼", ["선택안함"] + list(df.columns), key="position_mapping")
                phone_col = st.selectbox("전화 컬럼", ["선택안함"] + list(df.columns), key="phone_mapping")
                email_col = st.selectbox("이메일 컬럼", ["선택안함"] + list(df.columns), key="email_mapping")
                path_col = st.selectbox("획득경로 컬럼", ["선택안함"] + list(df.columns), key="path_mapping")
            
            if st.button("연락처 저장", type="primary"):
                contacts_data = []
                
                for _, row in df.iterrows():
                    company_name = row[company_name_col]
                    customer_name = row[customer_name_col]
                    
                    if pd.isna(company_name) or pd.isna(customer_name) or company_name == "" or customer_name == "":
                        continue
                    
                    # 연락처 정보 준비
                    position = row[position_col] if position_col != "선택안함" and not pd.isna(row[position_col]) else None
                    phone = row[phone_col] if phone_col != "선택안함" and not pd.isna(row[phone_col]) else None
                    email = row[email_col] if email_col != "선택안함" and not pd.isna(row[email_col]) else None
                    acquisition_path = row[path_col] if path_col != "선택안함" and not pd.isna(row[path_col]) else None
                    
                    # 유효성 검사 (전화번호 검증 임시 비활성화)
                    email_valid, email_error = validate_email(email)
                    phone_valid, phone_error = True, ""  # 전화번호 검증 비활성화
                    
                    if not email_valid:
                        st.warning(f"행 {len(contacts_data)+1}: {email_error}")
                        continue
                    
                    # phone_valid 체크 제거
                    # if not phone_valid:
                    #     st.warning(f"행 {len(contacts_data)+1}: {phone_error}")
                    #     continue
                    
                    contact_data = {
                        'company_name': company_name,
                        'customer_name': customer_name,
                        'position': position,
                        'phone': phone,
                        'email': email,
                        'acquisition_path': acquisition_path
                    }
                    contacts_data.append(contact_data)
                
                # 일괄 저장
                success, message = insert_contact_batch(conn, contacts_data)
                
                if success:
                    st.success(f"✅ {message}")
                    clear_all_caches()
                else:
                    st.error(f"저장 중 오류 발생: {message}")
                        
        except Exception as e:
            st.error(f"파일 읽기 오류: {str(e)}")


def show_direct_input_section(conn):
    """직접 입력 섹션"""
    st.subheader("연락처 직접 입력")
    
    with st.form("contact_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**기본 정보**")
            company_name = company_name_selector("contact_form")
            customer_name = customer_name_selector("contact_form")
            position = position_selector("contact_form")
        
        with col2:
            st.write("**연락처 정보**")
            phone = st.text_input("전화번호")
            email = st.text_input("이메일")
            acquisition_path = acquisition_path_selector("contact_form")
        
        submitted = st.form_submit_button("📝 연락처 저장", type="primary")
        
        if submitted:
            # 필수 필드 검증
            if not company_name or not customer_name:
                st.error("기업명과 고객명은 필수입니다.")
                return
            
            # 유효성 검사 (전화번호 검증 임시 비활성화)
            email_valid, email_error = validate_email(email)
            phone_valid, phone_error = True, ""  # 전화번호 검증 비활성화
            
            if not email_valid:
                st.error(f"이메일 오류: {email_error}")
                return
            
            # phone_valid 체크 제거
            # if not phone_valid:
            #     st.error(f"전화번호 오류: {phone_error}")
            #     return
            
            # 연락처 저장
            contact_data = [{
                'company_name': company_name,
                'customer_name': customer_name,
                'position': position,
                'phone': phone if phone else None,
                'email': email if email else None,
                'acquisition_path': acquisition_path
            }]
            
            success, message = insert_contact_batch(conn, contact_data)
            
            if success:
                st.success(f"✅ {message}")
                clear_all_caches()
                st.rerun()
            else:
                st.error(f"저장 실패: {message}")


def show_current_contacts(conn):
    """현재 연락처 목록 섹션"""
    try:
        contacts_df = get_contacts_data(conn)
        display_data_with_stats(contacts_df, "현재 저장된 연락처 목록", "contacts")
    except Exception as e:
        st.error(f"연락처 데이터 조회 오류: {str(e)}")
