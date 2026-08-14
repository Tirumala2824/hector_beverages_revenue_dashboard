from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_repository_has_readme_and_license():
    assert (ROOT / "README.md").exists()
    assert any((ROOT / name).exists() for name in ("LICENSE", "LICENSE.md", "COPYING"))

def test_repository_does_not_track_local_environment_files():
    tracked = []
    git_dir = ROOT / ".git"
    if git_dir.exists():
        import subprocess
        tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    assert not any(Path(name).name == ".env" for name in tracked)
