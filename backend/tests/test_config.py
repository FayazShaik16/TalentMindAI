from app.core.config.config import settings

def test_settings_load():
    """
    Validates that Pydantic settings load with correct defaults and constraints.
    """
    assert settings.APP_ENV in ["development", "production", "testing"]
    assert settings.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR"]
    assert settings.get_database_url is not None
    assert isinstance(settings.FLAG_SEMANTIC_SEARCH, bool)
