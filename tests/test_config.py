from pathlib import Path

from app.config import Settings


def test_settings_resolve_paths_from_repository_root():
    settings = Settings.from_environment(Path(__file__).parents[1])
    assert settings.data_path.name.endswith(".csv")
    assert settings.template_dir.name == "templates"
    assert settings.static_dir.name == "static"
