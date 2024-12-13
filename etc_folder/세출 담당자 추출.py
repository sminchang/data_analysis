# 테이블 식별 시 헤더열은 고정되어있기에 헤더열에서 기준을 잡는 것이 좋고,
# 실.국의 경우 .에 해당하는 특수문자가 사업마다 상이할 수 있어 과(팀)을 테이블 식별 기준으로 잡음

# <수작업 목록>
# 1. 실국 혹은 과(팀) 내부적으로 개행이 발생한 경우는 제대로 추출이 안됨, 이상하게 잘린 단어를 직접 확인-수정해야함(2023_02_00726, 2023_02_02964 예시)                                                    

import pdfplumber #pip install pdfplumber
import traceback
import re
import os
import pandas as pd #pip install pandas, pip install openpyxl

def B_C_table_process(table, file_name, data, part):
    # table에서 첫 번째 행을 제외한 나머지 행을 순회하면서 조건에 맞는 값을 추출
    for idx, row in enumerate(table[1:], start=1):  # 첫 번째 행을 제외한 부분
        
        #셀에 컬럼명만 있을 경우 생략
        if (row[2] is not None and
            re.search(r'실.*국.*과*.팀*.\)?', str(row[2])) and
            len(row[2].split('\n')) == 1):
                continue

        # 테이블 F 유형, [["사업명","구분","None"...],["oo사업","소관부처","실국과(팀)",OO국"],[None,None,"OO과"...]]
        # 같은 열에서 실국, 과팀을 별개 행으로 구분하는 경우
        elif (row[0] is None and  # row[0]이 None이 아닌 경우는 사업명이 적혀 있음
            row[2] is not None and  # index list out of range 예외처리
            table[idx-1][1] == "소관부처" and  # 바로 윗 행에 사업명이 있는지 확인 후 다음 행 정보까지 한 번에 추출
            row[1] != "사업시행주체"):
            if (idx + 1) <= len(table[1:]) and table[idx+1][1] != "사업시행주체":  # 행과 행 사이에 "사업시행주체" 행이 존재하는 경우 생략
                if table[idx+1][2] is not None:
                    part[0] = row[2]
                    part[1] = table[idx+1][2]
                else:
                    row_parts = row[2].split('\n')
                    part[0] = row_parts[0] if len(row_parts) > 1 else row[2]
                    part[1] = '\n'.join(row_parts[1:]) if len(row_parts) >= 2 else ""
            # 테이블 G 유형, [["사업명","구분","None"...],["oo사업","소관부처","실국과(팀)",OO국\nOO과"...],[None,None,None,"044-202-7348"...]...]
            elif (re.search(r'실.*국.*과*.팀*.\)?', str(table[idx-1][2])) and 
                  len(row[2].split('\n')) > 1):
                    row_parts = row[2].split('\n')
                    part[0] = row_parts[0] if len(row_parts) > 1 else row[2]
                    part[1] = '\n'.join(row_parts[1:]) if len(row_parts) >= 2 else ""

        # 일반적인 B,C 유형
        elif (row[1] is not None and
               row[1] != "사업시행주체" and
               row[2] is not None):
            row_parts = row[2].split('\n')
            part[0] = row_parts[1] if len(row_parts) > 1 else row[2]
            part[1] = '\n'.join(row_parts[2:]) if len(row_parts) >= 2 else ""
        
        else:
            continue
        
        data.append((file_name, part[0], part[1]))


