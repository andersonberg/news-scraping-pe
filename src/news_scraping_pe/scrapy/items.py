"""Itens Scrapy alinhados a docs/article_schema.json."""

import scrapy


class NewsArticleItem(scrapy.Item):
    article_id = scrapy.Field()
    url = scrapy.Field()
    portal_id = scrapy.Field()
    title = scrapy.Field()
    published_at = scrapy.Field()
    raw_text = scrapy.Field()
    view_count = scrapy.Field()
    view_count_raw = scrapy.Field()
    view_count_source = scrapy.Field()
    candidate_id = scrapy.Field()
    candidate_name = scrapy.Field()
    election_year = scrapy.Field()
    office = scrapy.Field()
    search_term_id = scrapy.Field()
    search_query = scrapy.Field()
    query_window_start = scrapy.Field()
    query_window_end = scrapy.Field()
    discovered_via = scrapy.Field()
    discovery_rank = scrapy.Field()
    language = scrapy.Field()
    extraction_method = scrapy.Field()
    http_status = scrapy.Field()
    collected_at = scrapy.Field()
    notes = scrapy.Field()
