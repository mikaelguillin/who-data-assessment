from pathlib import Path

from pipeline.db import normalize_database_url, resolve_database_url, resolve_var_dir


def test_normalize_postgres_urls() -> None:
    assert normalize_database_url("postgres://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert normalize_database_url("postgresql://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert normalize_database_url("postgresql+psycopg://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert normalize_database_url("sqlite:////tmp/x.db") == "sqlite:////tmp/x.db"


def test_resolve_database_url_prefers_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@h/db")
    assert resolve_database_url(tmp_path) == "postgresql+psycopg://u:p@h/db"


def test_resolve_database_url_sqlite_fallback(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    assert resolve_database_url(tmp_path) == f"sqlite:///{tmp_path / 'harmonized.db'}"


def test_resolve_var_dir_uses_tmp_on_vercel(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("VAR_DIR", raising=False)
    monkeypatch.setattr("pipeline.db.tempfile.gettempdir", lambda: str(tmp_path))
    resolved = resolve_var_dir()
    assert resolved == tmp_path / "who-data-assessment"
    assert resolved.is_dir()


def test_resolve_var_dir_honors_override(monkeypatch, tmp_path: Path) -> None:
    override = tmp_path / "custom-var"
    monkeypatch.setenv("VAR_DIR", str(override))
    resolved = resolve_var_dir()
    assert resolved == override
    assert resolved.is_dir()