def extract_text_to_file(input_path, output_file):
    data = []

    #폴더 내 모든 파일 순회
    for file_name in os.listdir(input_path):

        if file_name.endswith('.pdf'):
            file_path = os.path.join(input_path, file_name)

        try:
            # pdf 파일 열기
            with pdfplumber.open(file_path) as pdf:

                # 파일 단위로 초기화
                part = ["-", "-"]

                #페이지 단위로 데이터 추출
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        text = page.extract_text()
                        match = re.search(r'□\s*사업\s*담당자', text)
                        if match:
                            tables = page.extract_tables()
                            if len(tables) > 0:
                            # 페이지 내 모든 테이블 순회
                                for table in tables:

                                    if table and len(table[0]) >= 3 and table[0][1] is not None and table[0][2] is not None:
                                        # 테이블 A 유형, [["실국","과(팀)"...]...]
                                        if re.search(r'과\s*\(?팀\s*\)?', str(table[0][1])):
                                            for row in table[1:]:
                                                part[0] = row[0]
                                                part[1] = row[1]
                                                data.append((file_name, part[0], part[1]))
                                            break

                                        # 테이블 B 유형, [["사업명","소관부처","실국과(팀)\nOO실\nOO과"...]...]
                                        elif re.search(r'실.*국.*과\s*\(?팀\s*\)?', str(table[0][2])):
                                            B_C_table_process(table,file_name,data,part)
                                            break

                                    elif table and len(table[0]) >= 3 and len(table) >= 2 and table[1][2] is not None and table[1][1] is not None:
                                        # 테이블 C 유형, [["사업명","구분","None"...],["oo사업","소관부처","실국과(팀)\nOO실\nOO과"...]...]
                                        if re.search(r'실.*국.*과\s*\(?팀\s*\)?', str(table[1][2])):
                                            B_C_table_process(table,file_name,data,part)
                                            break

                                        # 테이블 D 유형, [["사업명","구분","None"...],["oo사업","소관부처","실국\nOO실","과(팀)\nOO과"...]...]
                                        elif re.search(r'실.*국', str(table[1][1])) and re.search(r'과\s*\(?팀\s*\)?', str(table[1][2])):
                                            for row in table[1:]:
                                                part1_splits = row[1].split('\n',1)
                                                part2_splits = row[2].split('\n',1)
                                                part[0] = '\n'.join(part1_splits[1:]) if len(part1_splits) > 1 else row[1]
                                                part[1] = '\n'.join(part2_splits[1:]) if len(part2_splits) > 1 else row[2]
                                                data.append((file_name, part[0], part[1]))
                                            break

                            # 사업 담당자 테이블이 오버페이징된 경우
                            if page_num < len(pdf.pages):  # 마지막 페이지가 아닌 경우
                                next_table = pdf.pages[page_num].extract_table()
                                if next_table:
                                    flag = False
                                    for row in next_table:
                                        for cell in row:
                                            if cell and re.search(r'\d{2,}-\d{2,}-\d{2,}',cell):
                                                part[0] = "overPaging"
                                                part[1] = "overPaging"
                                                data.append((file_name, part[0], part[1]))
                                                flag =True
                                                break
                                        if flag:
                                            break
                            
                            #사업 담당자 키워드를 찾았지만 기존 테이블 유형에서 찾지 못한 경우
                            if (part[0] == "-" and part[1] == "-"):
                                part[0] = "table error"
                                part[1] = "table error"
                                data.append((file_name, part[0], part[1]))
                            break


                    except Exception as e:
                        print(f"error {page_num} in file {file_name}: {str(e)}")
                        traceback.print_exc()
                        continue

                # 사업 담당자 테이블이 존재하지 않는 경우
                if (part[0] == "-" and part[1] == "-"):
                    data.append((file_name, part[0], part[1]))
  
        except Exception as e:
            print(f"file open error {file_name}: {str(e)}")
            continue


    # 결과를 엑셀 파일로 저장
    columns = ['유니코드', '실국', '과(팀)']
    df = pd.DataFrame(data, columns=columns)
    df.to_excel(output_file, index=False)

    print(f"데이터가 '{output_file}'에 저장되었습니다.")


input_path = r"C:\Users\Minchang Sung\Desktop\2023_세출"
output_file = r'C:\Users\Minchang Sung\Desktop\2023_세출_담당자_v9.xlsx'

extract_text_to_file(input_path, output_file)
