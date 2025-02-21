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
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager #pip install webdriver-manager

import datetime
import time
import re
import pandas as pd #pip install pandas, pip install openpyxl


# 데이터를 저장할 리스트
data = []

# 드라이버 설정
service = ChromeService(executable_path=ChromeDriverManager().install()) # 크롬 드라이버 다운로드
options = webdriver.ChromeOptions()
options.add_argument('--headless=new')  # 브라우저 화면 미출력 설정
options.add_argument('--no-sandbox') # sandbox 모드에서 실행되지 않도록 설정
options.add_argument('--disable-dev-shm-usage') # /dev/shm 메모리 사용을 비활성화하여 크롬 안정성 향상
driver = webdriver.Chrome(service=service, options=options) # 드라이버로 크롬 브라우저 할당


def bill_assembly_scrapping(from_date,today,from_date_daeNum,today_daeNum):
    # 페이지 요청
    url = "https://likms.assembly.go.kr/bill/BillSearchDetail.do"
    driver.get(url)


    # 상세검색-특정기간 내 '국정감사 결과보고' 검색
    srch_form = driver.find_element(By.ID, "srchForm")
    billName_input = srch_form.find_element(By.NAME, 'billName')
    dateFrom_input = srch_form.find_element(By.NAME, 'dateFrom')
    dateTo_input = srch_form.find_element(By.NAME, 'dateTo')
    ageFrom_select = Select(srch_form.find_element(By.NAME, 'ageFrom'))
    ageTo_select = Select(srch_form.find_element(By.NAME, 'ageTo'))
    billName_input.send_keys('국정감사 결과보고')
    dateFrom_input.send_keys(f"{from_date}") # 날짜형식 2012-01-02
    dateTo_input.send_keys(f"{today}") # 날짜형식 2012-01-02
    ageFrom_select.select_by_value(f"{from_date_daeNum}")
    ageTo_select.select_by_value(f"{today_daeNum}")
    # 검색된 페이지로 전환
    driver.find_element(By.XPATH,'/html/body/div/div[2]/div[2]/div/div[2]/button[1]').click()

    # 페이지네이션 횟수 찾기
    total_rows = driver.find_element(By.XPATH, '/html/body/div/div[2]/div[2]/div/p/span').text
    total_rows = re.match(r"(?:.*\(으\)로 총)(\d+)(?:건이 검색.*)", total_rows).group(1)
    total_page = int(total_rows)//10
    total_page = total_page + 1 if int(total_rows)%10 > 0 else total_page
    for page_num in range(2, total_page+2):

    # 용어목록 갯수 확인
        current_rows = WebDriverWait(driver,10).until(
            EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/div[2]/div[2]/div/div[2]/table/tbody/tr'))
            )
        
        for i in range(1,len(current_rows)+1):

            try:
                driver.find_element(By.XPATH,f'/html/body/div/div[2]/div[2]/div/div[2]/table/tbody/tr[{i}]/td[2]/div[2]/a').click()
                billId = driver.find_element(By.XPATH,'/html/body/div/div[2]/div[2]/div/div[3]/div/table/tbody/tr/td[1]').text
                submitDate = driver.find_element(By.XPATH,'/html/body/div/div[2]/div[2]/div/div[3]/div/table/tbody/tr/td[2]').text
                chairName = driver.find_element(By.XPATH, '/html/body/div/div[2]/div[2]/div/div[3]/div/table/tbody/tr/td[3]').text
                chairName_match = re.match(r"(.*위원)(.*)",chairName)
                commName = f"{chairName_match.group(1)}회" if chairName_match else ""
                try:
                    try:
                        href = driver.find_element(By.XPATH,'/html/body/div/div[2]/div[2]/div/div[3]/div/table/tbody/tr/td[4]/a[1]').get_attribute('href')
                    except NoSuchElementException: # 접수된 첨부 파일은 없고, 심사된 첨부 파일은 있는 경우
                        href = driver.find_element(By.XPATH,'/html/body/div/div[2]/div[2]/div/div[5]/div[1]/table/tbody/tr/td[6]/a[1]').get_attribute('href')
                    href_match = re.match(r"javascript:openBillFile\('(.*?)','(.*?)','(.*?)'\);",href)
                    hwp_link = f"{href_match.group(1)}?bookId={href_match.group(2)}&type=0"
                    pdf_link = f"{href_match.group(1)}?bookId={href_match.group(2)}&type=1"
                except Exception: #결과보고서의 채택 건만 있고, 결과보고서는 첨부되지 않은 경우
                    hwp_link = ""
                    pdf_link = ""
            
                row_data = {
                    "의안번호": billId,
                    "소관위원회명": commName,
                    "제안일자": submitDate,
                    'hwp_link': hwp_link,
                    'pdf_link': pdf_link
                    }
                data.append(row_data)

                driver.back()

            except Exception as e:
                print(f"{billId} find_element Error : {e}")
                continue

        # 다음 페이지 이동 스크립트 실행
        try:
            time.sleep(1)
            driver.execute_script(f"GoPage('{page_num}');")

        except Exception as e:
            print(f"{page_num} pagination Error: {e}")
            break

    driver.quit()

if __name__ == "__main__":

    # batch 용도, 기본 세팅값 (우선 15일 주기 insert 생각하고 작성)
    # today = datetime.date.today()
    # from_date = today - datetime.timedelta(days=15)
    # today_daeNum = (today.year - 1988) // 4 + 13 # 1988년 13대를 기준점으로 현재 연도의 제안대수 계산 (1988년부터 4년 주기가 확보되었기 때문)
    # from_date_daeNum =(from_date.year - 1988) // 4 + 13
    # bill_assembly_scrapping(from_date,today,from_date_daeNum,today_daeNum)

    # 과거 데이터 일괄 수집, 초기 수집 후 주석 처리
    bill_assembly_scrapping("1948-01-01","2024-12-31","01","22")

    # 데이터프레임 생성
    df = pd.DataFrame(data)

    # Excel 파일로 저장
    df.to_excel('국정감사_결과보고서.xlsx', index=False)