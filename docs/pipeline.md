# CGV 수집 파이프라인

현재 파이프라인은 로컬에서 다음 순서로 실행됩니다.

```text
run_crawling
    -> raw CSV 저장
    -> poster 다운로드
    -> 전처리 및 clean CSV 저장
    -> MySQL 저장 및 행 수 검증
```

## 모듈 책임

- `config.py`: 공통 URL, 경로, 타임아웃, 컬럼 설정
- `crawling.py`: Selenium 기반 영화 차트 수집
- `poster.py`: 포스터 URL 다운로드 및 날짜별 파일 저장
- `preprocess.py`: 원본 데이터 정제 및 CSV 저장
- `load.py`: MySQL 테이블 생성, 저장, 건수 검증

AWS 도입 시 각 단계의 진입점은 `handlers/`의 Lambda 함수로 분리할 수 있습니다.