import time
import pandas as pd
import csv
import re
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# 웹드라이버 실행 시 옵션 추가 (유니코드 문제 해결)
chrome_options = Options()
chrome_options.add_argument("--disable-extensions")  # 확장 프로그램 비활성화
chrome_options.add_argument("--lang=ko-KR")  # 한국어 언어로 설정
chrome_options.add_argument("--no-sandbox")  # 보안 모드 비활성화
chrome_options.add_argument("--disable-dev-shm-usage")  # 메모리 관련 이슈 방지

url = 'https://zigzag.kr/categories/-1?title=%EC%9D%98%EB%A5%98&category_id=-1&middle_category_id=547&sort=200'
# WebDriver 경로 지정
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
driver.get(url)
time.sleep(2)  # 페이지 로딩 대기

# 스크롤하여 데이터 수집
scrolls = 9  # 원하는 만큼 스크롤 (조정 가능)
collected_links = set()  # 중복 방지를 위한 set()

for _ in range(scrolls):
    # 스크롤 내리기
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)  # 페이지가 로딩될 시간을 줌
    
    # 페이지 HTML 업데이트
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # 상품 링크 수집 (새로운 상품이 로딩되었을 가능성이 있으므로 계속 추가)
    links = soup.select("#__next > div.zds-themes.light-theme > div.css-xrh5h3.edi339y0 > main > section.css-j2fe9p.eeob9mf0 > div a")
    
    for link in links:
        product_url = link.get('href')
        if product_url and product_url.startswith('/catalog/products/'):
            collected_links.add(f'https://zigzag.kr{product_url}')  # 중복 제거 위해 set에 추가

# 최종 수집된 링크 확인
print(f"총 {len(collected_links)}개의 상품 링크를 수집했습니다.")

# 수집된 정보를 저장할 리스트
data = []

# 이미 저장된 CSV 파일 경로
csv_file = r'D:\0_Yebang\취업\포트폴리오\개인프로젝트\Shopping_mall_analyze\data\pants_info_reviews.csv'

# 기존 CSV 파일이 있으면 데이터 불러오기 (오류가 난 부분부터 크롤링을 재개하기 위함)
if os.path.exists(csv_file):
    df_existing = pd.read_csv(csv_file)
    # 이미 수집된 링크를 제외한 새로운 링크만 크롤링
    collected_links -= set(df_existing['링크'].dropna())
    print(f"기존 데이터가 {len(df_existing)}개 있으며, {len(collected_links)}개의 링크를 새로 크롤링합니다.")
    

# 상품 상세 정보 크롤링
for idx, full_url in enumerate(list(collected_links)):  # 모든 상품 링크를 크롤링
    try:
        driver.get(full_url)
        time.sleep(2)
        item_page = BeautifulSoup(driver.page_source, 'html.parser')

        brand_name = item_page.select_one('.css-gwr30y').text.strip()
        item_name = item_page.select_one('h1.css-1n8byw.e14n6e5u1').text.strip()
        origin_price = item_page.select_one('.css-14j45be.e1yx2lle2').text.strip()
        discount_price = item_page.select_one('.css-no59fe.e1ovj4ty1').text.strip()
        review_count = item_page.select_one('span.css-1ovjo5n').text.strip()
        item_score_avg = item_page.select_one('.css-1hld56p.e71452m2').text.strip()
        brand_keyword = [span.text for span in item_page.select("#__next > div.zds-themes.light-theme > div.css-xrh5h3.edi339y0 > div > div.shop_row > div > div > div > div > div:nth-child(2) > div.css-2jjng0.eq4fxvi7 span")]

        # 리뷰 페이지 들어가기 
        product_id = full_url.split("/")[-1]
        review_link = f"https://zigzag.kr/review/list/{product_id}"
        driver.get(review_link)
        time.sleep(2)

        # 스크롤 다운 (3번)
        for _ in range(5):
            driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')
            time.sleep(2) 

        # 리뷰 컨테이너 찾기 (리뷰 데이터 크롤링 시작)
        review_containers = driver.find_elements(By.CSS_SELECTOR, "div.css-vbvoj0.e13bai5o0")
        
        product_count = 0
        
        for review in review_containers:
            try:
                add_button = review.find_elements(By.CSS_SELECTOR, "span.zds4_s96ru86.zds4_s96ru813 p")
                for button in add_button:
                    try:
                        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(button))
                        action = ActionChains(driver)
                        action.move_to_element(button).click().perform()
                        time.sleep(1)
                    except Exception as e:
                        print(f"⚠ 버튼 클릭 오류: {e}")
                
                reviewer = review.find_element(By.CSS_SELECTOR, "p.zds4_s96ru86.zds4_s96ru815").text.strip()
                review_date = review.find_element(By.CSS_SELECTOR, "div.css-1xqlji6.eimmef70").text.strip()
                
                # 옵션 정보 가져오기
                option_elements = review.find_elements(By.CSS_SELECTOR, "div.css-6e8rvi.eld8gav1")
                options = [opt.text.strip() for opt in option_elements if opt.text.strip()]
                
                # 리뷰 
                review_texts  = review.find_elements(By.CSS_SELECTOR, "span.zds4_s96ru86.zds4_s96ru813")
                review_contents = [con.text.strip() for con in review_texts if con.text.strip()]
                
                # 정규표현식으로 값 추출
                size = next((opt.split()[-1] for opt in options if "사이즈" in opt), "")
                quality = next((opt.split()[-1] for opt in options if "퀄리티" in opt), "")
                color = next((opt.split()[-1] for opt in options if "색감" in opt), "")
                height = next((re.search(r"(\d+)cm", opt).group(1) + "cm" for opt in options if "cm" in opt), "")
                weight = next((re.search(r"(\d+)kg", opt).group(1) + "kg" for opt in options if "kg" in opt), "")
                top_size = next((opt.split()[-1] for opt in options if "상의" in opt), "")
                
                # 수집한 데이터를 리스트에 추가
                data.append({
                    '브랜드': brand_name,
                    '상품명': item_name,
                    '원가': origin_price,
                    '할인 가격': discount_price,
                    '리뷰 개수': review_count,
                    '평점': item_score_avg,
                    '키워드': ', '.join(brand_keyword),
                    '링크': full_url,
                    '리뷰어': reviewer,
                    '작성날짜': review_date,
                    '사이즈': size,
                    '퀄리티': quality,
                    '색감': color,
                    '키': height,
                    '몸무게': weight,
                    '상의사이즈': top_size,
                    '리뷰': review_contents
                })

                # 상품 크롤링 완료 메시지 출력
                product_count += 1
                print(f"✔ 상품 {product_count}: {item_name} 리뷰 데이터 크롤링 완료.")
            
            except Exception as e:
                print(f"⚠ 리뷰 크롤링 오류: {e}")
        
        # 데이터를 바로 CSV에 append 모드로 기록
        with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            if os.stat(csv_file).st_size == 0:  # 파일이 비어 있으면 헤더 작성
                writer.writeheader()
            writer.writerows(data)
        
        data.clear()  # 크롤링한 데이터 초기화

    except Exception as e:
        print(f"⚠ 상품 크롤링 오류 (URL: {full_url}): {e}")
        continue  # 오류 발생 시 다음 상품으로 넘어감

# 브라우저 종료
driver.quit()
print("크롤링이 완료되었습니다.")
