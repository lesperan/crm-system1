"""
database/operations.py

데이터베이스 CRUD 작업 및 비즈니스 로직
"""

import streamlit as st
import sqlite3
import pandas as pd
from .connection import generate_company_code, parse_revenue, get_writable_connection


# 자동완성용 데이터 가져오기 함수들
@st.cache_data(ttl=300)  # 5분간 캐시
def get_company_names():
    """기업명 목록 가져오기"""
    try:
        conn = sqlite3.connect('crm_database.db', check_same_thread=False)
        cursor = conn.execute("SELECT DISTINCT company_name FROM companies WHERE company_name IS NOT NULL ORDER BY company_name")
        result = [row[0] for row in cursor.fetchall()]
        conn.close()
        return result
    except:
        return []


@st.cache_data(ttl=300)  # 5분간 캐시
def get_customer_names():
    """고객명 목록 가져오기"""
    try:
        conn = sqlite3.connect('crm_database.db', check_same_thread=False)
        cursor = conn.execute("SELECT DISTINCT customer_name FROM customer_contacts WHERE customer_name IS NOT NULL ORDER BY customer_name")
        result = [row[0] for row in cursor.fetchall()]
        conn.close()
        return result
    except:
        return []


@st.cache_data(ttl=300)  # 5분간 캐시
def get_industries():
    """업종 목록 가져오기"""
    try:
        conn = sqlite3.connect('crm_database.db', check_same_thread=False)
        cursor = conn.execute("SELECT DISTINCT industry FROM companies WHERE industry IS NOT NULL ORDER BY industry")
        result = [row[0] for row in cursor.fetchall()]
        conn.close()
        return result
    except:
        return []


@st.cache_data(ttl=300)  # 5분간 캐시
def get_positions():
    """직위 목록 가져오기"""
    try:
        conn = sqlite3.connect('crm_database.db', check_same_thread=False)
        cursor = conn.execute("SELECT DISTINCT position FROM customer_contacts WHERE position IS NOT NULL ORDER BY position")
        result = [row[0] for row in cursor.fetchall()]
        conn.close()
        return result
    except:
        return []


