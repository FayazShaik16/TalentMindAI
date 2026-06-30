from app.core.logging.logging import logger

def test_logger_emits():
    """
    Ensures that structlog configuration permits structured info logs.
    """
    logger.info("testing_logger_emits_success", test_parameter="log_verify")
