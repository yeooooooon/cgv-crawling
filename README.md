# CGV Movie Chart Crawling
> CGV 무비차트 페이지에서 영화 정보를 수집하고, 정제한 뒤 CSV와 MySQL에 저장하는 데이터 파이프라인 프로젝트입니다.

## 1. 프로젝트 개요
CGV 무비차트 웹페이지를 Selenium으로 크롤링하여 영화 순위, 영화명, 에그지수, 누적 관객 수, 관람등급, 개봉 정보를 수집했습니다.
수집한 원본 데이터는 pandas를 이용해 분석과 저장에 적합한 형태로 정제하고, 최종 결과를 CSV 파일과 MySQL 데이터베이스에 저장하도록 구성했습니다.

## 2. 프로젝트 목적
- CGV 무비차트 데이터 자동 수집
- 웹페이지에서 제공되는 영화 정보 구조화
- 원본 데이터의 결측치와 형식 정리
- CSV와 관계형 데이터베이스 저장 과정 자동화
- 수집 데이터의 저장 전후 건수 검증

## 3. 기능 요약
- **데이터 수집**: Selenium으로 CGV 무비차트 동적 페이지 수집
- **정보 추출**: 순위, 영화명, 에그지수, 누적 관객 수, 개봉 정보, 관람등급, 포스터 URL 추출
- **포스터 저장**: 포스터 이미지를 날짜별 `data/raw/posters/YYYYMMDD/` 폴더에 저장
- **전처리**: 날짜, 관람등급, URL, 숫자 및 결측값 형식 정리
- **중복 제거**: 영화명을 기준으로 중복 데이터 제거
- **파일 저장**: 원본 및 정제 데이터를 CSV로 저장
- **DB 저장**: 정제 데이터를 MySQL `movie_chart` 데이터베이스의 `cgv_movies` 테이블에 저장
- **검증**: CSV와 MySQL의 저장 행 수 비교

## 4. 기술 스택
- **Language**: Python
- **Web Crawling**: Selenium
- **Data Processing**: pandas
- **Database**: MySQL, PyMySQL
- **Configuration**: python-dotenv
- **Notebook**: Jupyter Notebook
- **Version Control**: Git, GitHub

## 5. 파이프라인 작업 흐름
1. CGV 무비차트 페이지에 접속
2. 동적으로 렌더링되는 차트 항목이 나타날 때까지 대기
3. 영화별 원본 데이터를 추출해 `data/raw/cgv_movie_raw.csv`로 저장
4. 포스터 이미지를 `data/raw/posters/YYYYMMDD/`에 저장
5. 영화명, 순위, 에그지수, 누적 관객 수, 관람등급과 URL을 정제
6. 개봉 및 재개봉 여부와 개봉일을 분리
7. 영화명 기준 중복을 제거하고 `data/cgv_movie_clean.csv`로 저장
8. 정제 데이터를 MySQL `movie_chart` 데이터베이스의 `cgv_movies` 테이블에 저장
9. CSV와 MySQL의 저장 건수를 비교해 결과 검증

## 6. 주요 데이터 컬럼
- `rank`: 무비차트 순위
- `title`: 영화명
- `egg_index`: CGV 에그지수
- `cumulative_viewers_count`: 누적 관객 수
- `is_re_release`: 개봉, 개봉예정 또는 재개봉 여부
- `release_date`: 개봉 또는 재개봉 날짜
- `age_rating`: 관람등급
- `poster_url`: 영화 포스터 URL
- `crawled_at`: 데이터 수집 시각
- `source_url`: 원본 CGV 페이지 URL

## 7. 프로젝트 구조
```text
cgv_crawling/
├── cgv_crawling.ipynb             # 수집 및 전처리 과정 확인용 노트북
├── main.py                        # 전체 파이프라인 실행 파일
├── data/
│   ├── cgv_movie_clean.csv        # 정제된 영화 데이터
│   └── raw/
│       ├── cgv_movie_raw.csv      # 크롤링 원본 데이터
│       └── posters/YYYYMMDD/      # 날짜별 포스터 이미지
├── src/
│   ├── cgv_crawling/
│   │   ├── crawling.py            # CGV 무비차트 수집
│   │   ├── load.py                # MySQL 저장 및 검증
│   │   └── preprocess.py          # 데이터 전처리
│   └── data/                      # 패키지 내부 데이터 사본
└── .gitignore                     # 환경 변수 및 로컬 파일 제외
```

## 8. 기대 효과
- 반복적인 무비차트 데이터 수집 자동화
- 크롤링 원본과 정제 데이터의 단계별 관리
- CSV와 MySQL을 활용한 데이터 분석 및 서비스 확장
- 영화 순위, 관객 수, 에그지수 기반의 추가 분석으로 확장 가능

## 09. 데이터 출처
본 프로젝트는 CGV 무비차트 페이지의 공개 정보를 대상으로 합니다.

- [CGV 무비차트](https://cgv.co.kr/cnm/cgvChart/movieChart?tabParam=144)
