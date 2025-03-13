import pdfplumber
import pandas as pd
import os


def extract_tables_by_divided_double_page(input_path, output_file):
    """좌표값 범위를 기준으로 페이지 유형을 식별하고 적절한 테이블만 추출"""
    excel_data = []
    files_processed = 0
    tables_extracted = 0

    for file_name in os.listdir(input_path):
        file_path = os.path.join(input_path, file_name)

        if not file_name.endswith('.pdf'):
            continue

        file_name = os.path.splitext(file_name)[0]
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # 페이지 너비와 시각적 경계
                    width = page.width
                    bbox = page.bbox
                    
                    # 실제 보이는 문자 필터링
                    visible_chars = [c for c in page.chars if 
                                    c['x0'] >= bbox[0] and c['x1'] <= bbox[2] and 
                                    c['top'] >= bbox[1] and c['bottom'] <= bbox[3]]
                    
                    if not visible_chars:
                        continue
                    
                    # 문자 좌표 범위로 페이지 유형 판단
                    x_coords = [c['x0'] for c in visible_chars]
                    min_x = min(x_coords)
                    max_x = max(x_coords)
                    
                    if min_x > width/2:
                        page_side = "오른쪽"
                    elif max_x < width:
                        page_side = "왼쪽"
                    else:
                        page_side = "불명확"
                    
                    # 테이블 추출
                    tables = page.extract_tables()
                    table_bboxes = page.find_tables()
                    
                    for table_idx, table in enumerate(tables):
                        if table_idx < len(table_bboxes):
                            x0, y0, x1, y1 = table_bboxes[table_idx].bbox
                            table_side = "왼쪽" if x0 < width/2 else "오른쪽"
                            
                            # 페이지 유형과 테이블 위치가 일치하는 경우만 추출
                            if page_side == table_side:
                                for row in table:
                                    excel_data.append([f"{file_name} (페이지 {page_num+1})"] + row)
                                excel_data.append([])  # 테이블 간 공백 행 추가
                                tables_extracted += 1
        
        except Exception as e:
            print(f"오류 발생: {file_name} - {str(e)}")
            excel_data.append([file_name, f"오류 발생: {str(e)}"])
        
        files_processed += 1

    # 엑셀 저장
    if excel_data:
        df = pd.DataFrame(excel_data)
        df.to_excel(output_file, index=False, header=False)
        print(f"처리 완료: {files_processed}개 파일에서 {tables_extracted}개 테이블 추출")
        print(f"데이터가 '{output_file}'로 저장되었습니다.")
    else:
        print("추출된 테이블이 없습니다.")

#사용 예
input_path = r"C:\Users\yunis\바탕 화면\test1"
txt_output_path = 'extracted_texts.txt'
excel_output_path = 'extracted_tables.xlsx'
extract_tables_by_divided_double_page(input_path, excel_output_path)