"""
utils/validators.py

데이터 검증 관련 함수들
"""

import re
import pandas as pd


def validate_company_name(company_name):
    """
    기업명 유효성 검사
    
    Args:
        company_name (str): 기업명
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not company_name or pd.isna(company_name):
        return False, "기업명은 필수입니다."
    
    company_name = str(company_name).strip()
    
    if len(company_name) == 0:
        return False, "기업명은 필수입니다."
    
    if len(company_name) > 100:
        return False, "기업명은 100자를 초과할 수 없습니다."
    
    return True, ""


def validate_email(email):
    """
    이메일 유효성 검사
    
    Args:
        email (str): 이메일 주소
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not email or pd.isna(email):
        return True, ""  # 이메일은 선택사항
    
    email = str(email).strip()
    if len(email) == 0:
        return True, ""
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        return False, "올바른 이메일 형식이 아닙니다."
    
    return True, ""


def validate_phone(phone):
    """
    전화번호 유효성 검사
    
    Args:
        phone (str): 전화번호
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not phone or pd.isna(phone):
        return True, ""  # 전화번호는 선택사항
    
    phone = str(phone).strip()
    if len(phone) == 0:
        return True, ""
    
    # 숫자, 하이픈, 괄호, 공백만 허용
    phone_clean = re.sub(r'[^\d]', '', phone)
    
    if len(phone_clean) < 9 or len(phone_clean) > 11:
        return False, "전화번호는 9-11자리 숫자여야 합니다."
    
    return True, ""


def validate_revenue(revenue):
    """
    매출액 유효성 검사
    
    Args:
        revenue: 매출액 (숫자 또는 문자열)
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not revenue or pd.isna(revenue):
        return True, ""  # 매출액은 선택사항
    
    try:
        # 문자열인 경우 쉼표 제거 후 숫자 변환
        if isinstance(revenue, str):
            revenue_clean = revenue.replace(',', '').replace(' ', '')
            revenue_num = float(revenue_clean)
        else:
            revenue_num = float(revenue)
        
        if revenue_num < 0:
            return False, "매출액은 0 이상이어야 합니다."
        
        if revenue_num > 999999999999:  # 1조 이상
            return False, "매출액이 너무 큽니다."
        
        return True, ""
        
    except (ValueError, TypeError):
        return False, "올바른 숫자 형식이 아닙니다."


def validate_employee_count(count):
    """
    종업원수 유효성 검사
    
    Args:
        count: 종업원수 (숫자 또는 문자열)
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not count or pd.isna(count):
        return True, ""  # 종업원수는 선택사항
    
    try:
        count_num = int(float(count))
        
        if count_num < 0:
            return False, "종업원수는 0 이상이어야 합니다."
        
        if count_num > 1000000:  # 100만명 이상
            return False, "종업원수가 너무 큽니다."
        
        return True, ""
        
    except (ValueError, TypeError):
        return False, "올바른 숫자 형식이 아닙니다."


def validate_consultation_content(content):
    """
    상담 내용 유효성 검사
    
    Args:
        content (str): 상담 내용
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not content or pd.isna(content):
        return False, "상담 내용은 필수입니다."
    
    content = str(content).strip()
    
    if len(content) == 0:
        return False, "상담 내용은 필수입니다."
    
    if len(content) < 5:
        return False, "상담 내용은 최소 5자 이상 입력해주세요."
    
    if len(content) > 2000:
        return False, "상담 내용은 2000자를 초과할 수 없습니다."
    
    return True, ""


def validate_batch_data(data_list, validators_dict):
    """
    일괄 데이터 유효성 검사
    
    Args:
        data_list (list): 검사할 데이터 리스트
        validators_dict (dict): {필드명: 검증함수} 딕셔너리
        
    Returns:
        tuple: (is_valid, error_list)
    """
    errors = []
    
    for idx, data in enumerate(data_list):
        row_errors = []
        
        for field_name, validator_func in validators_dict.items():
            if field_name in data:
                is_valid, error_msg = validator_func(data[field_name])
                if not is_valid:
                    row_errors.append(f"{field_name}: {error_msg}")
        
        if row_errors:
            errors.append(f"행 {idx+1}: {', '.join(row_errors)}")
    
    return len(errors) == 0, errors
