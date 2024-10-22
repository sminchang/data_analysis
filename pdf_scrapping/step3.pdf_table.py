# 다양한 표 형식으로 테스트해보지는 않았지만 표 추출에 있어 pdfminer보다 pdfplumber가 간단하고 성능이 좋았다.

import pdfplumber
import pandas as pd
import re

def extract_table_data(pdf_path, output_file):
    data = []

    # PDF 파일 열기
    with pdfplumber.open(pdf_path) as pdf:
        # 페이지를 반복합니다
        for page_num, page in pdf.pages:
            # 페이지에서 텍스트 추출
            text = page.extract_text()

            # "소요재원"이 포함된 섹션 추출
            if "소요재원" in text:
                # 정규 표현식을 사용하여 세부사업 번호 추출
                title_numbers = re.findall(r'세부사업:\s*([^\n]*)', text)

                # 페이지에서 테이블 추출
                tables = page.extract_tables()

                for table in tables:
                    #테이블별 행 단위로 데이터 추출
                    for row in table:
                        # 세부사업 번호가 있는 경우 마지막으로 찾은 번호 사용
                        if title_numbers:
                            title_number = title_numbers[-1]
                        else:
                            title_number = "N/A: P{page_num}"  # 세부사업 번호가 없는 경우 페이지 번호 사용
                        # 세부사업 번호를 행에 추가
                        data.append([title_number] + row)

            else:   # 오버페이징되어 테이블만 있는 경우, 직전 세부사업 번호를 가져와서 행 생성
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if title_numbers:
                            title_number = title_numbers[-1]
                        else:
                            title_number = "N/A: P{page_num}"
                        data.append([title_number] + row)

    # 데이터프레임으로 변환하고 엑셀로 저장
    columns = ['세부사업 번호', '재 원 별', '계', '기투자', '2024년', '2025년', '2026년', '2027년', '2028년', '향후투자', '연평균증가율']  # 컬럼 이름 설정
    df = pd.DataFrame(data, columns=columns)
    df.to_excel(output_file, index=False)

    print(f"데이터가 '{output_file}'에 저장되었습니다.")


pdf_path = '2024_사업별 세부설명자료.pdf'
output_file = 'extracted_table_2024.xlsx'

extract_table_data(pdf_path, output_file)

