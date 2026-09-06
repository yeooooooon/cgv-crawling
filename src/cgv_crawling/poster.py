"""영화 포스터 다운로드 기능."""

from urllib.request import Request, urlopen

import pandas as pd

from .config import PAGE_LOAD_TIMEOUT, RAW_DIR, TODAY_STR, USER_AGENT


def download_posters(
    raw_df: pd.DataFrame,
    poster_date: str | None = None,
) -> int:
    """수집한 포스터 URL을 날짜별 raw/posters 폴더에 저장한다."""

    poster_dir = RAW_DIR / 'posters' / (poster_date or TODAY_STR)
    poster_dir.mkdir(parents=True, exist_ok=True)
    downloaded_count = 0

    for _, row in raw_df.iterrows():
        poster_url = row.get('poster_url')
        if pd.isna(poster_url) or not str(poster_url).strip():
            continue

        output_path = poster_dir / f"{int(row['rank']):02d}.jpg"

        try:
            request = Request(
                str(poster_url),
                headers={'User-Agent': USER_AGENT},
            )
            with urlopen(request, timeout=PAGE_LOAD_TIMEOUT) as response:
                output_path.write_bytes(response.read())

            downloaded_count += 1
            print(f'포스터 저장 완료: {output_path.name}')

        except Exception as error:
            print(f"포스터 다운로드 실패 ({row.get('title', '-')}) : {error}")

    print(f'포스터 저장 건수 : {downloaded_count}건')
    print(f'포스터 저장 경로 : {poster_dir}')

    return downloaded_count