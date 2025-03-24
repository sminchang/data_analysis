import pdfplumber #pip install pdfplumber
import pandas as pd #pip install pandas, pip install openpyxl
import re
import os
import util.extract_divided_double_page as eddp


# step3. 테이블 구조에 대한 파악을 토대로, 금액값에 대한 검증을 포함한 최종 추출을 수행한다.


def convert_row(row):
    """금액값 문자열->정수형으로 변환"""
    refer_cell_flag = False # *특수문자 예외 중복처리 방지

    for cell in row[1:9]:
                    
        # 빈 셀값 0 처리
        if not cell or cell.strip() == '' or cell.strip() == '-':
            convert_row.append(0)
            continue

        # '*금액' 형식의 주석이 달린 금액 처리 
        refer_cell = cell.replace('*','')
        if cell != refer_cell:
            cell = refer_cell
            if not refer_cell_flag:
                log += "금액 참고사항 주석 확인\n"
                refer_cell_flag = True
        
        cell = re.sub(r'[,().\s]', '', cell).replace('△', '-').replace('∆', '-').replace('⧍','-').replace('∇','-') # 셀 내 특수문자 처리
        cell = re.sub(r'(?<=\d)\s*-', '', cell) # 숫자 뒤에 오는 하이픈 처리

        # 특수문자 처리 후 빈 셀 0처리
        if cell == '':
            convert_row.append(0)
            continue

        # 금액: 문자열->정수형 변환 
        cell = int(cell)
        convert_row.append(cell)

    return convert_row


def find_and_extarct_table(tables, file_name, excel_data):
    """추출할 테이블 식별 및 데이터 추출"""
    for table in tables:
        if (re.match(r"구\s*분", table[0][0]) and re.match(r"총\s*사\s*업\s*비|총\s*수\s*입", table[0][1])):
            for row in table[2:]:
                log = ""
                row = [row[0]] # '구분'
                
                if len(table[0]) != 10:
                    log += "테이블 구조 확인\n"
                
                # 금액이 빈 경우 행 생략
                if all(not cell for cell in row[1:]):
                    continue
                
                # 금액값 문자열->정수형으로 변환 후 검증
                row = convert_row(row)
                
                # 금액값 오탈자 검수
                if row[3] != row[4] + row[5]:
                    log += "A+B 오타 확인\n"
                if row[7] != row[6] - row[4]:
                    log += "C-A 오타 확인\n"
                
                row.append(row[9]) # '비고'
                
                # 새 행 추가
                excel_data.append([file_name] + row + [log])
            return True
    return False


def pdf_table_extract(input_path, output_file):
    """pdf 읽기 및 모아찍기 예외처리"""
    excel_data = []
    
    #폴더 내 모든 파일 순회
    for file_name in os.listdir(input_path):

        if file_name.endswith('.pdf'):
            file_name = os.path.splitext(file_name)[0]
            file_path = os.path.join(input_path, file_name + '.pdf')

            try:
                # pdf 파일 열기
                with pdfplumber.open(file_path) as pdf:

                    # 모아찍기 식별 및 예외처리
                    if eddp.has_text_layer_mismatch(pdf.pages[0]):
                        tables = eddp.extract_tables_by_divided_double_page(pdf.pages[0])
                    else:
                        tables = pdf.pages[0].extract_tables()

                    if len(tables) > 0:
                        match_found = find_and_extarct_table(tables, file_name, excel_data)
                        if not match_found:
                            log = "첫 페이지 내 테이블을 찾지 못함"
                            excel_data.append([file_name] + ['']*10 + [log])

            except (IndexError, TypeError):
                pass
            except Exception as e:
                print(f"Error {file_name}: {str(e)}")

    df = pd.DataFrame(excel_data)
    df.columns = ['파일명', '구분', '총사업비', 'N-2년 투자 계', 'N-1년 계(A+B)', 'N-1년 당초(A)', 'N-1년 추경(B)', 
                'N년 예산안(C)', 'N년 본예산 대비 증감(C-A)', '향후 투자', '비고', 'log']
    
    # 금액값 오탈자 및 누락 검수
    for file_name, group in df.groupby("파일명"):

        sub_rows = group[group["구분"] != "계"]
        columns_to_check = ['총사업비', 'N-2년 투자 계', 'N-1년 계(A+B)', 'N-1년 당초(A)', 
                            'N-1년 추경(B)', 'N년 예산안(C)', 'N년 본예산 대비 증감(C-A)', '향후 투자']
        
        for idx, row in group.iterrows():
            if row["구분"] == "계":  # '계' 행에서만 검사
                
                for col in columns_to_check:
                    total_value = row[col]
                    sub_sum = sub_rows[col].sum()
                    
                    if total_value != sub_sum:
                        df.at[idx, 'log'] += "계와 나머지 총합 불일치\n"
                        break

    df.to_excel(output_file, index=False)
    print(f"successful: {output_file}")


if __name__ == "__main__":
    input_path = r'C:\Users\yunis\바탕 화면\세부사업설명서\세출'
    output_file = r'C:\Users\yunis\바탕 화면\세출_예산총괄표_최종.xlsx'
    pdf_table_extract(input_path, output_file)
