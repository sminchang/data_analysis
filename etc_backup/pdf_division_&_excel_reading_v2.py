import pandas as pd
from PyPDF2 import PdfReader, PdfWriter
import os
import traceback

# 엑셀 파일 읽어오기 함수
def read_from_excel(excel_file):
    try:
        df = pd.read_excel(excel_file)
        results = []
        for index, row in df.iterrows():
            row_data = row.to_dict()
            file_name = row_data['파일명']  # 파일명 컬럼 추가
            code_nm = row_data['CODE']
            start_p = int(row_data['시작페이지'])
            end_p = int(row_data['종료페이지'])
            row_dict = {
                '파일명': file_name,  # 파일명 컬럼 추가
                'CODE': code_nm,
                '시작페이지': start_p,
                '종료페이지': end_p
            }
            results.append(row_dict)
        return results
    except Exception as e:
        print(f"엑셀 파일 읽기 오류: {e}")
        traceback.print_exc()
        return None

# PDF 파일 생성 함수
def save_pdf_file(output_path: str, file_name: str, pdf_writer: PdfWriter):
    try:
        output_file = os.path.join(output_path, f"{file_name}.pdf")
        with open(output_file, 'wb') as output:
            pdf_writer.write(output)
        print(f"파일 저장 성공: {output_file}")
    except Exception as e:
        print(f"PDF 파일 저장 오류: {e}")
        traceback.print_exc()

# 엑셀 페이지 번호를 기준으로 페이지를 분할하는 함수
def pdf_division(input_path, output_path, results):
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    for item in results:
        target_file_name = item['파일명'] +'.PDF' # 엑셀 파일명에 .pdf 확장자 추가
        found_file = None

        # 입력 폴더에서 엑셀 파일명과 일치하는 파일 찾기
        for file_name in os.listdir(input_path):
            print(file_name)
            if file_name == target_file_name:
                found_file = file_name
                break

        if not found_file:
            print(f"경고: {target_file_name} 파일을 찾을 수 없습니다.")
            continue

        file_path = os.path.join(input_path, found_file)

        try:
            pdf_reader = PdfReader(file_path)
            total_pages = len(pdf_reader.pages)

            start_page = item['시작페이지'] - 1  # 엑셀은 1부터 시작, PDF는 0부터 시작
            end_page = item['종료페이지'] - 1

            if start_page < 0 or end_page >= total_pages or start_page > end_page:
                print(f"경고: {item['CODE']} - 잘못된 페이지 번호 ({start_page+1}-{end_page+1}), 파일 {found_file} 건너뜀")
                continue
                
            pdf_writer = PdfWriter()  # 항목마다 새로운 PdfWriter 생성
            for page_num in range(start_page, end_page + 1):
                pdf_writer.add_page(pdf_reader.pages[page_num])

            save_pdf_file(output_path, f"{item['CODE']}_{os.path.splitext(found_file)[0]}", pdf_writer)
            # pdf_writer = PdfWriter() # 저장 후 초기화

        except Exception as e:
            print(f"파일 처리 오류: {found_file}, 오류: {e}")
            traceback.print_exc()

# 실행
excel_file = r"C:\Users\yunis\OneDrive - 씨지인사이드\task\국감\국감_분할_공수조사.xlsx"
input_path = r"C:\Users\yunis\OneDrive - 씨지인사이드\task\국감\2023_정부시정및처리결과 보고서"
output_path = r"C:\Users\yunis\바탕 화면\test"

results = read_from_excel(excel_file)

if results:
    pdf_division(input_path, output_path, results)