import logging

from app.logging_config import LOG_FILENAME, configure_logging, get_logger


def test_configure_logging_creates_console_and_rotating_file_handler(tmp_path):
    logger = configure_logging(str(tmp_path), level=logging.DEBUG)

    assert logger.name == "youtube_audio_extractor"
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) == 2
    assert any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers)
    assert any(handler.__class__.__name__ == "RotatingFileHandler" for handler in logger.handlers)

    logger.info("mensagem de teste")
    for handler in logger.handlers:
        handler.flush()

    log_path = tmp_path / LOG_FILENAME
    assert log_path.exists()
    assert "mensagem de teste" in log_path.read_text(encoding="utf-8")


def test_get_logger_returns_named_child_logger():
    logger = get_logger("service")
    assert logger.name == "youtube_audio_extractor.service"
