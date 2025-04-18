# spire.pdf는 정확도가 높지만 유료 API로 무료 버전에서는 페이지 갯수가 제한되어있다.

# PyMuPDF, PyPDF2는 텍스트 내 공백 문자를 생략해버리는 문제가 있어 사용하지 않았다.
# PyMuPDF는 텍스트 내 개행 문자를 기준으로 개행하는 것으로 보인다.
# PyPDF2는 페이지 레이아웃을 기준으로 개행하는 것으로 보인다.

# pdfplumber, pdfminer가 원본 형식을 가장 잘 살렸다.
# pdfminber는 연속된 공백 문자를 개행 문자로 처리해버리는데 간혹 여기서 텍스트 순서도 뒤엉킨다.
# pdfplumber는 개행 문자를 식별하는 부분에서 pdfminer보다 부정확할 때가 생긴다.
# 결론적으로 pdfplumber와 pdfminer로 각각 추출 후 교차 검증을 하는 방식으로 처리하기로 했다.


import pdfplumber #pip install pdfplumber
import os

def pdf_to_text(input_path, output_file_path):

    # 해당 폴더 안에 있는 파일 리스트(여러 파일) 불러오기
    for file_name in os.listdir(input_path):
        file_path = os.path.join(input_path, file_name)
            
        with pdfplumber.open(file_path) as pdf:
            text = ""

            for page in pdf.pages:
                text += page.extract_text() #+ "\n"  # 각 페이지의 텍스트를 추가하고 줄바꿈

        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write(text)
            # file.write(left_text)
            # file.write(right_text)

        print(f"텍스트가 '{output_file_path}'에 저장되었습니다.")


input_path = r"C:\Users\yunis\바탕 화면\test1"
output_file_path = 'output_pdfplumber.txt'

pdf_to_text(input_path, output_file_path)

#--------------------------------------------------------------------

# from pdfminer.high_level import extract_text #pip install pdfminer.six
# import os

# def pdf_to_text(input_path, output_file_path):

#         # 해당 폴더 안에 있는 파일 리스트(여러 파일) 불러오기
#     for file_name in os.listdir(input_path):
#         file_path = os.path.join(input_path, file_name)

#         # PDF 파일에서 텍스트 추출
#         text = extract_text(file_path)
        
#         # 추출한 텍스트를 텍스트 파일로 저장
#         with open(output_file_path, 'w', encoding='utf-8') as file:
#             file.write(text)

#         print(f"텍스트가 '{output_file_path}'에 저장되었습니다.")


# # 추출할 PDF 폴더 경로, 저장할 파일 경로
# input_path = r"C:\Users\yunis\바탕 화면\test"
# output_file_path = 'output_pdfminer.txt'

# #실행
# pdf_to_text(input_path, output_file_path)

#--------------------------------------------------------------------

# import fitz # pip install PyMuPDF
# import os

# def pdf_to_text(input_path, output_file_path):

#     # 해당 폴더 안에 있는 파일 리스트(여러 파일) 불러오기
#     for file_name in os.listdir(input_path):
#         file_path = os.path.join(input_path, file_name)

#         doc = fitz.open(file_path)
        
#         # 전체 텍스트를 저장할 변수
#         full_text = ""
        
#         # 모든 페이지에서 텍스트 추출
#         for page in doc:
#             full_text += page.get_text()
        
#         with open(output_file_path, 'w', encoding='utf-8') as f:
#             f.write(full_text)
        
#         print(f"텍스트가 '{output_file_path}'에 저장되었습니다.")


# input_path = r"C:\Users\yunis\바탕 화면\test1"
# output_file_path = 'output_pymupdf.txt'

# pdf_to_text(input_path, output_file_path)

#--------------------------------------------------------------------

# import PyPDF2 #pip install PyPDF2
# import os

# def pdf_to_text(input_path, output_file_path):

#     # 해당 폴더 안에 있는 파일 리스트(여러 파일) 불러오기
#     for file_name in os.listdir(input_path):
#         file_path = os.path.join(input_path, file_name)
 
#         with open(file_path, 'rb') as pdf_file:
#             pdf_reader = PyPDF2.PdfReader(pdf_file)
            
#             text = ''
#             for page in pdf_reader.pages:
#                 text += page.extract_text() + '\n'  # 페이지별로 텍스트 추출하여 추가

#         with open(output_file_path, 'w', encoding='utf-8') as f:
#             f.write(text)

#         print(f"텍스트가 '{output_file_path}'에 저장되었습니다.")


# input_path = r'C:\python\pdf_python\test'
# output_file_path = 'output_pypdf2.txt'

# pdf_to_text(input_path, output_file_path)
