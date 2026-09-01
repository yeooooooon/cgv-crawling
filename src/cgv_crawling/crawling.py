"""
CGV 무비차트 페이지를 Selenium으로 수집
"""

from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
import re
import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException


## ===========================================================
## 1. 수집 설정
## ===========================================================

TARGET_URL = 'https://cgv.co.kr/cnm/cgvChart/movieChart?tabParam=144'

## 무비차트 항목을 찾기 위한 CSS 선택자 (앞에서부터 순서대로 시도)
CHART_ITEM_SELECTORS = [
    "li[class*='bestChartList_chartItem__']",
    "li[class*='chartItem']",
]

## 영화명을 찾기 위한 CSS 선택자 (앞에서부터 순서대로 시도)
TITLE_SELECTORS = [
    "span[class*='bestChartList_name__']",
    "[class*='chartName']",
]

PAGE_LOAD_TIMEOUT = 30
WAIT_TIMEOUT = 20

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
)

RAW_COLUMNS = [
    'rank',
    'title',
    'egg_index_raw',
    'cumulative_viewers_raw',
    'release_info_raw',
    'age_rating',
    'poster_url',
    'crawled_at',
    'source_url',
]


## ===========================================================
## 2. 기본 저장 경로 설정
## ===========================================================

## 프로젝트 루트 (cgv_crawling 폴더)
PROJECT_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_DIR / 'data'
RAW_DIR = DATA_DIR / 'raw'
TODAY_STR = datetime.now().strftime('%Y%m%d')
RAW_CSV_PATH = RAW_DIR / f'cgv_movie_raw_{TODAY_STR}.csv'

print(f'프로젝트 기준 경로 : {PROJECT_DIR}')
print(f'Raw CSV 저장 경로 : {RAW_CSV_PATH}')


def build_driver(headless: bool = True) -> webdriver.Chrome:
    """
    CGV 무비차트 수집용 크롬 웹드라이버를 생성한다.

    Args:
        headless:
            브라우저 창을 표시하지 않고 실행할지 여부

    Returns:
        옵션이 설정된 크롬 웹드라이버 객체
    """

    options = Options()

    if headless:
        options.add_argument('--headless=new')

    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1440,1200')
    options.add_argument(f'user-agent={USER_AGENT}')

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)

    return driver


def clean_text(text) -> str | None:
    """
    공백을 정리하고 빈 문자열이면 None을 반환한다.
    """

    if text is None:
        return None

    text = re.sub(r'\s+', ' ', str(text)).strip()

    return text if text else None


def first_text(element, selectors: list[str]) -> str | None:
    """
    선택자 목록을 순서대로 시도하여 처음 찾은 텍스트를 반환한다.
    """

    for selector in selectors:
        try:
            value = clean_text(element.find_element(By.CSS_SELECTOR, selector).text)
            if value:
                return value
        except Exception:
            pass

    return None


def normalize_url(url) -> str | None:
    """
    상대 경로 URL을 CGV 절대 URL로 변환한다.
    """

    if not url:
        return None

    return urljoin('https://cgv.co.kr', url)


def wait_for_chart_items(driver: webdriver.Chrome) -> None:
    """
    무비차트 목록 요소가 렌더링될 때까지 대기한다.

    렌더링이 예상보다 늦어져 타임아웃이 발생해도
    수집을 중단하지 않고 추가로 3초를 더 대기한다.
    """

    try:
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            lambda d: len(d.find_elements(
                By.CSS_SELECTOR,
                CHART_ITEM_SELECTORS[0],
            )) > 0
        )
    except TimeoutException:
        time.sleep(3)

    ## 렌더링 안정화 대기
    time.sleep(2)


def find_chart_items(driver: webdriver.Chrome) -> list:
    """
    무비차트 목록 항목 요소를 CSS 선택자로 찾는다.
    """

    for selector in CHART_ITEM_SELECTORS:
        items = driver.find_elements(By.CSS_SELECTOR, selector)
        if items:
            return items

    return []


def extract_age_rating(item) -> str | None:
    """
    차트 카드의 관람등급 이미지 alt만 추출한다.
    """

    try:
        for img in item.find_elements(By.CSS_SELECTOR, "img[alt*='관람가']"):
            alt = clean_text(img.get_attribute('alt'))
            if alt:
                return alt

        html = item.get_attribute('outerHTML') or ''
        match = re.search(
            r'alt=["\']([^"\']*(?:관람가|관람불가|청불)[^"\']*)["\']',
            html,
            flags=re.I,
        )
        if match:
            return clean_text(match.group(1))

    except Exception as error:
        print('관람등급 추출 오류:', error)

    return None


def extract_release_info(item) -> str | None:
    """
    '재개봉' 또는 '개봉' 텍스트를 추출한다.
    """

    try:
        text = item.text
        match = re.search(r'(\d{4}\.\d{2}\.\d{2}\s*(?:개봉|재개봉))', text)
        if match:
            return clean_text(match.group(1))
    except Exception:
        pass

    return None


