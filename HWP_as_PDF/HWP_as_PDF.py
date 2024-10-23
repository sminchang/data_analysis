# 한글 설치가 안된 상태에서는 사용할 수 없는 hwpAsPdf 방식임
# hwp 추출 후 pdf로 변환하는 파이썬 라이브러리들은 2차 가공을 거치기 때문에 신뢰하기 어려움
# win32com은 윈도우가 한글을 직접 제어하여 pdf 변환 기능을 자동 수행함
# win32com에서 제공하는 saveAs()함수로 간단하게 변환할 수 있는데, 모아찍기(2쪽씩) 옵션 해제가 안되는 문제가 있음
# PrintToPDF 액션은 pdf 변환 옵션을 제어할 수 있어, 모아찍기 해제 후 변환할 수 있음 

import os
import win32com.client #pip install pywin32

def convert_hwp_to_pdf(hwp_path, pdf_path):
    # PDF 저장 경로가 없으면 생성
    os.makedirs(pdf_path, exist_ok=True)

    # HWP API 로드
    hwp = win32com.client.gencache.EnsureDispatch('HWPFrame.HwpObject')
    hwp.RegisterModule('FilePathCheckDLL', 'FilePathCheckerModule')

    try:
        # HWP 파일 목록 가져오기
        file_list = [f for f in os.listdir(hwp_path) if f.lower().endswith(('.hwp','.hwpx'))]
        
        for file in file_list:
            pre, ext = os.path.splitext(file)
            src = os.path.join(hwp_path, file)
            dst = os.path.join(pdf_path, pre + ".pdf")
            
            try:
                # HWP 파일 열기
                hwp.Open(src)
                
                # PrintToPDF 액션 생성 및 설정
                action = hwp.CreateAction("PrintToPDF")
                pSet = action.CreateSet()
                
                # 기본 프린터 설정 가져오기
                action.GetDefault(pSet)
                
                # PDF 변환 옵션 설정
                pSet.SetItem("PrintMethod", 0)  # 기본 인쇄 방식
                pSet.SetItem("PrintPageOption", 1)  # 1페이지씩 인쇄
                pSet.SetItem("FileName", dst)  # 저장할 PDF 파일 경로 지정
                
                # PDF로 변환 실행
                action.Execute(pSet)
                print(f'변환 완료: {src} -> {dst}')
                
            except Exception as e:
                print(f'변환 실패: {src}. 오류: {str(e)}')
            finally:
                # 열린 문서 닫기
                hwp.Clear(3)  # 3 = all documents
                
    except Exception as e:
        print(f'스크립트 실행 중 오류 발생: {str(e)}')
    finally:
        # HWP 종료
        hwp.Quit()
        print("모든 변환 작업이 완료되었습니다.")


# 실행 파라미터 설정
hwp_path = r'c:\python\repos_python\downloads'  # 변환할 hwp 파일들이 있는 경로
pdf_path = r'c:\python\repos_python\asPDFs'  # 변환된 pdf 파일들을 저장할 경로

# 변환 실행
convert_hwp_to_pdf(hwp_path, pdf_path)
