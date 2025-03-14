import os
from PyPDF2 import PdfReader, PdfWriter

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
            output_pdf.add_page(page)

        with open(output_path, "wb") as f:
            output_pdf.write(f)
        print(f"Saved: {filename}")

# 분할 저장할 페이지 번호
if __name__ == "__main__":
    ranges = [
        (1, 255),
        (256, 282),
        (283, 360),
        (361, 430),
        (431, 446),
        (447, 587),
        (588, 1119),
        (1120, 1365),
        (1366, 2447),
        (2448, 3441),
        (3442, 4152),
        (4153, 4647),
        (4648, 5774),
        (5775, 5793),
        (5794, 6329),
        (6330, 7083),
        (7084, 7503),
        (7504, 7538),
        (7539, 7700),
        (7701, 7910),
        (7911, 8027),
        (8028, 8281),
        (8282, 9431),
        (9432, 9649),
        (9650, 9664),
        (9665, 9709),
        (9710, 9732),
        (9733, 10089),
        (10090, 10511),
        (10512, 10575),
        (10576, 10744),
        (10745, 10812),
        (10813, 10855),
        (10856, 10922),
        (10923, 10948),
        (10949, 11138),
        (11139, 11168),
        (11169, 11592),
        (11593, 11639),
        (11640, 11675),
        (11676, 11940),
        (11941, 12255),
        (12256, 13037),
        (13038, 13215),
        (13216, 13367),
        (13368, 14106),
        (14107, 14254),
        (14255, 14837),
        (14838, 15484),
        (15485, 15531)
    ]
    
    input_pdf = r"C:\Users\yunis\바탕 화면\test" # 실제 PDF 파일 이름으로 변경
    output_dir = r"C:\Users\yunis\바탕 화면\사업설명서_원본"  # 출력 디렉토리
    split_pdf(input_pdf, output_dir, ranges)