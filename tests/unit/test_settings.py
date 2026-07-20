import pytest

from app.settings import Settings


def test_settings_ignores_docker_compose_env_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POSTGRES_DB", "gite_agent")
    monkeypatch.setenv("POSTGRES_USER", "gite_agent")
    monkeypatch.setenv("POSTGRES_PASSWORD", "gite_agent")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("STREAMLIT_PORT", "8501")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/db")

    settings = Settings(_env_file=None)

    assert settings.database_url == "postgresql+psycopg://user:pass@localhost:5432/db"
