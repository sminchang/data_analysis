# 실국 혹은 과(팀) 내부적으로 개행이 발생하여 이상하게 잘린 단어를 직접 확인-수정해야함

import pdfplumber #pip install pdfplumber
import traceback
import re
import os
import pandas as pd #pip install pandas, pip install openpyxl

def B_C_table_process(table, file_name, data, part):
    skip_next = False
    # table에서 첫 번째 행을 제외한 나머지 행을 순회하면서 조건에 맞는 값을 추출
    for idx, row in enumerate(table[1:], start=1): 
        
        if skip_next:
            skip_next = False
            continue

        # 컬럼명만 있는 경우, 행 생략
        elif (row[2] is not None and
            re.search(r'실.*국.*과*.팀*.\)?', str(row[2])) and
            len(row[2].split('\n')) == 1):
                continue

        elif (row[2] is not None and 
            (row[1] is None or (row[1] is not None and row[1] != "사업시행주체"))):
            if row[0] is None:
                
                # 행 분할 b 유형, 2행 분할 [..."실국과(팀)\nOO실,..], [...“OO과"...]
                # 행 분할 c 유형, 3행 분할 [..."실국과(팀)”...], [...“OO실”...], [...“OO과"...] #컬럼명만 있는 행 생략 후 b 유형과 동일하게 동작
                if ((idx + 1) <= len(table[1:]) and 
                    table[idx+1][1] is None and 
                    table[idx+1][2] is not None):
                        part[0] = row[2]
                        part[1] = table[idx+1][2]
                        skip_next = True  # 다음 행 건너뛰기 플래그
                
                # 사업시행주체가 2행 분할된 경우, 행 생략
                elif row[1] is None and table[idx-1][1] == "사업시행주체":
                    continue

                # 행 분할 d 유형, 2행 분할 [..."실국과(팀)”...], [...\nOO실\nOO과”...]
                else:
                    row_parts = row[2].split('\n')
                    part[0] = row_parts[0] if len(row_parts) > 1 else row[2]
                    part[1] = '\n'.join(row_parts[1:]) if len(row_parts) >= 2 else ""

            # 행 분할 a 유형, 1행 통합 [..."실국과(팀)\nOO실\nOO과”...]
            else:
                row_parts = row[2].split('\n')
                part[0] = row_parts[1] if len(row_parts) > 1 else row[2]
                part[1] = '\n'.join(row_parts[2:]) if len(row_parts) >= 2 else ""

        # row[1]이 "사업시행주체"인 경우 또는, row[2]가 None인 경우
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
                                        if flag: # 오버페이징을 찾았다면 반복 중단
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

                # 사업 담당자 테이블 자체가 존재하지 않는 경우
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

input_path = r"C:\Users\고객관리\Desktop\2-1 분할본\2023_세출"
output_file = r"C:\Users\고객관리\Desktop\2023_세출_담당자_v10.xlsx"

extract_text_to_file(input_path, output_file)
