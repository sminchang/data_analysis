# refined data source: https://www.gg.go.kr/bbs/board.do?bsIdx=619&menuId=1765
# pdfminer는 탭 문자를 포함한 개행처리가 명확하다. 하지만 pdfplumber보다는 원본 형식을 못살린다.

import re
import os
from pdfminer.high_level import extract_text  #pip install pdfminer.six
import pandas as pd #pip install pandas, pip install openpyxl

def clean_text(text):
    # 연속된 개행 문자를 하나의 개행 문자로 대체, 한 문장이 길어져 자동개행된 경우를 원래대로 처리
    text = re.sub(r'\n{2,}', '\n', text)

    return text.strip()

def extract_text_to_file(input_path, output_file):
    data = []

    # 정규 표현식, 문건 추출 패턴
    document_pattern = r'세부사업:\s*\n([^\n]+)\s*\n([\s\S]*?)(?=\n*회계연도\s*:)'
    non_number_pattern = r'(.*?)(?=\n회계연도)' # 세부사업 번호가 없는 문건 추출 패턴
    content_patterns = {                       # 세부내용 추출 패턴
        '회계연도': r'회계연도\s*:\s*(\d{4})',
        '회계': r'회\s*계\s*:\s*(.+?)(?=\n)',
        '조직': r'조\s*직\s*:\s*(.+?)(?=\n)',
        '기능': r'기\s*능\s*:\s*(.+?)(?=\n)',
        '정책사업': r'정책사업\s*:\s*(.+?)(?=단위사업\s*|□\s*사업개요|$)',
        '단위사업': r'단위사업\s*:\s*(.+?)(?=○\s*사업목적|□\s*사업개요|$)',
        '사업목적': r'○\s*사업목적\s*:(.*?)(?=○\s*사업기간|$)',
        '사업기간': r'○\s*사업기간\s*:(.*?)(?=○\s*총사업비|$)',
        '총사업비': r'○\s*총사업비\s*:(.*?)(?=○\s*사업규모|$)',
        '사업규모': r'○\s*사업규모\s*:(.*?)(?=○\s*사업내용|$)',
        '사업내용': r'○\s*사업내용\s*:(.*?)(?=○\s*지원형태|$)',
        '지원형태': r'○\s*지원형태\s*:(.*?)(?=○\s*지원조건|$)',
        '지원조건': r'○\s*지원조건\s*:(.*?)(?=○\s*사업위치|$)',
        '사업위치': r'○\s*사업위치\s*:(.*?)(?=○\s*시행주체|$)',
        '시행주체': r'○\s*시행주체\s*:(.*?)(?=○\s*추진근거|$)',
        '추진근거': r'○\s*추진근거\s*:(.*?)(?=○\s*추진경위|$)',
        '추진경위': r'○\s*추진경위\s*:(.*?)(?=○\s*추진계획|$)',
        '추진계획': r'○\s*추진계획\s*:(.*?)(?=□|\Z)'
    }

    #폴더 내 모든 파일 순회
    for file_name in os.listdir(input_path):

        previous_row_data = None  # 직전 행 데이터를 저장하기 위한 변수

        if file_name.endswith('.pdf'):
            file_path = os.path.join(input_path, file_name)

            # pdfminer로 전체 페이지에서 텍스트 추출
            text = extract_text(file_path)
            text = clean_text(text)

            # 각 페이지를 구분하기 위해 페이지 구분자 "\x0c"를 사용
            pages = text.split("\x0c")

            #페이지 단위로 데이터 추출
            for page_num, page_text in enumerate(pages, 1):
                
                # 문건 정보 초기화
                start_page = end_page = page_num
                title_number = ""
                title = ""

                # 문건 정보 추출
                title_match = re.search(document_pattern, page_text, re.DOTALL)
                if title_match:
                    title_number = title_match.group(1).strip()
                    title = title_match.group(2).strip()
                else:
                    # 세부사업 번호가 없는 문건의 경우
                    title_match = re.search(non_number_pattern, page_text, re.DOTALL)
                    if title_match:
                        title = title_match.group(0).strip()
                    else:
                        # 오버페이징된 경우, 이전 문건의 페이지 범위 확장
                        if previous_row_data:
                            previous_row_data[3] = page_num
                        continue  # 다음 페이지로 넘어감

                # 새로운 행 추가
                row_data = [title_number, title, start_page, end_page]

                # 문건 내, 세부내용 정보 추출
                for item_key, item_pattern in content_patterns.items():
                    item_match = re.search(item_pattern, page_text, re.DOTALL)
                    if item_match:
                        content = item_match.group(1).strip()
                        row_data.append(content)
                    else:
                        row_data.append("")

                data.append(row_data)
                previous_row_data = row_data  # 현재 행을 저장하여 다음에 사용할 수 있게 함

                print(f"처리 완료: {file_name}")

    # 결과를 엑셀 파일로 저장
    columns = ['세부사업 번호', '제목', '시작페이지', '마지막페이지'] + list(content_patterns.keys())
    df = pd.DataFrame(data, columns=columns)
    df.to_excel(output_file, index=False)

    print(f"데이터가 '{output_file}'에 저장되었습니다.")


input_path = r"C:\Users\User\Desktop\2024_pdf"
output_file = r"C:\Users\User\Desktop\pdfminer_content_2024.xlsx"

extract_text_to_file(input_path, output_file)
