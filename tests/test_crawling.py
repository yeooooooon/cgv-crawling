from src.cgv_crawling.crawling import (
    clean_text,
    normalize_url,
    parse_chart_item,
)


class FakeImage:
    def __init__(self, alt, src):
        self.attributes = {'alt': alt, 'src': src}

    def get_attribute(self, name):
        return self.attributes.get(name)


class FakeElement:
    text = '98% 누적관객수 12.3만 2026.09.16 개봉'

    def find_elements(self, by, selector):
        if selector == 'img':
            return [FakeImage('테스트 영화 포스터', '/poster.jpg')]
        if selector == "img[alt*='관람가']":
            return [FakeImage('12세관람가', '/rating.png')]
        return []

    def find_element(self, by, selector):
        if selector == "span[class*='bestChartList_name__']":
            return FakeTextElement('테스트 영화')
        raise LookupError(selector)

    def get_attribute(self, name):
        if name == 'outerHTML':
            return '<img alt="12세관람가">'
        return None


class FakeTextElement:
    def __init__(self, text):
        self.text = text


def test_clean_text_and_normalize_url():
    assert clean_text('  테스트\n 영화  ') == '테스트 영화'
    assert clean_text('   ') is None
    assert normalize_url('/poster.jpg') == 'https://cgv.co.kr/poster.jpg'


def test_parse_chart_item_extracts_movie_fields():
    record = parse_chart_item(
        FakeElement(),
        rank=1,
        crawled_at='2026-09-06 10:00:00',
        source_url='https://cgv.co.kr/chart',
    )

    assert record['rank'] == 1
    assert record['title'] == '테스트 영화'
    assert record['egg_index_raw'] == '98'
    assert record['cumulative_viewers_raw'] == '12.3만'
    assert record['release_info_raw'] == '2026.09.16 개봉'
    assert record['age_rating'] == '12세관람가'
    assert record['poster_url'] == 'https://cgv.co.kr/poster.jpg'