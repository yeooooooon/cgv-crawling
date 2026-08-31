"""
CGV 무비차트 원본(raw) 데이터를 정제
"""

from pathlib import Path
from urllib.parse import urljoin
import re

import pandas as pd


## 프로젝트 루트 (cgv_crawling 폴더)
PROJECT_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_DIR / 'data'
TODAY_STR = pd.Timestamp.today().strftime('%Y%m%d')
RAW_CSV_PATH = DATA_DIR / 'raw' / f'cgv_movie_raw_{TODAY_STR}.csv'
FINAL_CSV_PATH = DATA_DIR / f'cgv_movie_clean_{TODAY_STR}.csv'

FINAL_COLUMNS = [
    'rank',
    'title',
    'egg_index',
    'cumulative_viewers_count',
    'is_re_release',
    'release_date',
    'age_rating',
    'poster_url',
    'crawled_at',
    'source_url',
]

AGE_RATING_MAP = {
    '전체관람가': '전체 관람가',
    '12세관람가': '12세 관람가',
    '15세관람가': '15세 관람가',
    '18세관람가': '18세 관람가',
    '19세관람가': '19세 관람가',
    '청소년관람불가': '청소년 관람불가',
    '청불': '청소년 관람불가',
}


def load_raw_csv(raw_csv_path: Path = RAW_CSV_PATH) -> pd.DataFrame:
    """
    data/raw/cgv_movie_raw.csv를 읽어 반환한다.

    Args:
        raw_csv_path:
            읽을 원본 CSV 파일 경로

    Returns:
        원본 데이터프레임

    Raises:
        FileNotFoundError:
            원본 CSV 파일이 존재하지 않는 경우
    """

    if not raw_csv_path.is_file():
        raise FileNotFoundError(f'원본 CSV 파일이 없습니다. {raw_csv_path}')

    return pd.read_csv(raw_csv_path, encoding='utf-8-sig')


def parse_release_info(text) -> tuple[str, object]:
    """
    개봉 관련 원본 텍스트를 재개봉 여부와 날짜로 분리한다.

    '2026.08.26 재개봉' -> ('재개봉', '2026-08-26')
    '2026.08.19 개봉'   -> ('개봉예정', '2026-08-19')
    NaN (이미 개봉됨)   -> ('개봉', pd.NA)
    """

    if pd.isna(text) or not str(text).strip():
        return '개봉', pd.NA

    val = str(text)

    if '재개봉' in val:
        release_type = '재개봉'
    elif '개봉' in val:
        release_type = '개봉예정'
    else:
        release_type = '개봉'

    date_match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})', val)

    if date_match:
        formatted_date = f'{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}'
    else:
        formatted_date = pd.NA

    return release_type, formatted_date


def clean_age_rating(value):
    """
    HTML이 섞여 있어도 관람등급 텍스트만 남긴다.
    """

    if pd.isna(value):
        return pd.NA

    text = str(value)

    alt_match = re.search(
        r'alt=["\']([^"\']*(?:관람가|관람불가|청불)[^"\']*)["\']',
        text,
        flags=re.I,
    )
    if alt_match:
        text = alt_match.group(1)

    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', '', text).strip()

    for key, value_str in AGE_RATING_MAP.items():
        if key in text:
            return value_str

    return text if text else pd.NA


def normalize_url(url):
    """
    상대 경로 URL을 CGV 절대 URL로 변환한다.
    """

    if pd.isna(url) or not url:
        return pd.NA

    return urljoin('https://cgv.co.kr', str(url))


