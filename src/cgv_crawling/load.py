"""
CGV 무비차트 최종 데이터를 MySQL에 저장
"""

from pathlib import Path
import os

from dotenv import load_dotenv
from pymysql.cursors import DictCursor
import pandas as pd
import pymysql


## 프로젝트 루트 (cgv_crawling 폴더)
PROJECT_DIR = Path(__file__).resolve().parents[1]

FINAL_CSV_PATH = PROJECT_DIR / 'data' / 'cgv_movie_clean.csv'

DB_COLUMNS = [
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

CREATE_TABLE_SQL = """
CREATE TABLE cgv_movies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    `rank` INT NULL,
    title VARCHAR(255) NOT NULL,
    egg_index VARCHAR(10) NULL,
    `cumulative_viewers_count` VARCHAR(20) NULL,
    is_re_release VARCHAR(20) NULL,
    release_date DATE NULL,
    age_rating VARCHAR(100) NULL,
    poster_url TEXT NULL,
    crawled_at DATETIME NULL,
    source_url TEXT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

INSERT_SQL = """
INSERT INTO cgv_movies
(`rank`, title, egg_index, `cumulative_viewers_count`,
 is_re_release, release_date, age_rating, poster_url, crawled_at, source_url)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def load_db_config() -> dict:
    """
    .env 파일에서 MySQL 접속 정보를 읽어 반환한다.

    Returns:
        host, port, user, password, database 키를 가진 접속 정보 딕셔너리
    """

    load_dotenv()

    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'movie_chart'),
    }


def load_clean_csv(clean_csv_path: Path = FINAL_CSV_PATH) -> pd.DataFrame:
    """
    data/cgv_movie_clean.csv를 읽어 반환한다.

    Args:
        clean_csv_path:
            읽을 최종 CSV 파일 경로

    Returns:
        최종 데이터프레임

    Raises:
        FileNotFoundError:
            최종 CSV 파일이 존재하지 않는 경우
    """

    if not clean_csv_path.is_file():
        raise FileNotFoundError(f'최종 CSV 파일이 없습니다. {clean_csv_path}')

    return pd.read_csv(clean_csv_path, encoding='utf-8-sig')


def ensure_database(config: dict) -> None:
    """
    설정된 데이터베이스가 없으면 생성한다.

    Args:
        config:
            MySQL 접속 정보
    """

    server_conn = pymysql.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        password=config['password'],
        charset='utf8mb4',
        autocommit=True,
    )

    try:
        with server_conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{config['database']}` "
                'CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci'
            )
    finally:
        server_conn.close()


def save_to_mysql(clean_df: pd.DataFrame, config: dict) -> int:
    """
    최종 데이터를 cgv_movies 테이블에 저장한다.

    기존 테이블을 삭제하고 다시 만든 뒤, 최종 데이터를 저장한다.

    Args:
        clean_df:
            저장할 최종 데이터프레임

        config:
            MySQL 접속 정보

    Returns:
        저장된 행 개수

    Raises:
        Exception:
            저장 과정에서 오류가 발생한 경우 롤백 후 다시 발생시킨다.
    """

    conn = pymysql.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        password=config['password'],
        database=config['database'],
        charset='utf8mb4',
        autocommit=False,
    )

    try:
        with conn.cursor() as cursor:
            cursor.execute('DROP TABLE IF EXISTS cgv_movies')
            cursor.execute(CREATE_TABLE_SQL)

            rows = []
            for _, row in clean_df[DB_COLUMNS].iterrows():
                values = [
                    None if pd.isna(row[col]) else row[col]
                    for col in DB_COLUMNS
                ]
                rows.append(tuple(values))

            cursor.executemany(INSERT_SQL, rows)

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    return len(rows)


def verify_saved_rows(config: dict, expected_count: int) -> pd.DataFrame:
    """
    MySQL에 저장된 행 수를 CSV 건수와 비교하고 상위 10건 미리보기를 반환한다.

    Args:
        config:
            MySQL 접속 정보

        expected_count:
            CSV 기준 예상 저장 건수

    Returns:
        MySQL에서 조회한 상위 10건 미리보기 데이터프레임

    Raises:
        ValueError:
            CSV 건수와 MySQL 저장 건수가 다른 경우
    """

    conn = pymysql.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        password=config['password'],
        database=config['database'],
        charset='utf8mb4',
        cursorclass=DictCursor,
    )

    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) AS cnt FROM cgv_movies')
            db_count = cursor.fetchone()['cnt']

            cursor.execute(
                "SELECT `rank`, title, egg_index, `cumulative_viewers_count`, "
                'age_rating, poster_url, crawled_at, source_url '
                'FROM cgv_movies ORDER BY `rank` LIMIT 10'
            )
            preview_df = pd.DataFrame(cursor.fetchall())

    finally:
        conn.close()

    if db_count != expected_count:
        raise ValueError(
            f'CSV 건수({expected_count})와 MySQL 저장 건수({db_count})가 다릅니다.'
        )

    return preview_df


def run_load(clean_df: pd.DataFrame | None = None) -> int:
    """
    최종 데이터를 MySQL cgv_movies 테이블에 저장한다.

    Args:
        clean_df:
            저장할 최종 데이터프레임

            값을 전달하지 않으면 data/cgv_movie_clean.csv를 읽는다.

    Returns:
        MySQL에 저장된 행 개수

    Raises:
        ValueError:
            CSV 건수와 MySQL 저장 건수가 다른 경우
    """

    if clean_df is None:
        clean_df = load_clean_csv()

    config = load_db_config()

    ensure_database(config)
    saved_count = save_to_mysql(clean_df, config)
    verify_saved_rows(config, saved_count)

    print('=' * 60)
    print('CGV 무비차트 MySQL 저장 완료')
    print('=' * 60)

    print(f'CSV 건수 : {len(clean_df)}')
    print(f'MySQL 저장 건수 : {saved_count}')
    print(f"저장 데이터베이스 : {config['database']}.cgv_movies")

    return saved_count


if __name__ == '__main__':
    try:
        run_load()

    except (FileNotFoundError, OSError, ValueError) as error:
        print('MySQL 저장 작업에 실패했습니다.')
        print(f'오류 내용 : {error}')

        raise SystemExit(1) from error
