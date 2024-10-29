# refined data source: https://www.openfiscaldata.go.kr/op/ko/bs/UOPKOBSA02
# 조건없이 테이블 추출하여 구조 파악 후 필요한 추출 조건 추가

import pdfplumber #pip install pdfplumber
import pandas as pd #pip install pandas, pip install openpyxl
import re
import os


def pdf_table_extract(input_path, output_file):
    excel_data = []
    
    #폴더 내 모든 파일 순회
    for file_name in os.listdir(input_path):
        
        # 추출 데이터 구조 초기화
        document_set = {
            # A 테이블
            'accounting_code': "",          # 회계코드
            'accounting_name': "",          # 회계명
            'jurisdiction_code': "",        # 소관코드
            'jurisdiction_name': "",        # 소관명
            'account_code': "",             # 계정코드
            'account_name': "",             # 계정명
            'field_code': "",               # 분야코드
            'field_name': "",               # 분야명
            'sector_code': "",              # 부문코드
            'sector_name': "",              # 부문명
            # B 테이블
            'program_code': "",             # 프로그램코드
            'program_name': "",             # 프로그램명
            'unit_business_code': "",       # 단위사업코드
            'unit_business_name': "",       # 단위사업명
            'detailed_business_code': "",   # 세부사업코드
            'detailed_business_name': "",   # 세부사업명
            # C 테이블
            'N_2': "-",                      # N-2년전 결산
            'N_last_1': "",                 # N-1년전 본예산
            'N_last_2': "",                 # N-1년전 추경
            'N_main_1': "",                 # N년 본예산
            'N_main_2': ""                  # N년 추경
                                            # 증감률, A/B에 적용하는 A와 B가 문건마다 달라 통일된 기준으로 직접 추산 예정
        }

        if file_name.endswith('.pdf'):
            file_name = os.path.splitext(file_name)[0]
            file_path = os.path.join(input_path, file_name + '.pdf')

            try:
                # pdf 파일 열기
                with pdfplumber.open(file_path) as pdf:

                    # 파일 내 모든 페이지 순회
                    for page in pdf.pages:
                        tables = page.extract_tables()
                        if len(tables) > 0:
                            # 페이지 내 모든 테이블 순회
                            for table in tables:
                            # A 테이블 패턴 발견
                                if len(table[0]) > 2 and table[0][2] == "소관":

                                    # C 테이블 생략 체크
                                    if any(value != "" for value in document_set.values()):
                                        excel_data.append([file_name] + list(document_set.values()))
                                        document_set = {key: "" for key in document_set}

                                    if len(table[0]) == 7 and len(table) == 3: # 기본 테이블 구조와 다른 경우 예외처리
                                        # 회계 처리
                                        accounting = table[1][1]
                                        if table[2][1] == None:
                                            try:
                                                accounting_match = re.search(r"(\d+)\s*([\s\S]+)", accounting)
                                                document_set['accounting_code'] = accounting_match.group(1)
                                                document_set['accounting_name'] = accounting_match.group(2)
                                            except:
                                                document_set['accounting_code'] = ""
                                                document_set['accounting_name'] = table[1][1]
                                        else:
                                                document_set['accounting_code'] = table[1][1]
                                                document_set['accounting_name'] = table[2][1]

                                        # 소관 처리
                                        jurisdiction = table[1][2]
                                        if table[2][2] == None:
                                            if "518민주화" not in jurisdiction and "1029이태원" not in jurisdiction:
                                                try:
                                                    jurisdiction_match = re.search(r"(\d+)\s*([\s\S]+)", jurisdiction)
                                                    document_set['jurisdiction_code'] = jurisdiction_match.group(1)
                                                    document_set['jurisdiction_name'] = jurisdiction_match.group(2)
                                                except:
                                                    document_set['jurisdiction_code'] = ""
                                                    document_set['jurisdiction_name'] = table[1][2]
                                            else:
                                                document_set['jurisdiction_code'] = ""
                                                document_set['jurisdiction_name'] = table[1][2]
                                        else:
                                            document_set['jurisdiction_code'] = table[1][2]
                                            document_set['jurisdiction_name'] = table[2][2]
                                        
                                        # 계정 처리
                                        account = table[1][4]
                                        if table[2][4] == None:
                                            try:
                                                account_match = re.search(r"(\d+)\s*([\s\S]+)", account)
                                                document_set['account_code'] = account_match.group(1)
                                                document_set['account_name'] = account_match.group(2)
                                            except:
                                                if re.match(r'^\d+$', account):
                                                    document_set['account_code'] = account
                                                    document_set['account_name'] = ""
                                                else:
                                                    document_set['account_code'] = ""
                                                    document_set['account_name'] = account
                                        else:
                                            document_set['account_code'] = table[1][4]
                                            document_set['account_name'] = table[2][4]

                                        # 분야, 부문 처리
                                        document_set['field_code'] = table[1][5]
                                        document_set['field_name'] = table[2][5]
                                        document_set['sector_code'] = table[1][6]
                                        document_set['sector_name'] = table[2][6]
                                    else:
                                        document_set['accounting_code'] = "error/사업코드 테이블 구조 확인 요구"

                                # B 테이블 패턴 발견
                                elif len(table[0]) > 1 and table[0][1] == "프로그램":
                                    if len(table[0]) == 4 and len(table) == 3: # 기본 테이블 구조와 다른 경우 예외처리
                                        document_set['program_code'] = table[1][1]
                                        document_set['program_name'] = table[2][1]
                                        document_set['unit_business_code'] = table[1][2]
                                        document_set['unit_business_name'] = table[2][2]
                                        document_set['detailed_business_code'] = table[1][3]
                                        document_set['detailed_business_name'] = table[2][3]
                                    else:
                                        document_set['program_code'] = "error/프로그램 테이블 구조 확인 요구"

                                # C 테이블 패턴 발견
                                elif (len(table[0]) > 1 and isinstance(table[0][1], str) and re.match(r'^\d{4}년\s*결산', table[0][1])):
                                    
                                    document_set['N_2'] = table[2][1]
                                    document_set['N_last_1'] = table[2][2]

                                    # 기본 테이블 구조(3x8, N-1년에 2개 항목, N년에 2개 항목)
                                    if len(table) <= 3 and table[0][3] is None and table[0][5] is None and table[0][6] is not None:
                                        document_set['N_last_2'] = table[2][3]
                                        document_set['N_main_1'] = table[2][4]
                                        document_set['N_main_2'] = table[2][5]

                                    # 예시) N-1년에 1개 항목, N년에 2개 항목
                                    # elif len(table) <= 3 and table[0][3] is not None and table[0][4] is None and table[0][5] is not None:
                                    #     document_set['N_last_2'] = ""
                                    #     document_set['N_main_1'] = table[2][3]
                                    #     document_set['N_main_2'] = table[2][4]
                                    
                                    else:
                                        # 그 외 다양한 형식
                                        # (len(table) > 3)인 경우
                                        # N-1년에 1개 항목, N년에 1개 항목
                                        # N-1년에 1개 항목, N년에 3개 항목
                                        # N-1년에 2개 항목, N년에 1개 항목
                                        # N-1년에 2개 항목, N년에 3개 항목
                                        # N-1년에 3개 항목, N년에 1개 항목
                                        # N-1년에 3개 항목, N년에 2개 항목
                                        # N-1년에 3개 항목, N년에 3개 항목
                                        document_set['N_2'] = "error/예산 테이블 구조 확인 요구"
                                    
                                    excel_data.append([file_name] + list(document_set.values()))
                                    document_set = {key: "" for key in document_set} # 모든 값 초기화
    
            except Exception as e:
                excel_data.append([file_name, "파일 열기 오류 발생", str(e)] + [""] * 20)
    

    # 엑셀 저장
    columns = ["유니코드", "회계코드", "회계명", "소관코드", "소관명", "계정코드", "계정명", 
                "분야코드", "분야명", "부문코드", "부문명", "프로그램코드", "프로그램명", "단위사업코드", 
                "단위사업명", "세부사업코드", "세부사업명", "N-2년_결산", "N-1년_본예산", "N-1년_추경", 
                "N년_본예산", "N년_추경"]
    df = pd.DataFrame(excel_data, columns=columns)
    df.to_excel(output_file, index=False)
    print(f"데이터가 {output_file}로 저장되었습니다.")


# 실행
input_path = r'C:\Users\User\Desktop\중앙정부)국가재정\2024_pdf'
output_file = 'pdf_table_2024_v2.xlsx'
pdf_table_extract(input_path, output_file)
