from PyPDF2 import PdfReader, PdfWriter  # pip install PyPDF2
import os

def pdf_division(input_path, output_path, division_standard):
    # output 폴더가 없으면 생성
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # 폴더 내 모든 파일 순회
    for file_name in os.listdir(input_path):
        if file_name.endswith('.pdf'):
            # 파일 경로 설정
            file_path = os.path.join(input_path, file_name)
            source_name = os.path.splitext(file_name)[0]
                        
            try:
                # PyPDF2로 파일 열기
                pdf_reader = PdfReader(file_path)
                pdf_writer = PdfWriter()
                total_pages = len(pdf_reader.pages)
                
                # 파일 내 모든 페이지 순회
                for page_num in range(total_pages):
                    try:
                        pdf_writer.add_page(pdf_reader.pages[page_num])

                        if((page_num + 1) % division_standard == 0):
                            output_file = os.path.join(output_path, f"{source_name}_{page_num+1}.pdf")
                            with open(output_file, 'wb') as output:
                                pdf_writer.write(output)
                            pdf_writer = PdfWriter()

                    except Exception as page_error:
                        print(f"오류 페이지: {page_num + 1} / 오류 내용: {str(page_error)}")
                    
                output_file = os.path.join(output_path, f"{total_pages}.pdf")
                with open(output_file, 'wb') as output:
                    pdf_writer.write(output)

            except Exception as e:
                print(f"error: {str(e)} in file: {file_name}")

# 실행
division_standard = 3000  # 분할 기준 페이지 번호
input_path = r'C:\Users\User\Desktop\test'
output_path = r'C:\Users\User\Desktop\test'  # 저장될 경로 지정
pdf_division(input_path, output_path, division_standard)

            
