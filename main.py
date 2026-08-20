"""
CGV 무비차트 데이터 수집 파이프라인을 순서대로 실행
"""

from src.cgv_crawling import run_crawling, run_load, run_preprocess


def main() -> None:
    """
    CGV 무비차트 파이프라인 전체를 실행한다.
    """

    raw_df = run_crawling()
    clean_df = run_preprocess(raw_df)
    saved_count = run_load(clean_df)

    print()
    print('#' * 60)
    print('CGV 무비차트 파이프라인 전체 실행 완료')
    print('#' * 60)
    print(f'MySQL 저장 건수 : {saved_count}')


if __name__ == '__main__':
    main()
