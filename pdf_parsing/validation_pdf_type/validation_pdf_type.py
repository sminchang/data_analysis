import pdfplumber
from enum import Enum

# 상수 정의
class PageType(Enum):
    DIGITAL = "digital"
    HIDDEN_TEXT = "hidden_text"
    IMAGED = "imaged"
    EMPTY = "empty"

def has_text_layer_mismatch(page):
    """
    모아찍기 해제된 페이지인지 확인
    x좌표가 페이지 너비를 초과하면 불일치로 판단
    """
    # 모든 문자 가져오기
    chars = page.chars
    bbox = page.bbox
    
    if not chars:
        return False  # 문자가 없으면 불일치 확인 불가
    
    visible_chars = [c for c in chars if c['x0'] >= bbox[0] and c['x1'] <= bbox[2] 
                    and c['top'] >= bbox[1] and c['bottom'] <= bbox[3]]
    
    if len(chars) != len(visible_chars):
        return True
    
    # 불일치 없음
    return False

def get_page_type(page):
    """
    PDF 페이지의 유형을 간단히 반환하는 함수
    
    Args:
        page: pdfplumber의 Page 객체
        
    Returns:
        str: 'digital', 'hidden_text', 'imaged', 'empty' 중 하나
    """
    text = page.extract_text()
    has_text = bool(text and text.strip())
    has_image = bool(page.images)
    has_chars = bool(page.chars)
    has_shapes = bool(page.objects.get("curve") or page.objects.get("rect"))
    text_layer_mismatch = has_text_layer_mismatch(page)
    
    # 텍스트는 추출되지만 좌표가 페이지 범위를 벗어나는 경우
    if has_text and text_layer_mismatch:
        return PageType.HIDDEN_TEXT.value
    
    # 텍스트가 정상적으로 추출되는 경우
    if has_text:
        return PageType.DIGITAL.value
    
    # 완전 빈 페이지
    if not has_image and not has_chars and not has_shapes:
        return PageType.EMPTY.value
    
    # 텍스트는 없지만 이미지/도형/문자 요소가 있는 경우
    return PageType.IMAGED.value

def analyze_page_detailed(page):
    """
    PDF 페이지의 상세 분석 정보를 반환하는 함수
    
    Args:
        page: pdfplumber의 Page 객체
        
    Returns:
        dict: 상세 분석 정보
    """
    text = page.extract_text()
    has_text = bool(text and text.strip())
    has_image = bool(page.images)
    has_chars = bool(page.chars)
    has_shapes = bool(page.objects.get("curve") or page.objects.get("rect"))
    text_layer_mismatch = has_text_layer_mismatch(page)
    
    page_type = get_page_type(page)
    
    # 타입별 설명 매핑
    descriptions = {
        PageType.HIDDEN_TEXT.value: '숨겨진 텍스트 레이어 페이지 (모아찍기 해제된 페이지)',
        PageType.DIGITAL.value: '디지털 페이지 (텍스트 추출 가능)',
        PageType.EMPTY.value: '빈 페이지',
        PageType.IMAGED.value: '이미지 페이지 (텍스트 추출 불가, 시각적 요소 존재)'
    }
    
    return {
        'type': page_type,
        'has_text': has_text,
        'has_image': has_image,
        'has_chars': has_chars,
        'has_shapes': has_shapes,
        'has_text_layer_mismatch': text_layer_mismatch,
        'description': descriptions.get(page_type, '알 수 없는 타입'),
        'text_length': len(text) if text else 0,
        'image_count': len(page.images) if page.images else 0,
        'char_count': len(page.chars) if page.chars else 0
    }

# 사용 예제
if __name__ == "__main__":
    # from utils.validation_pdf_type import get_page_type, PageType

    pdf_path = r"C:\Users\yunis\Desktop\test\2022_04_01003 (스캔된문서).pdf"

    with pdfplumber.open(pdf_path) as pdf:

        print("=== 간단 분석 ===")
        for page_num, page in enumerate(pdf.pages):
            page_type = get_page_type(page)
            if page_type == PageType.DIGITAL.value:
                print(f"페이지 {page_num + 1}: {page_type} = 텍스트 추출 가능")
            elif page_type == PageType.IMAGED.value:
                print(f"페이지 {page_num + 1}: {page_type} = OCR 필요")
            elif page_type == PageType.HIDDEN_TEXT.value:
                print(f"페이지 {page_num + 1}: {page_type} = 모아찍기 해제 필요")
            elif page_type == PageType.EMPTY.value:
                print(f"페이지 {page_num + 1}: {page_type} = 빈 페이지")
        
        print("\n=== 상세 분석 ===")
        for page_num, page in enumerate(pdf.pages):
            detailed_info = analyze_page_detailed(page)
            print(f"페이지 {page_num + 1}: {detailed_info}")
            