def preprocess_movie_data(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    CGV 무비차트 원본 데이터를 정제하여 최종 데이터프레임을 만든다.

    전처리 항목:
        1. 영화명 공백 제거, 영화명이 없는 데이터 제거
        2. 순위 숫자형 변환
        3. 에그지수, 누적관객수 형식 정리
        4. 관람등급 텍스트 정리
        5. 포스터 URL 절대 경로 변환
        6. 개봉/재개봉 여부와 날짜 분리
        7. 영화명 기준 중복 제거
        8. 최종 컬럼 순서 정리

    Args:
        raw_df:
            crawling 단계에서 만든 원본 데이터프레임

    Returns:
        정제가 끝난 최종 데이터프레임
    """

    df = raw_df.copy()

    df['title'] = df['title'].astype('string').str.strip()
    df = df[df['title'].notna() & (df['title'] != '')]

    df['rank'] = pd.to_numeric(df['rank'], errors='coerce').astype('Int64')

    df['egg_index'] = df['egg_index_raw'].apply(
        lambda x: f'{str(x).strip()}%' if pd.notna(x) and str(x).strip() not in ['', '-'] else None
    )

    df['cumulative_viewers_count'] = df['cumulative_viewers_raw'].apply(
        lambda x: str(x).strip() if pd.notna(x) and str(x).strip() not in ['', '-'] else None
    )

    df['age_rating'] = df['age_rating'].apply(clean_age_rating)
    df['poster_url'] = df['poster_url'].apply(normalize_url)

    df[['is_re_release', 'release_date']] = df['release_info_raw'].apply(
        lambda x: pd.Series(parse_release_info(x))
    )

    df = df.drop_duplicates(subset=['title'], keep='first')

    for col in FINAL_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    return (
        df[FINAL_COLUMNS]
        .sort_values('rank', na_position='last')
        .reset_index(drop=True)
    )


def save_clean_csv(clean_df: pd.DataFrame) -> Path:
    """
    정제가 끝난 데이터프레임을 data/cgv_movie_clean.csv에 저장한다.

    Args:
        clean_df:
            정제가 끝난 최종 데이터프레임

    Returns:
        저장된 CSV 파일 경로
    """

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(FINAL_CSV_PATH, index=False, encoding='utf-8-sig')

    return FINAL_CSV_PATH


def verify_saved_csv(clean_csv_path: Path, original_df: pd.DataFrame) -> pd.DataFrame:
    """
    저장한 CSV 파일을 다시 읽고 저장 전후의 행 수를 검증한다.

    Args:
        clean_csv_path:
            저장한 CSV 파일 경로

        original_df:
            CSV 저장 전 원본 데이터프레임

    Returns:
        다시 읽은 CSV 데이터프레임

    Raises:
        ValueError:
            CSV 저장 전후의 행 수가 다른 경우
    """

    saved_df = pd.read_csv(clean_csv_path, encoding='utf-8-sig')

    if len(saved_df) != len(original_df):
        raise ValueError('CSV 저장 전후의 행 수가 다릅니다.')

    return saved_df


def run_preprocess(raw_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    원본 데이터를 정제하고 최종 CSV로 저장한다.

    Args:
        raw_df:
            정제할 원본 데이터프레임

            값을 전달하지 않으면 data/raw/cgv_movie_raw.csv를 읽는다.

    Returns:
        정제가 끝난 최종 데이터프레임

    Raises:
        ValueError:
            CSV 저장 전후의 행 수가 다른 경우
    """

    if raw_df is None:
        raw_df = load_raw_csv()

    clean_df = preprocess_movie_data(raw_df)

    clean_csv_path = save_clean_csv(clean_df)
    verify_saved_csv(clean_csv_path, clean_df)

    print('=' * 60)
    print('CGV 무비차트 데이터 전처리 완료')
    print('=' * 60)

    print(f'원본 건수 : {len(raw_df)}')
    print(f'정제 후 건수 : {len(clean_df)}')
    print(f'최종 CSV 저장 경로 : {clean_csv_path}')

    return clean_df


if __name__ == '__main__':
    try:
        run_preprocess()

    except (FileNotFoundError, OSError, ValueError) as error:
        print('데이터 전처리 작업에 실패했습니다.')
        print(f'오류 내용 : {error}')

        raise SystemExit(1) from error
