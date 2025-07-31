import os
import time
import win32com.client  # pip install pywin32

# 한글 프로그램 기반 PDF 인쇄 방식 사용
# "인쇄 진행 중" 팝업 창 제거 실패 -> 해당 코드 실행 중 다른 작업 못함.

def convert_hwp_to_pdf(hwp_path, pdf_path):
    """HWP 파일들을 PDF로 변환하는 함수 (실패시 3번까지 재시도)"""
    
    if not os.path.exists(hwp_path):
        print(f"HWP 파일 경로가 존재하지 않습니다: {hwp_path}")
        return
    
    # PDF 저장 경로가 없으면 생성
    os.makedirs(pdf_path, exist_ok=True)

    # HWP API 로드
    hwp = win32com.client.gencache.EnsureDispatch('HWPFrame.HwpObject')
    hwp.RegisterModule('FilePathCheckDLL', 'FilePathCheckerModule')

    try:
        # HWP 파일 목록 가져오기
        file_list = [f for f in os.listdir(hwp_path) if f.lower().endswith(('.hwp', '.hwpx'))]
        
        if not file_list:
            print("변환할 HWP 파일이 없습니다.")
            return
        
        print(f"총 {len(file_list)}개의 파일을 변환합니다.")
        
        success_count = 0
        fail_count = 0
        
        for i, file in enumerate(file_list, 1):
            print(f"[{i}/{len(file_list)}] 변환 중: {file}")
            
            # 각 파일마다 최대 3번 시도
            success = False
            for attempt in range(1, 4): 

                success = process_single_file(hwp, hwp_path, pdf_path, file, attempt)
                if success:
                    success_count += 1
                    break
                time.sleep(1)  # 재시도 전 잠시 대기
            
            if not success:
                print(f"  → 실패: {file}")
                fail_count += 1
        
        print(f"\n변환 완료: 성공 {success_count}개, 실패 {fail_count}개")
                
    except Exception as e:
        print(f'스크립트 실행 중 오류 발생: {str(e)}')
    finally:
        # HWP 종료
        try:
            hwp.Quit()
            print("HWP 프로그램을 종료했습니다.")
        except:
            print("HWP 프로그램 종료 중 오류가 발생했습니다.")


def process_single_file(hwp, hwp_path, pdf_path, file, attempt):
    """단일 파일을 처리하고 성공/실패 여부를 반환"""
    try:
        pre, ext = os.path.splitext(file)
        src = os.path.join(hwp_path, file)
        dst = os.path.join(pdf_path, pre + ".pdf")
        
        # 이미 변환된 파일이 있으면 스킵 (크기가 0보다 큰 경우만)
        if os.path.exists(dst):
            file_size = os.path.getsize(dst)
            if file_size > 0:
                if attempt == 1:
                    print(f"  → 이미 존재함. 스킵: {pre}.pdf ({file_size:,} bytes)")
                return True
            else:
                print(f"  → 0KB 파일 발견. 다시 변환: {pre}.pdf")
                try:
                    os.remove(dst)  # 0KB 파일 삭제
                except:
                    pass
        
        # HWP 파일 열기
        hwp.Open(src)
        
        # PrintToPDF 액션 생성 및 설정
        action = hwp.CreateAction("PrintToPDF")
        pSet = action.CreateSet()
        action.GetDefault(pSet)  # 기본 프린터 설정 가져오기
        
        # PDF 변환 옵션 설정
        pSet.SetItem("PrintMethod", 0)  # 기본 인쇄 방식
        pSet.SetItem("PrintPageOption", 1)  # 1페이지씩 인쇄
        pSet.SetItem("FileName", dst)  # 저장할 PDF 파일 경로 지정
        
        # PDF로 변환 실행
        action.Execute(pSet)
        
        # 변환 완료 대기 (스핀락)
        max_wait_time = 10
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            if os.path.exists(dst) and os.path.getsize(dst) > 0:
                try:
                    # 파일 열기 시도로 완료 확인
                    with open(dst, 'rb') as f:
                        f.read(1024)  # 1KB 읽어보기
                    file_size = os.path.getsize(dst)
                    print(f"  → 완료: {pre}.pdf ({file_size:,} bytes)")
                    return True
                except:
                    time.sleep(0.5)
            else:
                time.sleep(0.5)
        
        return False
        
    except Exception as e:
        print(f"  → 오류: {str(e)}")
        return False 
    finally:
        # 현재 문서 닫기
        try:
            hwp.Clear(1)
        except:
            pass

if __name__ == "__main__":
    # 실행 파라미터 설정
    hwp_path = r"C:\Users\yunis\Desktop\4. 예산안(추경)사업설명자료(세부사업기준)\2025년(본예산및추경)\2025년 제1회 추경"
    pdf_path = r"C:\Users\yunis\Desktop\2025_본청_추경_pdf" 

    convert_hwp_to_pdf(hwp_path, pdf_path)