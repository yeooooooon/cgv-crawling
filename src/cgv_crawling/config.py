"""CGV 수집 파이프라인의 공통 설정."""

from datetime import datetime
from pathlib import Path
import os


PROJECT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv('DATA_DIR', PROJECT_DIR / 'data'))
RAW_DIR = DATA_DIR / 'raw'
TODAY_STR = datetime.now().strftime('%Y%m%d')

TARGET_URL = 'https://cgv.co.kr/cnm/cgvChart/movieChart?tabParam=144'
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