import pandas as pd

from src.cgv_crawling import poster


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return b'poster-bytes'


def test_download_posters_saves_images_without_network(monkeypatch, tmp_path):
    monkeypatch.setattr(poster, 'RAW_DIR', tmp_path)
    monkeypatch.setattr(poster, 'urlopen', lambda request, timeout: FakeResponse())

    raw_df = pd.DataFrame([
        {'rank': 1, 'title': '테스트 영화', 'poster_url': 'https://example.com/poster.jpg'},
    ])

    downloaded_count = poster.download_posters(raw_df, '20260906')

    output_path = tmp_path / 'posters' / '20260906' / '01.jpg'
    assert downloaded_count == 1
    assert output_path.read_bytes() == b'poster-bytes'