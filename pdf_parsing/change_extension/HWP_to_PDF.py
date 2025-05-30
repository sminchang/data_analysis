# 윈도우와 한글(최신 버전) 설치가 되어있어야함
# hwp 추출 후 pdf로 변환하는 파이썬 라이브러리들은 2차 가공을 거치기 때문에 신뢰하기 어려움
# win32com은 윈도우가 한글 프로그램을 직접 제어하여 pdf 변환 기능을 자동 수행함
# win32com의 saveAs()함수로 간단하게 변환할 수 있는데, 모아찍기(2쪽씩) 옵션 해제가 안됨
# PrintToPDF 액션은 pdf 변환 옵션을 제어할 수 있어, 모아찍기 해제 후 변환할 수 있어 사용
# 테스트를 통해 누락되는 문서가 없는지 확인해가며 time.sleep()을 PC 성능에 맞게 조절해서 사용해야함

# HWP 파일이 매우 큰 경우, 로딩이나 메모리 관련 최적화가 필요할 수 있는데, 
# GUI로 직접 변환할 경우 이를 사용자 환경에 맞게 동적으로 최적화하지만, 
# API 호출은 이 과정을 단축해 기본 설정만 사용해서 오류가 날 수 있음

import os
import time
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
            
            # HWP 파일 열기
            hwp.Open(src)
            
            # PrintToPDF 액션 생성 및 설정
            action = hwp.CreateAction("PrintToPDF")
            pSet = action.CreateSet()
            action.GetDefault(pSet) # 기본 프린터 설정 가져오기
            
            # PDF 변환 옵션 설정
            pSet.SetItem("PrintMethod", 0)  # 기본 인쇄 방식
            pSet.SetItem("PrintPageOption", 1)  # 1페이지씩 인쇄
            pSet.SetItem("FileName", dst)  # 저장할 PDF 파일 경로 지정
            
            # PDF로 변환 실행
            action.Execute(pSet)

            #스핀락(비동기 동작 대기)
            while True:
                if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                    try:
                        # 파일 열기 시도로 완료 확인
                        with open(pdf_path, 'rb') as f:
                            f.read(1)  # 1바이트만 읽어보기
                        break  # 성공하면 루프 탈출
                    except:
                        pass

                
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