def parse_chart_item(item, rank: int, crawled_at: str, source_url: str) -> dict:
    """
    무비차트 항목 한 건에서 원본 필드를 추출한다.

    Args:
        item:
            무비차트 항목 웹 엘리먼트

        rank:
            차트 순위

        crawled_at:
            수집 시각 문자열

        source_url:
            원본 페이지 URL

    Returns:
        항목 한 건의 원본 필드 딕셔너리

    Raises:
        ValueError:
            영화명을 찾지 못한 경우
    """

    title = None
    poster_url = None

    ## 영화명과 포스터
    for img in item.find_elements(By.TAG_NAME, 'img'):
        alt = clean_text(img.get_attribute('alt'))
        src = normalize_url(img.get_attribute('src'))

        if src and not poster_url:
            poster_url = src

        if alt and '포스터' in alt:
            title = alt.replace('포스터', '').strip()

    title_span = first_text(item, TITLE_SELECTORS)
    if title_span:
        title = title_span

    if not title:
        raise ValueError('영화명을 찾을 수 없음')

    info_text = clean_text(item.text) or ''

    ## 에그지수
    egg_match = re.search(r'(\d+(?:\.\d+)?)\s*%', info_text)
    egg_index = egg_match.group(1) if egg_match else None

    ## 누적관객수
    viewer_match = re.search(r'누적관객수\s*([\d,.]+\s*(?:만|천)?)', info_text)
    cumulative_viewers = viewer_match.group(1) if viewer_match else None

    return {
        'rank': rank,
        'title': title,
        'egg_index_raw': egg_index,
        'cumulative_viewers_raw': cumulative_viewers,
        'release_info_raw': extract_release_info(item),
        'age_rating': extract_age_rating(item),
        'poster_url': poster_url,
        'crawled_at': crawled_at,
        'source_url': source_url,
    }


def collect_chart_list(driver: webdriver.Chrome, url: str = TARGET_URL) -> pd.DataFrame:
    """
    CGV 무비차트에서 최종 산출물에 필요한 항목을 수집한다.

    Args:
        driver:
            페이지 접속에 사용할 웹드라이버

        url:
            접속할 CGV 무비차트 URL

    Returns:
        무비차트 원본 데이터프레임
    """

    driver.get(url)
    wait_for_chart_items(driver)

    items = find_chart_items(driver)
    print(f'차트 항목 수: {len(items)}')

    crawled_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    records: list[dict] = []

    for rank, item in enumerate(items, start=1):
        try:
            record = parse_chart_item(item, rank, crawled_at, url)
            records.append(record)

            print(
                f"{rank}위 | {record['title']} | "
                f"에그={record['egg_index_raw'] or '-'} | "
                f"누적관객={record['cumulative_viewers_raw'] or '-'} | "
                f"등급={record['age_rating'] or '-'}"
            )

        except Exception as error:
            print(f'{rank}위 수집 실패: {error}')

    return pd.DataFrame(records, columns=RAW_COLUMNS)


def save_raw_csv(raw_df: pd.DataFrame) -> Path:
    """
    수집한 원본 데이터를 data/raw/cgv_movie_raw.csv에 저장한다.

    Args:
        raw_df:
            수집한 무비차트 원본 데이터프레임

    Returns:
        저장된 CSV 파일 경로
    """

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_df.to_csv(RAW_CSV_PATH, index=False, encoding='utf-8-sig')

    return RAW_CSV_PATH


def run_crawling(url: str = TARGET_URL, headless: bool = True) -> pd.DataFrame:
    """
    CGV 무비차트를 Selenium으로 수집하고 raw CSV로 저장한다.

    Args:
        url:
            수집할 CGV 무비차트 URL

        headless:
            브라우저 창을 표시하지 않고 실행할지 여부

    Returns:
        수집한 무비차트 원본 데이터프레임

    Raises:
        OSError:
            CSV 파일 저장에 실패한 경우
    """

    driver = build_driver(headless=headless)

    try:
        print('=' * 60)
        print('CGV 무비차트 접속 및 수집 시작')
        print(f'접속 URL : {url}')

        raw_df = collect_chart_list(driver, url)

    finally:
        driver.quit()
        print('웹브라우저 종료')

    raw_csv_path = save_raw_csv(raw_df)

    print()
    print('=' * 60)
    print('CGV 무비차트 원본 데이터 수집을 완료했습니다.')
    print('=' * 60)

    print(f'수집 건수 : {len(raw_df)}건')
    print(f'raw CSV 저장 경로 : {raw_csv_path}')

    return raw_df


if __name__ == '__main__':
    try:
        run_crawling()

    except OSError as error:
        print()
        print('원본 데이터 저장에 실패했습니다.')
        print(f'오류 내용 : {error}')