# 기업 관련 작업
def find_company_code(conn, company_name):
    """기업명으로 업체코드를 찾고, 없으면 새로 생성"""
    cursor = conn.execute("SELECT company_code FROM companies WHERE company_name = ?", (company_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        # 새로운 업체코드 생성
        new_code = generate_company_code()
        return new_code


def update_company_data(conn, company_code, updated_data):
    """기업 데이터 업데이트"""
    try:
        conn.execute('''
            UPDATE companies SET 
            company_name = ?, revenue_2024 = ?, industry = ?, 
            employee_count = ?, address = ?, products = ?, 
            customer_category = ?, updated_at = CURRENT_TIMESTAMP
            WHERE company_code = ?
        ''', (
            updated_data.get('기업명'),
            parse_revenue(updated_data.get('매출액_2024')),
            updated_data.get('업종'),
            int(updated_data.get('종업원수')) if updated_data.get('종업원수') else None,
            updated_data.get('주소'),
            updated_data.get('상품'),
            updated_data.get('고객구분'),
            company_code
        ))
        return True, "기업 정보가 업데이트되었습니다."
    except Exception as e:
        return False, f"업데이트 실패: {str(e)}"


def insert_company_batch(conn, companies_data):
    """기업 데이터 일괄 삽입"""
    try:
        success_count = 0
        update_count = 0
        
        for company_data in companies_data:
            company_name = company_data.get('company_name')
            if not company_name:
                continue
            
            # 업체코드 결정
            company_code = company_data.get('company_code')
            if not company_code:
                company_code = find_company_code(conn, company_name)
                if company_code.startswith("AUTO"):
                    company_code = generate_company_code()
            
            # 기존 데이터 확인
            existing = conn.execute("SELECT company_code FROM companies WHERE company_code = ?", (company_code,)).fetchone()
            
            if existing:
                # 업데이트
                conn.execute('''
                    UPDATE companies SET 
                    company_name = ?, revenue_2024 = ?, industry = ?, 
                    employee_count = ?, address = ?, products = ?, 
                    customer_category = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE company_code = ?
                ''', (
                    company_name,
                    company_data.get('revenue_2024'),
                    company_data.get('industry'),
                    company_data.get('employee_count'),
                    company_data.get('address'),
                    company_data.get('products'),
                    company_data.get('customer_category'),
                    company_code
                ))
                update_count += 1
            else:
                # 신규 삽입
                conn.execute('''
                    INSERT INTO companies 
                    (company_code, company_name, revenue_2024, industry, employee_count, address, products, customer_category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    company_code,
                    company_name,
                    company_data.get('revenue_2024'),
                    company_data.get('industry'),
                    company_data.get('employee_count'),
                    company_data.get('address'),
                    company_data.get('products'),
                    company_data.get('customer_category')
                ))
                success_count += 1
        
        return True, f"신규 저장: {success_count}개, 업데이트: {update_count}개"
    except Exception as e:
        return False, f"일괄 처리 실패: {str(e)}"


# 연락처 관련 작업
def insert_contact_batch(conn, contacts_data):
    """연락처 데이터 일괄 삽입"""
    try:
        success_count = 0
        
        for contact_data in contacts_data:
            company_name = contact_data.get('company_name')
            customer_name = contact_data.get('customer_name')
            
            if not company_name or not customer_name:
                continue
            
            # 기업 코드 찾기
            company_code = find_company_code(conn, company_name)
            
            # 기업이 없으면 기본 정보로 생성
            existing_company = conn.execute("SELECT company_code FROM companies WHERE company_code = ?", (company_code,)).fetchone()
            if not existing_company:
                conn.execute('''
                    INSERT INTO companies (company_code, company_name)
                    VALUES (?, ?)
                ''', (company_code, company_name))
            
            # 연락처 저장
            conn.execute('''
                INSERT INTO customer_contacts 
                (company_code, customer_name, position, phone, email, acquisition_path)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                company_code,
                customer_name,
                contact_data.get('position'),
                contact_data.get('phone'),
                contact_data.get('email'),
                contact_data.get('acquisition_path')
            ))
            success_count += 1
        
        return True, f"{success_count}개의 연락처를 저장했습니다!"
    except Exception as e:
        return False, f"연락처 저장 실패: {str(e)}"


# 상담 이력 관련 작업
def insert_new_consultation(conn, consultation_data):
    """새로운 상담 이력 추가"""
    try:
        # 기업명으로 기업코드 찾기 또는 생성
        company_name = consultation_data.get('기업명')
        company_code = find_company_code(conn, company_name)
        
        # 기업이 없으면 기본 정보로 생성
        existing_company = conn.execute("SELECT company_code FROM companies WHERE company_code = ?", (company_code,)).fetchone()
        if not existing_company:
            conn.execute('''
                INSERT INTO companies (company_code, company_name)
                VALUES (?, ?)
            ''', (company_code, company_name))
        
        # 상담 이력 추가
        conn.execute('''
            INSERT INTO consultations 
            (company_code, customer_name, consultation_date, consultation_content, project_name)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            company_code,
            consultation_data.get('고객명'),
            consultation_data.get('상담날짜'),
            consultation_data.get('상담내역'),
            consultation_data.get('프로젝트명')
        ))
        return True, "새로운 상담 이력이 추가되었습니다."
    except Exception as e:
        return False, f"추가 실패: {str(e)}"


def insert_consultation_batch(conn, consultations_data):
    """상담 이력 데이터 일괄 삽입"""
    try:
        success_count = 0
        
        for consultation_data in consultations_data:
            company_name = consultation_data.get('company_name')
            consultation_content = consultation_data.get('consultation_content')
            
            if not company_name or not consultation_content:
                continue
            
            # 기업 코드 찾기
            company_code = find_company_code(conn, company_name)
            
            # 기업이 없으면 기본 정보로 생성
            existing_company = conn.execute("SELECT company_code FROM companies WHERE company_code = ?", (company_code,)).fetchone()
            if not existing_company:
                conn.execute('''
                    INSERT INTO companies (company_code, company_name)
                    VALUES (?, ?)
                ''', (company_code, company_name))
            
            # 상담 이력 저장
            conn.execute('''
                INSERT INTO consultations 
                (company_code, customer_name, consultation_date, consultation_content, project_name)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                company_code,
                consultation_data.get('customer_name'),
                consultation_data.get('consultation_date'),
                consultation_content,
                consultation_data.get('project_name')
            ))
            success_count += 1
        
        return True, f"{success_count}개의 상담 이력을 저장했습니다!"
    except Exception as e:
        return False, f"상담 이력 저장 실패: {str(e)}"


# 조회 관련 작업
def get_companies_data(conn):
    """기업 데이터 조회"""
    return pd.read_sql_query('''
        SELECT 
            company_code as 업체코드,
            company_name as 기업명,
            revenue_2024 as 매출액_2024,
            industry as 업종,
            employee_count as 종업원수,
            address as 주소,
            products as 상품,
            customer_category as 고객구분,
            created_at as 등록일,
            updated_at as 수정일
        FROM companies 
        ORDER BY company_name
    ''', conn)


def get_contacts_data(conn):
    """연락처 데이터 조회"""
    return pd.read_sql_query('''
        SELECT 
            c.company_name as 기업명,
            c.company_code as 업체코드,
            cc.customer_name as 고객명,
            cc.position as 직위,
            cc.phone as 전화,
            cc.email as 이메일,
            cc.acquisition_path as 획득경로,
            cc.created_at as 등록일,
            cc.updated_at as 수정일
        FROM customer_contacts cc
        JOIN companies c ON cc.company_code = c.company_code
        ORDER BY c.company_name, cc.customer_name
    ''', conn)


