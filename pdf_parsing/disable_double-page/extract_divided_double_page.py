import pdfplumber
import pandas as pd
import os

# 모아찍기된 페이지를 분할 저장했을 때 렌더링 텍스트와 내부 텍스트 레이어가 일치하지 않는 문제에 대한 예외처리 추출 코드 

def has_text_layer_mismatch(page):
    """
    모아찍기 해제된 페이지인지 확인
    x좌표가 페이지 너비를 초과하면 불일치로 판단"""
    # 모든 문자 가져오기
    chars = page.chars
    bbox = page.bbox

    if not chars:
        return False  # 문자가 없으면 불일치 확인 불가
    
    visible_chars = [c for c in chars if 
                    c['x0'] >= bbox[0] and c['x1'] <= bbox[2] and 
                    c['top'] >= bbox[1] and c['bottom'] <= bbox[3]]
    if len(chars) != len(visible_chars):
        return True
    
    # 불일치 없음
    return False

def extract_tables_by_divided_double_page(page):
    """좌표값 범위를 기준으로 분할 위치(왼쪽,오른쪽)를 식별하고 해당 테이블만 추출"""
    
    # 페이지 너비와 시각적 경계
    width = page.width
    bbox = page.bbox
    
    # 실제 보이는 문자 필터링
    visible_chars = [c for c in page.chars if 
                    c['x0'] >= bbox[0] and c['x1'] <= bbox[2] and 
                    c['top'] >= bbox[1] and c['bottom'] <= bbox[3]]
    
    if not visible_chars:
        return []
    
    # 문자 좌표 범위로 페이지 유형 판단
    x_coords = [c['x0'] for c in visible_chars]
    min_x = min(x_coords)
    max_x = max(x_coords)
    if min_x > width:
        page_side = "오른쪽"
    elif max_x < width:
        page_side = "왼쪽"
    else:
        page_side = "불명확"
    
    # 테이블 추출
    filtering_tables = []
    tables = page.extract_tables()
    table_bboxes = page.find_tables()
    
    for table_idx, table in enumerate(tables):
        if table_idx < len(table_bboxes):
            x0, y0, x1, y1 = table_bboxes[table_idx].bbox
            table_side = "왼쪽" if x0 < width  else "오른쪽"
            # 페이지 유형과 테이블 위치가 일치하는 경우만 추출
            if page_side == table_side:
                filtering_tables.append(table)

    return filtering_tables



def extract_text_by_divided_double_page(page):
    """페이지 내 실제 렌더링되는 텍스트만 추출하는 함수"""

    # 시각적 경계 확인 (페이지의 시각적 경계 상자)
    bbox = page.bbox
    
    # 모든 문자 가져오기
    chars = page.chars
    
    # 실제 시각적 경계 내에 있는 문자만 필터링
    # bbox는 (x0, top, x1, bottom) 형태
    visible_chars = [c for c in chars if 
                    c['x0'] >= bbox[0] and c['x1'] <= bbox[2] and 
                    c['top'] >= bbox[1] and c['bottom'] <= bbox[3]]

    # 가시성 추가 검사 (페이지에 렌더링될 때 실제로 보이는 요소만)
    cropped_visible_chars = []
    for char in visible_chars:
        cropped_visible_chars.append(char)
    
    # 줄 단위 처리
    filtered_chars = cropped_visible_chars
    filtered_chars.sort(key=lambda c: (c['top'], c['x0']))
    
    # 줄 단위로 그룹화
    line_groups = []
    current_line = []
    current_top = None
    y_tolerance = 3
    
    for char in filtered_chars:
        if current_top is None or abs(char['top'] - current_top) <= y_tolerance:
            current_line.append(char)
            if current_top is None:
                current_top = char['top']
        else:
            if current_line:
                line_groups.append(current_line)
            current_line = [char]
            current_top = char['top']
    
    if current_line:
        line_groups.append(current_line)
    
    # 텍스트 생성
    text_lines = []
    for line in line_groups:
        line_text = ''.join([c['text'] for c in line])
        text_lines.append(line_text)
    
    page_text = '\n'.join(text_lines)
    return page_text
                                
        

#사용 예
if __name__ == "__main__":
    input_path = r"C:\Users\yunis\바탕 화면\test"
    excel_output_path = 'extracted_tables.xlsx'
    txt_output_path = 'extracted_texts.txt'

    

    for file_name in os.listdir(input_path):
        file_path = os.path.join(input_path, file_name)

        if not file_name.endswith('.pdf'):
            continue

        file_name = os.path.splitext(file_name)[0]
        
        try:
            with pdfplumber.open(file_path) as pdf:
                texts = ""
                excel_data = []
                for page_num, page in enumerate(pdf.pages):

                    # 텍스트 추출
                    texts += extract_text_by_divided_double_page(page)

                    # 테이블 추출
                    tables = extract_tables_by_divided_double_page(page)
                    for table in tables:
                        for row in table:
                            excel_data.append([f"{file_name} (페이지 {page_num+1})"] + row)
                        excel_data.append([])  # 테이블 간 공백 행 추가
                    
                # 텍스트 저장
                with open(f"{txt_output_path}{file_name}.txt", 'w', encoding='utf-8') as f:
                    f.write(texts)
                print(f"{file_name} 텍스트가 '{txt_output_path}'로 저장되었습니다.")

                # 테이블 저장
                if excel_data:
                    df = pd.DataFrame(excel_data)
                    df.to_excel(f"{excel_output_path}{file_name}.xlsx", index=False, header=False)
                    print(f"{file_name} 테이블이 '{excel_output_path}'로 저장되었습니다.")
                else:
                    print("추출된 테이블이 없습니다.")

        except Exception as e:
            print(f"오류 발생: {file_name} - {str(e)}")
            excel_data.append([file_name, f"오류 발생: {str(e)}"])

