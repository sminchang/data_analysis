import os
from PyPDF2 import PdfReader, PdfWriter
import copy

def split_pdf(input_pdf, output_dir, ranges):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    pdf = PdfReader(input_pdf)
    total_pages = len(pdf.pages)

    for i, (start, end, is_split) in enumerate(ranges):
        output_pdf = PdfWriter()
        filename = f"output_{i+1}.pdf"
        output_path = os.path.join(output_dir, filename)

        for page_num in range(start - 1, min(end, total_pages)):
            page = pdf.pages[page_num]

            if is_split:
                # 페이지를 반으로 나누는 로직 (모아찍기된 페이지 처리)

                left_page = copy.deepcopy(page)
                right_page = copy.deepcopy(page)
                page_width = page.mediabox.width
                page_height = page.mediabox.height

                # 왼쪽 절반 페이지
                left_page.mediabox.upper_right = (page_width / 2, page_height)
                left_page.cropbox.upper_right = (page_width / 2, page_height)
                output_pdf.add_page(left_page)

                # 오른쪽 절반 페이지
                right_page.mediabox.lower_left = (page_width / 2, 0)
                right_page.cropbox.lower_left = (page_width / 2, 0)
                output_pdf.add_page(right_page)

            else:
                # 일반적인 페이지 추가
                output_pdf.add_page(page)


        with open(output_path, "wb") as f:
            output_pdf.write(f)
        print(f"Saved: {filename}")

# 분할 저장할 페이지 번호
if __name__ == "__main__":
    ranges = [
        (1, 255, False),
        (256, 282, True),
        (283, 360, False),
        (361, 430, False),
        (431, 446, False),
        (447, 587, True),
        (588, 1119, False),
        (1120, 1365, False),
        (1366, 2447, False),
        (2448, 3441, False),
        (3442, 4152, False),
        (4153, 4647, False),
        (4648, 5774, False),
        (5775, 5793, False),
        (5794, 6329, False),
        (6330, 7083, False),
        (7084, 7503, False),
        (7504, 7538, False),
        (7539, 7700, False),
        (7701, 7910, False),
        (7911, 8027, False),
        (8028, 8281, False),
        (8282, 9431, False),
        (9432, 9649, False),
        (9650, 9664, False),
        (9665, 9709, False),
        (9710, 9732, False),
        (9733, 10089, False),
        (10090, 10511, False),
        (10512, 10575, False),
        (10576, 10744, False),
        (10745, 10812, True),
        (10813, 10855, True),
        (10856, 10922, True),
        (10923, 10948, False),
        (10949, 11138, False),
        (11139, 11168, False),
        (11169, 11592, False),
        (11593, 11639, True),
        (11640, 11675, False),
        (11676, 11940, False),
        (11941, 12255, True),
        (12256, 13037, False),
        (13038, 13215, True),
        (13216, 13367, False),
        (13368, 14106, False),
        (14107, 14254, False),
        (14255, 14837, False),
        (14838, 15484, False),
        (15485, 15531, False)
    ]
    
    input_pdf = r"C:\Users\yunis\OneDrive - 씨지인사이드\task\소장님 지시\경기도_지방재정\2025 본예산안 사업설명서.pdf" # 실제 PDF 파일 이름으로 변경
    output_dir = r"C:\Users\yunis\바탕 화면\사업설명서_원본"  # 출력 디렉토리
    split_pdf(input_pdf, output_dir, ranges)