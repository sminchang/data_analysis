import pdfplumber
import pandas as pd
import os


def extract_text_by_divided_double_page(input_path, output_txt_path):
    """실제 렌더링되는 텍스트만 추출하는 함수"""

    for file_name in os.listdir(input_path):
        pdf_path = os.path.join(input_path, file_name)

        if not file_name.endswith('.pdf'):
            continue

        file_name = os.path.splitext(file_name)[0]
        
        with pdfplumber.open(pdf_path) as pdf:
            extracted_texts = []
            
            for i, page in enumerate(pdf.pages):
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
                # 크롭된 PDF에서는 원래 있던 요소 중 일부가 보이지 않을 수 있음
                cropped_visible_chars = []
                for char in visible_chars:
                    # 내부적으로 PDF 객체의 표시 속성 확인
                    # 실제 렌더링에 포함되는 요소만 선택
                    #if 'non_stroking_color' in char and char['non_stroking_color'] is not None:
                    cropped_visible_chars.append(char)
                
                # 줄 단위 처리 (기존 방식과 유사)
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
                extracted_texts.append(f"Page {i+1}:\n{page_text}\n")
                
            # 저장
            with open(output_txt_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(extracted_texts))



# 사용 예
input_path = r"C:\Users\yunis\바탕 화면\test1"
txt_output_path = 'extracted_texts.txt'
excel_output_path = 'extracted_tables.xlsx'
extract_text_by_divided_double_page(input_path,txt_output_path)