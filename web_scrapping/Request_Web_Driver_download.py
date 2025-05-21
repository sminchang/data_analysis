#pip install selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager #pip install webdriver-manager
import os
import time
import pandas as pd #pip install pandas, pip install openpyxl

# 다운로드 경로 설정 (여기에 원하는 경로 입력)
download_dir = r"C:\Users\yunis\Desktop\testInput"  # 원하는 경로로 변경하세요
os.makedirs(download_dir, exist_ok=True)  # 경로가 없으면 생성

# 드라이버 설정
service = ChromeService(executable_path=ChromeDriverManager().install()) # 크롬 드라이버 다운로드
options = webdriver.ChromeOptions()

# 다운로드 디렉토리 설정
prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,  # 다운로드 대화 상자 표시 안 함
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)
# options.add_argument('--headless=new')  # 브라우저 화면 미출력 설정
options.add_argument('--no-sandbox') # sandbox 모드에서 실행되지 않도록 설정
options.add_argument('--disable-dev-shm-usage') # /dev/shm 메모리 사용을 비활성화하여 크롬 안정성 향상
driver = webdriver.Chrome(service=service, options=options) # 드라이버로 크롬 브라우저 할당

# 페이지 요청
url = "https://www.ibk.co.kr/ir/bylaws/notifyListBylaws.ibk?pageId=IR07040200"
driver.get(url)

# 데이터를 저장할 리스트
data = []

# 용어목록 갯수 확인
rows = WebDriverWait(driver,10).until(
    EC.presence_of_all_elements_located((By.XPATH, '//*[@id="contents_in"]/div/div[1]/div/table/tbody/tr'))
    )

# 사이트 내 모든 페이지 순회
for page_num in range(2, 10):

    # 한 페이지 내 모든 목록 순회
    for i in range(1, len(rows)+1):
        try:
            title_element = driver.find_element(By.XPATH, f'//*[@id="contents_in"]/div/div[1]/div/table/tbody/tr[{i}]/td[2]/a') # HTML 요소 추출
            title_element.click() #클릭 이벤트 적용
            
            time.sleep(2)

            # 해당 경로 유뮤 파악
            if len(driver.find_elements(By.XPATH, '//*[@id="contents_in"]/div/table/tbody/tr[3]/td/dl/dd/ul/li')) > 0:

                # Ajax 로딩 완료를 기다리는 부분
                dl_rows = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, '//*[@id="contents_in"]/div/table/tbody/tr[3]/td/dl/dd/ul/li'))
                )

                for content_num in range(1, len(dl_rows)+1):
                    # 클릭 이벤트로 생성된 팝업창 로딩까지 대기
                    content = driver.find_element(By.XPATH,f'//*[@id="contents_in"]/div/table/tbody/tr[3]/td/dl/dd/ul/li[{content_num}]/a').click()
            
            driver.back() # 페이지 뒤로가기

        except Exception as e:
            print(f"Error : {e}")
            continue

    # 다음 페이지 이동 스크립트 실행
    try:
        driver.execute_script(f"getListData('{page_num}');")

    except Exception as e:
        print(f"Error: {e}")
        break

driver.quit()
