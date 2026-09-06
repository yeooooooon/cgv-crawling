import pandas as pd

from src.cgv_crawling import load


class FakeCursor:
    def __init__(self):
        self.executed_sql = []
        self.inserted_rows = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, sql):
        self.executed_sql.append(sql)

    def executemany(self, sql, rows):
        self.executed_sql.append(sql)
        self.inserted_rows.extend(rows)


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def test_save_to_mysql_inserts_rows_and_commits(monkeypatch):
    fake_connection = FakeConnection()
    monkeypatch.setattr(load.pymysql, 'connect', lambda **kwargs: fake_connection)

    clean_df = pd.DataFrame([
        {
            'rank': 1,
            'title': '테스트 영화',
            'egg_index': '98%',
            'cumulative_viewers_count': None,
            'is_re_release': '개봉',
            'release_date': pd.NaT,
            'age_rating': '12세 관람가',
            'poster_url': 'https://example.com/poster.jpg',
            'crawled_at': '2026-09-06 10:00:00',
            'source_url': 'https://cgv.co.kr/chart',
        },
    ])

    saved_count = load.save_to_mysql(clean_df, {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '',
        'database': 'movie_chart',
    })

    assert saved_count == 1
    assert fake_connection.committed is True
    assert fake_connection.rolled_back is False
    assert fake_connection.closed is True
    assert fake_connection.cursor_instance.inserted_rows[0][0:3] == (
        1,
        '테스트 영화',
        '98%',
    )
    assert fake_connection.cursor_instance.inserted_rows[0][3] is None
    assert fake_connection.cursor_instance.inserted_rows[0][5] is None