def get_consultations_data(conn):
    """상담 이력 데이터 조회"""
    return pd.read_sql_query('''
        SELECT 
            c.company_name as 기업명,
            c.company_code as 업체코드,
            con.customer_name as 고객명,
            con.consultation_date as 상담날짜,
            con.consultation_content as 상담내역,
            con.project_name as 프로젝트명,
            con.created_at as 등록일,
            con.updated_at as 수정일
        FROM consultations con
        JOIN companies c ON con.company_code = c.company_code
        ORDER BY con.consultation_date DESC, c.company_name
    ''', conn)


def get_integrated_data(conn):
    """통합 데이터 조회"""
    return pd.read_sql_query('''
        SELECT 
            c.company_name as 기업명,
            c.revenue_2024 as 매출액_2024,
            c.industry as 업종,
            c.employee_count as 종업원수,
            c.address as 주소,
            c.products as 상품,
            c.customer_category as 고객구분,
            cc.customer_name as 고객명,
            cc.position as 직위,
            cc.phone as 전화,
            cc.email as 이메일,
            cc.acquisition_path as 획득경로,
            con.consultation_date as 상담날짜,
            con.consultation_content as 상담내역,
            con.project_name as 프로젝트명
        FROM companies c
        LEFT JOIN customer_contacts cc ON c.company_code = cc.company_code
        LEFT JOIN consultations con ON c.company_code = con.company_code
        ORDER BY c.company_name, con.consultation_date DESC
    ''', conn)


# 편집 관련 작업
def save_edited_companies(conn, edited_df, original_df):
    """편집된 기업 데이터 저장"""
    try:
        write_conn = get_writable_connection()
        changes_count = 0
        errors = []
        
        # 원본과 편집된 데이터 비교
        for idx, (original_row, edited_row) in enumerate(zip(original_df.itertuples(), edited_df.itertuples())):
            # 변경사항이 있는지 확인
            if not original_row[1:] == edited_row[1:]:  # 인덱스 제외하고 비교
                company_code = edited_row.업체코드
                
                # 필수 필드 검증
                if not edited_row.기업명 or edited_row.기업명.strip() == "":
                    errors.append(f"행 {idx+1}: 기업명은 필수입니다.")
                    continue
                
                # 업데이트 실행
                try:
                    write_conn.execute('''
                        UPDATE companies SET 
                        company_name = ?, revenue_2024 = ?, industry = ?, 
                        employee_count = ?, address = ?, products = ?, 
                        customer_category = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE company_code = ?
                    ''', (
                        edited_row.기업명,
                        parse_revenue(edited_row.매출액_2024),
                        edited_row.업종 if edited_row.업종 else None,
                        int(edited_row.종업원수) if edited_row.종업원수 else None,
                        edited_row.주소 if edited_row.주소 else None,
                        edited_row.상품 if edited_row.상품 else None,
                        edited_row.고객구분 if edited_row.고객구분 else None,
                        company_code
                    ))
                    changes_count += 1
                except Exception as e:
                    errors.append(f"행 {idx+1}: 업데이트 실패 - {str(e)}")
        
        # 새로 추가된 행 처리
        if len(edited_df) > len(original_df):
            for idx in range(len(original_df), len(edited_df)):
                new_row = edited_df.iloc[idx]
                
                if new_row['기업명'] and new_row['기업명'].strip():
                    try:
                        # 새 업체코드 생성
                        new_company_code = generate_company_code()
                        
                        # 새 기업 추가
                        write_conn.execute('''
                            INSERT INTO companies 
                            (company_code, company_name, revenue_2024, industry, employee_count, address, products, customer_category)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            new_company_code,
                            new_row['기업명'],
                            parse_revenue(new_row['매출액_2024']),
                            new_row['업종'] if new_row['업종'] else None,
                            int(new_row['종업원수']) if new_row['종업원수'] else None,
                            new_row['주소'] if new_row['주소'] else None,
                            new_row['상품'] if new_row['상품'] else None,
                            new_row['고객구분'] if new_row['고객구분'] else None
                        ))
                        changes_count += 1
                    except Exception as e:
                        errors.append(f"새 행 {idx+1}: 추가 실패 - {str(e)}")
        
        write_conn.close()
        
        return True, changes_count, errors
        
    except Exception as e:
        return False, 0, [f"전체 저장 실패: {str(e)}"]


# 캐시 클리어 함수들
def clear_all_caches():
    """모든 캐시 클리어"""
    get_company_names.clear()
    get_customer_names.clear()
    get_industries.clear()
    get_positions.clear()
