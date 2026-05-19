"""Configurações Scrapy do projeto."""

from __future__ import annotations

import os

BOT_NAME = "news_scraping_pe"

SPIDER_MODULES = ["news_scraping_pe.scrapy.spiders"]
NEWSPIDER_MODULE = "news_scraping_pe.scrapy.spiders"

ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 4
DOWNLOAD_DELAY = 1.0
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 10.0

DEFAULT_REQUEST_HEADERS = {
    "Accept-Language": "pt-BR,pt;q=0.9",
}

ITEM_PIPELINES: dict[str, int] = {}

ARTICLES_OUTPUT_PATH = os.getenv("ARTICLES_OUTPUT_PATH", "data/articles.jsonl")
