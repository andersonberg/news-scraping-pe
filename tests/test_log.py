import logging

import pytest

from news_scraping_pe import log as log_module
from news_scraping_pe.log import configure_logging, get_logger


@pytest.fixture(autouse=True)
def reset_package_logger() -> None:
    """Remove handlers entre testes para isolar configure_logging."""
    logger = logging.getLogger(log_module.PACKAGE_LOGGER)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
    logger.setLevel(logging.NOTSET)
    yield
    for handler in list(logger.handlers):
        logger.removeHandler(handler)


def test_get_logger_prefixes_package_name() -> None:
    logger = get_logger("cli")
    assert logger.name == "news_scraping_pe.cli"


def test_get_logger_keeps_full_name() -> None:
    logger = get_logger("news_scraping_pe.config.loader")
    assert logger.name == "news_scraping_pe.config.loader"


def test_configure_logging_is_idempotent() -> None:
    configure_logging(level=logging.INFO)
    logger = logging.getLogger(log_module.PACKAGE_LOGGER)
    handler_count = len(logger.handlers)

    configure_logging(level=logging.DEBUG)

    assert len(logger.handlers) == handler_count
    assert logger.level == logging.DEBUG


def test_configure_logging_writes_to_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(level=logging.INFO)
    get_logger("tests").info("mensagem de teste")

    captured = capsys.readouterr()
    assert "mensagem de teste" in captured.err
    assert "news_scraping_pe.tests" in captured.err
