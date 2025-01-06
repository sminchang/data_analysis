import pandas as pd  #pip install pandas, #pip install openpyxl
from PyPDF2 import PdfReader, PdfWriter  # pip install PyPDF2
import os
import traceback

# 엑셀 파일 읽어오기 함수
def read_from_excel(excel_file):
    # 엑셀 파일 읽기
    df = pd.read_excel(excel_file)
    # 결과를 저장할 리스트
    results = []
    # 엑셀 행 단위로 순회하며, 지정된 열 값 추출
    for index, row in df.iterrows():
        row_data = row.to_dict()
        codeNm = row_data['CODE']
        start_p = row_data['시작페이지']
        end_p = row_data['종료페이지']
        row_dict = {
                'CODE': codeNm,
                '시작페이지': start_p,
                '종료페이지': end_p
            }
        results.append(row_dict)
    return results


# PDF 파일 생성 함수
def save_pdf_file(output_path: str, file_name: str, pdf_writer: PdfWriter):
    output_file = os.path.join(output_path, f"{file_name}.pdf")
    with open(output_file, 'wb') as output:
        pdf_writer.write(output)

# 엑셀 페이지 번호를 기준으로 페이지를 분할하는 함수
def pdf_division(input_path, output_path, results):
    # output 폴더가 없으면 생성
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # 폴더 내 모든 파일 순회
    for file_name in os.listdir(input_path):
        if file_name.endswith('.pdf'):
            # 파일 경로 설정
            file_path = os.path.join(input_path, file_name)

            try:
                # PyPDF2로 파일 열기
                pdf_reader = PdfReader(file_path)
                pdf_writer = PdfWriter()
                total_pages = len(pdf_reader.pages)
                
                # 파일 내 모든 페이지 순회 ,page_num은 0부터 시작한다.
                for page_num in range(total_pages):
                        pdf_writer.add_page(pdf_reader.pages[page_num])
                        for item in results:
                            
                            if (page_num+1) == item['시작페이지']:
                                start = item['시작페이지']
                                end = item['종료페이지']
                                if start == end:
                                    save_pdf_file(output_path, f"{item['CODE']}", pdf_writer)
                                    pdf_writer = PdfWriter()
                                    break

                            elif (page_num+1) == item['종료페이지']:
                                save_pdf_file(output_path, f"{item['CODE']}", pdf_writer)
                                pdf_writer = PdfWriter()
                                break

            except Exception as e:
                print(f"error: {str(e)} in file: {file_name}")
                traceback.print_exc()


excel_file = r"C:\Users\User\Desktop\통합_경기도_세부사업설명서_일반회계및특별회계(예산서기준).xlsx"
input_path = r"C:\Users\User\Desktop\경기도 지방재정"
output_path = r"C:\Users\User\Desktop\경기도 2023"
results = read_from_excel(excel_file)
pdf_division(input_path, output_path, results)

