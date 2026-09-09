"""AWS Lambda entry point for the CGV crawling pipeline."""

import json

from src.cgv_crawling.config import RAW_DIR, TODAY_STR
from src.cgv_crawling import (
    download_posters,
    run_crawling,
    run_load,
    run_preprocess,
)
from src.cgv_crawling.s3_storage import upload_dataframe, upload_directory


def lambda_handler(event, context):
    """Run the complete crawling, preprocessing, and MySQL load pipeline."""

    raw_df = run_crawling()
    poster_count = download_posters(raw_df)
    clean_df = run_preprocess(raw_df)

    raw_uri = upload_dataframe(
        raw_df,
        f'raw/cgv_movie_raw_{TODAY_STR}.csv',
    )
    interim_uri = upload_dataframe(
        clean_df,
        f'interim/cgv_movie_clean_{TODAY_STR}.csv',
    )
    processed_uri = upload_dataframe(
        clean_df,
        f'processed/cgv_movie_clean_{TODAY_STR}.csv',
    )
    poster_keys = upload_directory(
        RAW_DIR / 'posters' / TODAY_STR,
        f'raw/posters/{TODAY_STR}',
    )
    saved_count = run_load(clean_df)

    return {
        'statusCode': 200,
        'body': json.dumps(
            {
                'message': 'CGV movie pipeline completed',
                'raw_count': len(raw_df),
                'poster_count': poster_count,
                'saved_count': saved_count,
                'raw_uri': raw_uri,
                'interim_uri': interim_uri,
                'processed_uri': processed_uri,
                'poster_count_uploaded': len(poster_keys),
            },
            ensure_ascii=False,
        ),
    }