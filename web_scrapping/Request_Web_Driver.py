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
import time
import pandas as pd #pip install pandas, pip install openpyxl
import re
import os


# 드라이버 설정
service = ChromeService(executable_path=ChromeDriverManager().install()) # 크롬 드라이버 다운로드
options = webdriver.ChromeOptions()
# options.add_argument('--headless=new')  # 브라우저 화면 미출력 설정
options.add_argument('--no-sandbox') # sandbox 모드에서 실행되지 않도록 설정
options.add_argument('--disable-dev-shm-usage') # /dev/shm 메모리 사용을 비활성화하여 크롬 안정성 향상
driver = webdriver.Chrome(service=service, options=options) # 드라이버로 크롬 브라우저 할당

# 페이지 요청
url = "https://www.law.go.kr/lsTrmSc.do?menuId=13&subMenuId=65&query=#AJAX"
driver.get(url)

# 데이터를 저장할 리스트
data = []

# 용어목록 갯수 확인
rows = WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.XPATH, '//*[@id="lelistwrapLeft"]/ul/li')) # DOM에 로딩될 때까지 대기(최대 10초 설정)
)

# 사이트 내 모든 페이지 순회
for page_num in range(1, 2):
    # 한 페이지 내 모든 목록 순회
    for i in range(0, 12):#len(rows)+1):
        try:
            title_element = driver.find_element(By.XPATH, f'//*[@id="click{i}"]') # HTML 요소 추출
            title = title_element.get_attribute('title') # 태그 속성 추출
            title_element.click() #클릭 이벤트 적용
        
            dl_rows = WebDriverWait(driver, 3).until(
            EC.presence_of_all_elements_located((By.XPATH, f'//*[@id="contentBody"]/dl')) # DOM에 로딩될 때까지 대기(최대 10초 설정)
            )
            if dl_rows == 1:
                content = WebDriverWait(driver, 3).until(
                    EC.visibility_of_element_located((By.XPATH, f'//*[@id="contentBody"]/dl/dd[1]'))
                ).text
                ref_content = driver.find_element(By.XPATH, f'//*[@id="contentBody"]/dl/dd[2]').text
                ref_link = driver.find_element(By.XPATH, f'//*[@id="contentBody"]/dl/dd[2]/a[1]').get_attribute('href')

            else:
                for content_num in range(1, len(dl_rows)+1):
                    # #클릭 이벤트로 생성된 팝업창 로딩까지 대기
                    content = WebDriverWait(driver, 3).until(
                        EC.visibility_of_element_located((By.XPATH, f'//*[@id="contentBody"]/dl[{content_num}]/dd[1]'))
                    ).text
                    ref_content = driver.find_element(By.XPATH, f'//*[@id="contentBody"]/dl[{content_num}]/dd[2]').text
                    ref_link = driver.find_element(By.XPATH, f'//*[@id="contentBody"]/dl[{content_num}]/dd[2]/a[1]').get_attribute('href')

            row_data = {
                "용어명": title,
                "용어뜻": content,
                '참조명': ref_content,
                '참조링크': ref_link
                }
            data.append(row_data)

        except Exception as e:
            print(f"Error : {e}")
            continue

    # 다음 페이지 이동 스크립트 실행
    try:
        page_num += 1
        driver.execute_script(f"movePage('{page_num}');")

    except Exception as e:
        print(f"Error: {e}")
        break

driver.quit()

# 데이터프레임 생성
df = pd.DataFrame(data)

# Excel 파일로 저장
df.to_excel('driver_data.xlsx', index=False)
