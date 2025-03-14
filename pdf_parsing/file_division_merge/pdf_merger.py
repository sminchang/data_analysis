import os
from PyPDF2 import PdfMerger

def merge_pdfs_in_directory(input_dir, output_filename):
    # PDF 병합을 위한 PdfMerger 객체 생성
    merger = PdfMerger()
    
    # 디렉토리 내의 모든 PDF 파일 목록 가져오기
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    
    # 파일명 기준으로 정렬
    pdf_files.sort()
    
    # 각 PDF 파일을 병합
    for pdf_file in pdf_files:
        file_path = os.path.join(input_dir, pdf_file)
        merger.append(file_path)
        print(f"추가됨: {pdf_file}")
    
    # 병합된 PDF 저장
    merger.write(output_filename)
    merger.close()
    
    print(f"병합 완료! 결과 파일: {output_filename}")

# 사용 예
if __name__ == "__main__":
    # 'test' 폴더 내의 모든 PDF 파일 병합
    input_directory = r"C:\Users\yunis\바탕 화면\test"
    output_file = r"C:\Users\yunis\바탕 화면\test\merged_output.pdf"
    
    merge_pdfs_in_directory(input_directory, output_file)