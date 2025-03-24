# 엑셀 파일에 pdfplumber가 인식하고 변환하는 table 형식을 출력하여 pdf의 table 구조를 분석하는데 활용

import pdfplumber #pip install pdfplumber
import pandas as pd #pip install pandas, pip install openpyxl
import os

# step1. 기본 테이블 구조를 파악하기 위해 헤더를 추출한다.

def pdf_table_extract(input_path, output_file, table_settings=None):

    excel_data = []

    # 해당 폴더 안에 있는 파일 리스트(여러 파일) 불러오기
    for file_name in os.listdir(input_path):
        file_path = os.path.join(input_path, file_name)

        if file_name.endswith('.pdf'):
            file_name = os.path.splitext(file_name)[0] # 파일명에서 확장자 제거

            try:
                # PDF 파일 열기
                with pdfplumber.open(file_path) as pdf:
                    # 페이지 단위 순회
                    for page_num, page in enumerate(pdf.pages):

                        # 기본 추출 영역 확인
                        if not os.path.exists('table_debug'):
                            os.makedirs('table_debug')
                        page.to_image().debug_tablefinder(table_settings).save(f"table_debug_img/{page_num}_debug.png")
                        
                        tables = page.extract_tables() 
                        # 테이블 단위 순회
                        for table in tables:
                            #행 단위 데이터 추출
                            for row in table:
                                excel_data.append([file_name] + row)
                            excel_data.append([]) # 테이블 간 공백 행 추가

            except Exception as e:
                print(f"오류 발생: {e}"+file_name)
                excel_data.append([file_name, "오류 발생"])

    #엑셀 저장
    df = pd.DataFrame(excel_data)
    df.to_excel(output_file, index=False, header=False)
    print(f"데이터가 {output_file}로 저장되었습니다.")

if __name__ == "__main__":
    input_path= r"C:\Users\yunis\바탕 화면\test"
    output_file = 'test_table.xlsx'

    # PDFPlumber 0.11.5 tableSettings
    table_settings = {
    # 테이블 경계 탐지 전략
    "vertical_strategy": "lines",    # 세로 경계 탐지 방식: "lines"(실제 선 사용), "text"(텍스트 정렬 패턴 사용), 
                                     # "explicit"(명시적 좌표 사용), "lines_strict"(엄격한 선 검사)
    
    "horizontal_strategy": "lines",  # 가로 경계 탐지 방식: "lines", "text", "explicit", "lines_strict"
    
    # 명시적 선 좌표 지정 (vertical_strategy 또는 horizontal_strategy가 "explicit"일 때만 사용)
    "explicit_vertical_lines": [],   # 세로선 x좌표 목록 (예: [100, 200, 300])
    "explicit_horizontal_lines": [], # 가로선 y좌표 목록 (예: [50, 150, 250])
    
    # 비슷한 위치의 선을 하나로 합치는 허용 오차
    "snap_tolerance": 3,             # 기본 허용 오차(픽셀 단위). 값이 클수록 더 많은 선이 병합됨
    "snap_x_tolerance": 3,           # x축(가로) 방향 특정 허용 오차
    "snap_y_tolerance": 3,           # y축(세로) 방향 특정 허용 오차
    
    # 끊어진 선 조각을 연결하는 허용 오차
    "join_tolerance": 3,             # 기본 연결 허용 오차. 값이 클수록 더 멀리 떨어진 선 조각도 연결됨
    "join_x_tolerance": 3,           # x축 방향 특정 연결 허용 오차
    "join_y_tolerance": 3,           # y축 방향 특정 연결 허용 오차
    
    # 선 교차점 판별 허용 오차
    "intersection_tolerance": 3,     # 기본 교차점 허용 오차. 값이 클수록 약간 어긋난 교차점도 인식
    "intersection_x_tolerance": 3,   # x축 방향 교차점 허용 오차
    "intersection_y_tolerance": 3,   # y축 방향 교차점 허용 오차
    
    # 테이블 경계 인식 조건
    "edge_min_length": 3,            # 테이블 경계로 인정할 최소 선 길이. 작을수록 더 짧은 선도 경계로 인식
    
    # 텍스트 기반 경계 설정 (text 전략 사용 시)
    "min_words_vertical": 3,         # 세로 경계로 인식하기 위한 최소 단어 수. 작을수록 더 많은 열 생성
    "min_words_horizontal": 1,       # 가로 경계로 인식하기 위한 최소 단어 수. 작을수록 더 많은 행 생성
    
    # 텍스트 관련 추가 설정(필요시 추가)
    # "text_settings":           
    }

    pdf_table_extract(input_path, output_file, table_settings)
