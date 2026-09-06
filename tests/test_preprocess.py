import pandas as pd

from src.cgv_crawling.preprocess import preprocess_movie_data


def test_preprocess_movie_data_normalizes_movie_fields():
    raw_df = pd.DataFrame([
        {
            'rank': '1',
            'title': '  테스트 영화  ',
            'egg_index_raw': '98',
            'cumulative_viewers_raw': '12.3만',
            'release_info_raw': '2026.09.16 개봉',
            'age_rating': '12세관람가',
            'poster_url': '/poster.jpg',
            'crawled_at': '2026-09-06 10:00:00',
            'source_url': 'https://cgv.co.kr/chart',
        },
    ])

    clean_df = preprocess_movie_data(raw_df)

    assert clean_df.loc[0, 'title'] == '테스트 영화'
    assert clean_df.loc[0, 'egg_index'] == '98%'
    assert clean_df.loc[0, 'is_re_release'] == '개봉예정'
    assert clean_df.loc[0, 'release_date'] == '2026-09-16'
    assert clean_df.loc[0, 'age_rating'] == '12세 관람가'
    assert clean_df.loc[0, 'poster_url'] == 'https://cgv.co.kr/poster.jpg'