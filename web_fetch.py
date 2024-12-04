from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import json
from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.edge.service import Service
# from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium.common.exceptions import NoSuchElementException, UnexpectedAlertPresentException, TimeoutException
from selenium.common.exceptions import StaleElementReferenceException, ElementNotInteractableException
from bs4 import BeautifulSoup as bs
import urllib.request
import re
import os
import sys
from datetime import date, datetime
import time
import openpyxl
from inspect import currentframe, getframeinfo
from shutil import copyfile
from PySide6.QtCore import QFileSystemWatcher, QObject
from pathlib import Path
import readchar
import subprocess
# selenium 4
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from datetime import datetime
import random
import xlwings as xw

def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' +  directory)

class WEBManipulator(QObject):
    def __init__(self, position, size, download_folder, loading_wait_time, headless=False):

        self.position = position
        self.size = size
        self.download_folder = download_folder
        self.headless = headless
        self.driver = None

        self.open_browser(self.position, self.size, self.download_folder, self.headless)

        self.wait_time = 10
        self.wait_time_autocomplete = 5
        self.wait_time_viewmore = 5

        self.category = {}

        if '-' in loading_wait_time:
            [self.loading_wait_time_min, self.loading_wait_time_max] = [int(x) for x in loading_wait_time.split('-')]
        else:
            self.loading_wait_time_min = int(loading_wait_time)
            self.loading_wait_time_max = self.loading_wait_time_min
    
    # destructor
    def __del__(self):
        print('WEBManipulator.__del__')
        if self.driver:
            self.driver.quit()
            self.driver = None
        # subprocess.call("TASKKILL /f  /IM  CHROME.EXE")

    def open_browser(self, position, size, download_folder, headless=True):
        print('WEBManipulator.open_browser')
        # s = Service("chromedriver.exe")   # Chrome
        # s = Service("msedgedriver.exe") # Edge
        
        # s = Service("geckodriver.exe")    # Firefox 사용시 필요없음
        # options = webdriver.ChromeOptions()
        # options = webdriver.FirefoxOptions()
        options = Options()
        if headless == True:
            options.add_argument('headless')
        # options.add_argument('--window-size=1000,800')
        # options.add_argument('--start-maximized')
        # options.add_argument("--mute-audio")    
        # options.add_argument('disable-gpu') # Firefox 사용시 사용불가

        # options.binary_location = "C:\\\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # default 경로가 아닌 경우 필요
        # options.add_argument('--headless')
        options.add_argument('--incognito') # 시크릿모드
        # optional
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-setuid-sandbox')
        # optional
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        # options.add_argument("download.default_directory=D:/Users/jieun/work/soomgo/029. easywinner/download")    # download folder setting option #1 not work
        options.add_experimental_option("excludeSwitches", ["enable-logging"])  # Firefox 사용시 사용불가

        # user_agent = UserAgent().random
        # print(user_agent)
        # user_agent = user_agent.replace('Mobile', '')
        # options.add_argument(f'user-agent={user_agent}')
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
        options.add_argument(f'user-agent={user_agent}')

        caps = DesiredCapabilities.CHROME
        caps["goog:loggingPrefs"] = {"performance":"ALL"}

        # https://stackoverflow.com/questions/35331854/downloading-a-file-at-a-specified-location-through-python-and-selenium-using-chr
        download_folder = download_folder.replace('/', '\\')
        prefs = {'download.default_directory' : download_folder}    # download folder setting option #2
        options.add_experimental_option('prefs', prefs)

        # define the proxy address and port
        # proxy = "67.43.236.21:8307"        
        # options.add_argument(f"--proxy-server={proxy}")

        if self.driver:
            self.driver.quit()
            self.driver = None

        # self.driver = webdriver.Chrome(options=options, service=s)
        # self.driver = webdriver.Edge(options=options, service=s)
        # self.driver = webdriver.Chrome(ChromeDriverManager().install(),options=options)
        # self.driver = webdriver.Chrome(".\\chromedriver.exe")
        driver_path = ChromeDriverManager().install()
        print(driver_path)
        correct_driver_path = os.path.join(os.path.dirname(driver_path), "chromedriver.exe")
        self.driver = webdriver.Chrome(options=options, service=ChromeService(correct_driver_path), desired_capabilities=caps)

        self.driver.implicitly_wait(1)

        self.driver.set_window_position(position[0], position[1], windowHandle = 'current')
        self.driver.set_window_size(size[0], size[1])
        # self.driver.set_page_load_timeout(10)

        # Define the interceptor function to add or modify headers
        def interceptor(request):
            request.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
            # request.headers['Accept-Language'] = 'en-US,en;q=0.5'
            request.headers['Accept-Language'] = 'ko-KR,ko;q=0.9'

        # Set the request interceptor
        self.driver.request_interceptor = interceptor

    def quit(self):
        print('WEBManipulator.quit')
        self.driver.quit()

    def input(self, xpath, value):
        WebDriverWait(self.driver, self.wait_time).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        inp = self.driver.find_element(by=By.XPATH, value=xpath)
        inp.send_keys(value)
        return inp
    
    def clear(self, xpath):
        WebDriverWait(self.driver, self.wait_time).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        inp = self.driver.find_element(by=By.XPATH, value=xpath)
        inp.clear()

    def check_checkbox(self, xpath):
        WebDriverWait(self.driver, self.wait_time).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        inp = self.driver.find_element(by=By.XPATH, value=xpath)
        inp.click()

    def click(self, xpath):
        WebDriverWait(self.driver, self.wait_time).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        inp = self.driver.find_element(by=By.XPATH, value=xpath)
        inp.send_keys(Keys.ENTER)
        return inp

    def click_element(self, element):
        element.send_keys(Keys.ENTER)

    def select_by_visible_text(self, xpath, value):
        WebDriverWait(self.driver, self.wait_time).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        select = Select(self.driver.find_element(by=By.XPATH, value=xpath))
        select.select_by_visible_text(value)

    def select_by_value(self, xpath, value):
        WebDriverWait(self.driver, self.wait_time).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        select = Select(self.driver.find_element(by=By.XPATH, value=xpath))
        select.select_by_value(value)

    def select_by_index(self, xpath, value):
        WebDriverWait(self.driver, self.wait_time).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        select = Select(self.driver.find_element(by=By.XPATH, value=xpath))
        select.select_by_index(value)

    def get_select_current_option(self, xpath):
        WebDriverWait(self.driver, self.wait_time).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        select = Select(self.driver.find_element(by=By.XPATH, value=xpath))
        return select.first_selected_option.text

    def get_select_all_options(self, xpath):
        WebDriverWait(self.driver, self.wait_time).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        select = Select(self.driver.find_element(by=By.XPATH, value=xpath))
        return select.options

    def get_text(self, xpath):
        WebDriverWait(self.driver, self.wait_time).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        inp = self.driver.find_element(by=By.XPATH, value=xpath)
        return inp.text

    def set_url(self, url):
        print('set_url', url)
        self.driver.get(url)

    def print_msg(self, msg):
        current_time = time.time()
        time_elapsed = current_time - self.start_time
        hours, rem = divmod(time_elapsed, 3600)
        minutes, seconds = divmod(rem, 60)
        print(f"[경과시간 {int(hours):0>2}:{int(minutes):0>2}:{float(seconds):02.0f}] {msg}")

    def save_as_excel(self, mall_str, page, download_folder):
        if not os.path.exists(download_folder):
            createFolder(download_folder)
        chrome_download_folder = Path(download_folder).parent.parent.absolute()
        done = False
        while not done:
            for x in os.listdir(chrome_download_folder):
                if x.split('.')[-1] == 'xls':
                    chrome_download_file = str(chrome_download_folder).replace('\\','/') + '/' + x
                    if os.path.isfile(chrome_download_file):
                        os.rename(chrome_download_file, download_folder + '/' + str(page) + '.xls')
                        done = True
                        break
            time.sleep(1)
   
    def isint(self, str):
        try:
            int(str)
            return True
        except ValueError:
            return False

    def isfloat(self, num):
        try:
            float(num)
            return True
        except ValueError:
            return False

    def toFloat(self, str):
        if self.isfloat(str.replace(',','')):
            return float(str.replace(',',''))
        else:
            return str
        

    def num_with_unit(self, num, unit):
        if unit == "억원":
            return int(num.replace(',',''))*100000000
        elif unit == "만원":
            return int(num.replace(',',''))*10000
        else:
            return int(num.replace(',',''))

    def wait_loading(self, xpath, wait_time = 4):
        wait_time = self.loading_wait_time_min
        ret_msg = 'ok'
        print(f'wait_loading: {wait_time} sec')
        p = re.compile('display: (.+?);')
        inp = self.driver.find_element(by=By.XPATH, value=xpath)

        # wait for display block
        # time_start = time.time()
        # while True:
        #     style = inp.get_attribute('style')
        #     m = p.search(style)
        #     if m:
        #         if m.group(1) == 'block':
        #             break
        #     time.sleep(0.01)
        #     if time.time() - time_start > 5:
        #         print('5 sec timeout')
        #         break
        #     print('.',end='')
        #     sys.stdout.flush()
        time.sleep(wait_time)
        # wait for display none
        time_start = time.time()
        while True:
            try:
                style = inp.get_attribute('style')
                m = p.search(style)
                if m:
                    if m.group(1) == 'none':
                        break
                time.sleep(0.04)
                if time.time() - time_start > 5:
                    print('5 sec timeout')
                    ret_msg = 'timeout'
                    break
                print('-',end='')
                sys.stdout.flush()
            except UnexpectedAlertPresentException as e:
                print('UnexpectedAlertPresentException')
                print(e)
                # print("아무키나 누르시면 닫힙니다.")
                # k = readchar.readchar()
                continue
        return ret_msg

    # Function to get response body for each request
    def get_response_body(self, request_id):
        try:
            # Execute a DevTools command to get the response body
            body = self.driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
            return body.get("body", "")
        except Exception as e:
            # print(f"Could not get body for request ID {request_id}: {e}")
            # print(f"Could not get body for request ID {request_id}")
            return None
        
    def save_to_file(self, txt):
        filename = datetime.now().strftime("%Y-%m-%d %H%M%S")+".txt"
        fid = open(filename, "wb")
        fid.write(txt.encode('cp949', 'ignore'))
        fid.close()
        print(f"{filename} 파일이 저장되었습니다")

        # print(json.loads(txt))

    def naver_input_keyword(self, url, keyword):
        time.sleep(1)
        self.set_url(url)
        time.sleep(3)
        input_xpath = '//*[@id="gnb-gnb"]/div[2]/div/div[2]/div[1]/form/div/div/div/div/input'
        ele_input = self.input(input_xpath, keyword)
        return ele_input

    def proc_naver_related_keywords(self, url, keyword):
        results = set()

        ele_input = self.naver_input_keyword(url, keyword)
                 
        xpath_autocomplete = '//*[@id="gnb-gnb"]/div[2]/div/div[2]/div[1]/form/div/div[1]/div/div[2]/div/div[1]'
        try:
            print(f'{self.wait_time_autocomplete}초 동안 기다립니다')
            WebDriverWait(self.driver, self.wait_time_autocomplete).until(EC.element_to_be_clickable((By.XPATH, xpath_autocomplete)))
        except TimeoutException as te:
            print(f'[네이버] {keyword}의 연관검색어가 없습니다')
            ele_input.send_keys(Keys.ENTER)

            return results
        
        ele_div = self.driver.find_element(By.XPATH, xpath_autocomplete)
        time.sleep(2)
        # print(ele.get_attribute('innerHTML'))
        ele_ul = ele_div.find_element(By.TAG_NAME, "ul")
        items = ele_ul.find_elements(By.TAG_NAME, "li")
        for item in items:
            try:
                ele_a = item.find_element(By.TAG_NAME, "div").find_element(By.TAG_NAME, "a")
                ele_span = ele_a.find_elements(By.TAG_NAME, "span")[1] # [0]=아이콘 [1]=자동완성 [2]=최근검색일자 또는 아이콘
            except NoSuchElementException as nee:
                continue
            text = ele_span.text
            print(text)
            results.add(text)

        ele_input.send_keys(Keys.ENTER)

        # 더보기 클릭
        xpath = '//*[@id="container"]/div[1]/div/button'
        try:
            print(f'{self.wait_time_viewmore}초 동안 기다립니다')
            WebDriverWait(self.driver, self.wait_time_viewmore).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        except TimeoutException as te:
            print(f'[네이버] {keyword}의 더보기가 없습니다')

            return results

        self.click(xpath)

        ele_div = self.driver.find_element(By.XPATH, '//*[@id="container"]/div[1]/div')
        ele_ul = ele_div.find_element(By.TAG_NAME, "ul")
        items = ele_ul.find_elements(By.TAG_NAME, "li")
        for item in items:
            ele_a = item.find_element(By.TAG_NAME, "a")
            text = ele_a.text
            print(text)
            results.add(text)

        print(results)
        return results
    
    def get_split(self, txt):
        manutags = []
        if txt != None and len(txt.strip()) > 0:
            manutags += txt.split(',')
        return manutags

    def get_manu(self):
        manutags = []
        # Keep track of request IDs that have completed
        completed_requests = {}        
        # Iterate over performance logs to find responseReceived and loadingFinished events
        for entry in self.driver.get_log("performance"):
            log = json.loads(entry["message"])["message"]
            
            # Capture the responseReceived event
            if log["method"] == "Network.responseReceived":
                request_id = log["params"]["requestId"]
                url = log["params"]["response"]["url"]
                status = log["params"]["response"]["status"]
                
                # Only consider successful status codes
                if status == 200:
                    # print(f"Response received for URL: {url} with status {status}")
                    completed_requests[request_id] = url
            
            # Capture loadingFinished event for completed responses
            elif log["method"] == "Network.loadingFinished":
                request_id = log["params"]["requestId"]
                
                # Check if we have a valid request to get response body for
                if request_id in completed_requests:
                    response_body = self.get_response_body(request_id)
                    if response_body:
                        url = completed_requests[request_id]
                        if "productSetFilter" in response_body[:100]:
                            # self.save_to_file(response_body)
                            json_txt = response_body
                            # print(f"Response Body for {url} (Request ID {request_id}):\n{response_body[:500]}...")  # Print first 500 characters
                    # Remove processed requests
                    completed_requests.pop(request_id, None)

        if 'json_txt' in locals():
            json_result = json.loads(json_txt)
            manuTag_cnt = 0
            if len(json_result['searchAdResult']['adUnits']) > 0:
                cnt = len(json_result['searchAdResult']['adUnits'][0]['ads'])
                manuTag_cnt += cnt
                for i in range(0, cnt):
                    manutags += self.get_split(json_result['searchAdResult']['adUnits'][0]['ads'][i]['manuTag'])
            try:
                cnt = len(json_result['searchAdResult']['products'])
                manuTag_cnt += cnt
                for i in range(0, cnt):
                    manutags += self.get_split(json_result['searchAdResult']['products'][i]['manuTag'])
            except KeyError as ke:
                pass

            try:
                cnt = len(json_result['shoppingResult']['products'])
                manuTag_cnt += cnt
                for i in range(0, cnt):
                    manutags += self.get_split(json_result['shoppingResult']['products'][i]['manuTag'])
            except KeyError as ke:
                pass
            print(f"{manuTag_cnt}개 찾음, {','.join(manutags)}")
            return {"cnt":manuTag_cnt, "tags":manutags}
        else:
            print('마누태그 가져오기 에러')
            return {"cnt":0, "tags":[]}

    def naver_click_naverpay(self, keyword):
        try:
            # 네이버페이 클릭
            xpath_naverpay = '//*[@id="content"]/div[1]/div[1]/ul/li[3]/a'
            ele_naverpay = self.click(xpath_naverpay)
        except TimeoutException as te:
            print(f"[네이버] {keyword}의 검색결과가 없습니다.")
            return False
        
        while True:
            time.sleep(1)
            print('.', end='')
            if ele_naverpay.text.strip() != '네이버페이선택됨':
                print(ele_naverpay.text.strip())
                break
        time.sleep(2)
        return True

    def proc_naver_manutag(self, url, keyword, skip):
        if not skip:
            self.naver_input_keyword(url, keyword)
        time.sleep(2)
        if not self.naver_click_naverpay(keyword):
            return []

        # manu tag
        retry = 0
        while True:
            manutag1 = self.get_manu()
            if manutag1["cnt"] > 0:
                print(f"태그 {manutag1['cnt']}개를 찾았습니다")
                break
            else:
                if retry >= 10:
                    print('마누태그(1) 10회시도 실패')
                    break
                print(f'마누태그(1)를 다시 읽습니다({retry}회/최대10회 시도)')
                time.sleep(1)
                ele_input = self.naver_input_keyword(url, keyword)
                ele_input.send_keys(Keys.ENTER)
                time.sleep(2)
                self.naver_click_naverpay(keyword)
                retry += 1

        # '마누2'(네이버페이+해외직구)
        xpath = '//*[@id="content"]/div[1]/div[1]/div[2]/div[2]/div[2]/a'
        self.click(xpath)
        time.sleep(1)

        xpath = '//*[@id="content"]/div[1]/div[1]/div[2]/div[2]/div[2]/ul/li[2]/a'
        self.click(xpath)
        time.sleep(2)

        while True:
            manutag2 = self.get_manu()
            if manutag2["cnt"] > 0:
                print(f"태그 {manutag2['cnt']}개를 찾았습니다")
                break
            else:
                print('마누태그(2)를 다시 읽습니다')
                xpath_deselect_all = '//*[@id="container"]/div/div[2]/div[2]/a[1]'
                self.click(xpath_deselect_all)

                xpath = '//*[@id="content"]/div[1]/div[1]/div[2]/div[2]/div[2]/a'
                self.click(xpath)
                time.sleep(1)

                xpath = '//*[@id="content"]/div[1]/div[1]/div[2]/div[2]/div[2]/ul/li[2]/a'
                self.click(xpath)
                time.sleep(2)


        print(manutag1["tags"]+manutag2["tags"])
        return manutag1["tags"]+manutag2["tags"]

    # cmd='연관', '마누'
    def proc_naver(self, url, keyword='홍차', cmd=['연관']):
        ret = {}
        if '연관' in cmd:
            ret['연관'] = self.proc_naver_related_keywords(url, keyword)            
        if '마누' in cmd:
            if '연관' in cmd:
                ret['마누'] = self.proc_naver_manutag(url, keyword, skip=True) # '연관' 명령 처리시 페이지 로딩이 되었으므로 키워드 입력 생략
            else:
                ret['마누'] = self.proc_naver_manutag(url, keyword, skip=False)
        return ret


    def proc_coupang(self, url, keyword='홍차'):

        for i in range(0,100):
            while True:
                try:
                    # do stuff
                    random_sec = random.uniform(self.loading_wait_time_min, self.loading_wait_time_max)
                    print(random_sec)
                    time.sleep(random_sec)
                    self.set_url(f"https://www.coupang.com/np/search?q={keyword}")
                    # self.set_url(url)
                    # 로고를 찾아서 페이지 로딩을 대신 확인
                    xpath = '//*[@id="sticky-wrapper"]/section/div[1]/span/a/img'
                    ele_logo = self.driver.find_element(By.XPATH, xpath)

                except NoSuchElementException as te:
                    print('[쿠팡]timeout - 다시 시도합니다.')
                    continue

                try:
                    # random_sec = random.uniform(8, 10)
                    # print(random_sec)
                    # time.sleep(random_sec)

                    # input_xpath = '//*[@id="headerSearchKeyword"]'
                    # WebDriverWait(self.driver, self.wait_time).until(EC.element_to_be_clickable((By.XPATH, input_xpath)))
                    # ele_input = self.driver.find_element(By.XPATH, input_xpath) 
                    # self.input(input_xpath, keyword)
                    # random_sec = random.uniform(8, 10)
                    # print(random_sec)
                    # time.sleep(random_sec)
                    # ele_input.send_keys(Keys.ENTER)

                    ele_dl = self.driver.find_element(By.XPATH, '//*[@id="searchOptionForm"]/div[2]/div[2]/div[1]/dl')
                    ele_a = ele_dl.find_element(By.TAG_NAME, "dd")
                    items = ele_a.find_elements(By.TAG_NAME, "a")
                    ret = []
                    for item in items:
                        text = item.text
                        print(text)
                        ret.append(text)
                    return ret
                except NoSuchElementException as e:
                    print(f'[쿠팡] {keyword}의 연관검색어가 없습니다')
                    return []

    def remove_from_list(self, src, to_remove):
        for i in src[:]:
            if i in to_remove:
                src.remove(i)
        return src

    def count_duplicates(self, lst):
        seen = set()
        duplicates = set()
        for item in lst:
            if item in seen:
                duplicates.add(item)
            else:
                seen.add(item)
        dict_dup = {item: lst.count(item) for item in duplicates}
        dict_sorted = {k: v for k, v in sorted(dict_dup.items(), key=lambda item: item[1], reverse=True)}
        ret = []
        for it in dict_sorted.items():
            ret.append(f'{it[0]}({it[1]})')
        for it in list(seen):
            ret.append(f'{it}')
        return ret
        
    def proc_all_site(self, df, df_filter, filename, first_row):
        print('proc_all_site')
        self.start_time = time.time()
        row = first_row
        len_keywords = len(df.iloc[:,0].tolist())
        df['연관키워드'] = ['']*len_keywords
        df['마누태그'] = ['']*len_keywords

        if first_row == 2:
            workbook = xw.Book()
            sheet = workbook.sheets.active
            sheet.range("A1").value = "키워드"
            sheet.range("B1").value = "연관키워드"
            sheet.range("C1").value = "마누태그"
            workbook.save(filename)
        else:
            workbook = xw.Book(filename)
            sheet = workbook.sheets.active

        for keyword in df.iloc[first_row-2:,0].tolist():
            if len(keyword.strip()) == 0:
                row += 1
                continue
            # 연관키워드/마누 동시 처리
            self.print_msg(f'키워드 [{keyword}] 작업시작')
            ret1 = self.proc_naver('https://search.shopping.naver.com/search/all?query=', keyword, cmd=['연관', '마누'])
            ret2 = self.proc_coupang('', keyword)
            related_keywords = ','.join(self.remove_from_list(list(ret1['연관']) + ret2, df_filter['연관키워드 제외목록'].dropna().tolist()))
            manutag = ','.join(self.count_duplicates(self.remove_from_list(list(ret1['마누']), df_filter['마누태그 키워드 제외목록'].dropna().tolist())))
            df.at[row,'연관키워드'] = related_keywords
            df.at[row,'마누태그'] = manutag

            sheet.range(f'A{row}').value = keyword
            sheet.range(f'B{row}').value = related_keywords
            sheet.range(f'C{row}').value = manutag
            workbook.save(filename)

            row += 1

