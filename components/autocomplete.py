"""
components/autocomplete.py

자동완성 관련 컴포넌트들
"""

import streamlit as st
import sys
import os

# 상위 디렉토리를 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from database.operations import get_company_names, get_customer_names, get_industries, get_positions


def company_name_selector(key_suffix="", default_value=None):
    """
    기업명 선택 컴포넌트 (자동완성 지원)
    
    Args:
        key_suffix (str): 위젯 키 suffix
        default_value (str): 기본 선택값
        
    Returns:
        str: 선택된 기업명
    """
    company_names = get_company_names()
    
    if company_names:
        options = ["새 기업명 입력"] + company_names
        
        # 기본값이 있으면 해당 값을 선택
        if default_value and default_value in company_names:
            default_index = company_names.index(default_value) + 1  # "새 기업명 입력" 때문에 +1
        else:
            default_index = 0
        
        selected_company = st.selectbox(
            "기업명",
            options,
            index=default_index,
            key=f"company_select_{key_suffix}"
        )
        
        if selected_company == "새 기업명 입력":
            new_company_name = st.text_input(
                "새 기업명을 입력하세요",
                value=default_value if default_value and default_value not in company_names else "",
                key=f"new_company_{key_suffix}"
            )
            return new_company_name
        else:
            return selected_company
    else:
        # 등록된 기업이 없는 경우
        return st.text_input(
            "기업명",
            value=default_value or "",
            key=f"company_input_{key_suffix}"
        )


def customer_name_selector(key_suffix="", default_value=None):
    """
    고객명 선택 컴포넌트 (자동완성 지원)
    
    Args:
        key_suffix (str): 위젯 키 suffix
        default_value (str): 기본 선택값
        
    Returns:
        str: 선택된 고객명
    """
    customer_names = get_customer_names()
    
    if customer_names:
        options = ["새 고객명 입력"] + customer_names
        
        # 기본값이 있으면 해당 값을 선택
        if default_value and default_value in customer_names:
            default_index = customer_names.index(default_value) + 1
        else:
            default_index = 0
        
        selected_customer = st.selectbox(
            "고객명",
            options,
            index=default_index,
            key=f"customer_select_{key_suffix}"
        )
        
        if selected_customer == "새 고객명 입력":
            new_customer_name = st.text_input(
                "새 고객명을 입력하세요",
                value=default_value if default_value and default_value not in customer_names else "",
                key=f"new_customer_{key_suffix}"
            )
            return new_customer_name
        else:
            return selected_customer
    else:
        # 등록된 고객이 없는 경우
        return st.text_input(
            "고객명",
            value=default_value or "",
            key=f"customer_input_{key_suffix}"
        )


def industry_selector(key_suffix="", default_value=None):
    """
    업종 선택 컴포넌트 (자동완성 지원)
    
    Args:
        key_suffix (str): 위젯 키 suffix
        default_value (str): 기본 선택값
        
    Returns:
        str: 선택된 업종
    """
    industries = get_industries()
    
    if industries:
        options = [""] + industries
        
        # 기본값이 있으면 해당 값을 선택
        if default_value and default_value in industries:
            default_index = industries.index(default_value) + 1
        else:
            default_index = 0
        
        selected_industry = st.selectbox(
            "업종",
            options,
            index=default_index,
            key=f"industry_select_{key_suffix}"
        )
        
        return selected_industry if selected_industry else None
    else:
        # 등록된 업종이 없는 경우
        return st.text_input(
            "업종",
            value=default_value or "",
            key=f"industry_input_{key_suffix}"
        )


def position_selector(key_suffix="", default_value=None):
    """
    직위 선택 컴포넌트 (자동완성 지원)
    
    Args:
        key_suffix (str): 위젯 키 suffix
        default_value (str): 기본 선택값
        
    Returns:
        str: 선택된 직위
    """
    positions = get_positions()
    
    if positions:
        options = [""] + positions
        
        # 기본값이 있으면 해당 값을 선택
        if default_value and default_value in positions:
            default_index = positions.index(default_value) + 1
        else:
            default_index = 0
        
        selected_position = st.selectbox(
            "직위",
            options,
            index=default_index,
            key=f"position_select_{key_suffix}"
        )
        
        return selected_position if selected_position else None
    else:
        # 등록된 직위가 없는 경우
        return st.text_input(
            "직위",
            value=default_value or "",
            key=f"position_input_{key_suffix}"
        )


def customer_category_selector(key_suffix="", default_value=None):
    """
    고객구분 선택 컴포넌트
    
    Args:
        key_suffix (str): 위젯 키 suffix
        default_value (str): 기본 선택값
        
    Returns:
        str: 선택된 고객구분
    """
    options = ["", "신규", "기존", "잠재", "VIP"]
    
    # 기본값이 있으면 해당 값을 선택
    if default_value and default_value in options:
        default_index = options.index(default_value)
    else:
        default_index = 0
    
    selected_category = st.selectbox(
        "고객구분",
        options,
        index=default_index,
        key=f"category_select_{key_suffix}"
    )
    
    return selected_category if selected_category else None


def acquisition_path_selector(key_suffix="", default_value=None):
    """
    획득경로 선택 컴포넌트
    
    Args:
        key_suffix (str): 위젯 키 suffix
        default_value (str): 기본 선택값
        
    Returns:
        str: 선택된 획득경로
    """
    options = ["", "홈페이지", "전화", "이메일", "추천", "전시회", "세미나", "기타"]
    
    # 기본값이 있으면 해당 값을 선택
    if default_value and default_value in options:
        default_index = options.index(default_value)
    else:
        default_index = 0
    
    selected_path = st.selectbox(
        "획득경로",
        options,
        index=default_index,
        key=f"path_select_{key_suffix}"
    )
    
    return selected_path if selected_path else None
