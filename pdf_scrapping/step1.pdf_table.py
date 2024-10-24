# 엑셀 파일에 pdfplumber가 인식하고 변환하는 table 형식을 출력하여 pdf의 table 구조를 분석하는데 활용

import pdfplumber #pip install pdfplumber
import pandas as pd #pip install pandas, pip install openpyxl
import os


excel_data = []

def pdf_table_extension(input_path, output_file):

    # 해당 폴더 안에 있는 파일 리스트 불러오기
    for file_name in os.listdir(input_path):
        file_path = os.path.join(input_path, file_name)

        if file_name.endswith('.pdf'):
            file_name = os.path.splitext(file_name)[0] # 파일명에서 확장자 제거

            try:
                # PDF 파일 열기
                with pdfplumber.open(file_path) as pdf:
                    pages = pdf.pages
                    # 페이지 단위 순회
                    for page in pages:
                        tables = page.extract_tables() 
                        # 테이블 단위 순회
                        for table in tables:
                            #행 단위 데이터 추출
                            for row in table:
                                excel_data.append([file_name] + row)

            except Exception as e:
                print(f"오류 발생: {e}"+file_name)
                excel_data.append([file_name], "오류 발생")

    #엑셀 저장
    df = pd.DataFrame(excel_data)
    df.to_excel(output_file, index=False, header=False)
    print(f"데이터가 {output_file}로 저장되었습니다.")


# 폴더 경로 지정하기
input_path= r'C:\python\pdf_python\test'
output_file = 'table_2024.xlsx'
pdf_table_extension(input_path, output_file)
