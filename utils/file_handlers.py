"""
utils/file_handlers.py

파일 처리 관련 유틸리티 함수들
"""

import pandas as pd
import io
from datetime import datetime


def process_excel_file(uploaded_file):
    """
    업로드된 엑셀 파일 처리
    
    Args:
        uploaded_file: Streamlit의 UploadedFile 객체
        
    Returns:
        pd.DataFrame: 처리된 데이터프레임
    """
    try:
        df = pd.read_excel(uploaded_file)
        return df
    except Exception as e:
        raise Exception(f"엑셀 파일 읽기 오류: {str(e)}")


def create_excel_file(dataframes_dict):
    """
    여러 시트를 가진 엑셀 파일 생성
    
    Args:
        dataframes_dict (dict): {시트명: 데이터프레임} 형태의 딕셔너리
        
    Returns:
        bytes: 엑셀 파일의 바이트 데이터
    """
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sheet_name, df in dataframes_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # 워크시트 포맷팅
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]
            
            # 헤더 포맷
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1
            })
            
            # 헤더 적용
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # 열 너비 자동 조정
            for i, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).str.len().max(),
                    len(str(col))
                )
                worksheet.set_column(i, i, min(max_length + 2, 50))
    
    return output.getvalue()


def generate_download_filename(base_name):
    """
    다운로드용 파일명 생성
    
    Args:
        base_name (str): 기본 파일명
        
    Returns:
        str: 타임스탬프가 포함된 파일명
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    return f"{base_name}_{timestamp}.xlsx"
