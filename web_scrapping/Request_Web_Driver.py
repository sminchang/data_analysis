from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService

import time
import pandas as pd
import re
import os

# find_element()로 요소 찾기
# get_attribute()로 속성값 찾기


# 드라이버 설정 (webdriver_manager 사용)
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

# 테이블의 행 수 확인
rows = WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.XPATH, '//*[@id="lelistwrapLeft"]/ul/li')) # DOM에 로딩될 때까지 대기(최대 10초 설정)
)

# 사이트 내 모든 페이지 순회
while True:
    # 한 페이지 내 모든 목록 순회
    for i in range(0, len(rows)+1):
        try:
            title_element = driver.find_element(By.XPATH, f'//*[@id="click{i}"]') # HTML 요소 추출
            title = title_element.get_attribute('title') # 태그 속성 추출
            title_element.click() #클릭 이벤트 적용

            #클릭 이벤트로 생성된 팝업창 로딩까지 대기
            content = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, f'//*[@id="contentBody"]/dl/dd[1]'))
            ).text 

            #connect와 같은 팝업창이기에 별도 대기없이 추출출
            ref = driver.find_element(By.XPATH, f'//*[@id="contentBody"]/dl/dd[2]').text
            
            print(f"제목: {title}\n===========================\n")
            print(f"내용: {content}\n===========================\n")
            print(f"참조: {ref}\n===========================\n")

        except:
            continue

    # 다음 페이지 버튼 클릭
    try:
        next_page = driver.find_element(By.XPATH, f'//*[@id="listDiv"]/div[3]/a[1]')
        next_page.click()
    except:
        break

driver.quit()
