"""Repository data-contract smoke tests.

These tests validate artifact presence and readability without training models or
calling external services.
"""
from pathlib import Path
import csv
import json

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ["data/Sales Data For Data Analyst Role (1).csv"]

def test_declared_data_artifacts_exist():
    missing = [name for name in ARTIFACTS if not (ROOT / name).exists()]
    assert not missing, f"Missing declared data artifacts: {missing}"

def test_csv_artifacts_have_a_header():
    for name in ARTIFACTS:
        path = ROOT / name
        if path.suffix.lower() == '.csv':
            with path.open(newline='', encoding='utf-8-sig', errors='replace') as handle:
                header = next(csv.reader(handle), [])
            assert header and any(cell.strip() for cell in header), f"CSV has no header: {name}"

def test_json_artifacts_are_parseable():
    for name in ARTIFACTS:
        path = ROOT / name
        if path.suffix.lower() == '.json':
            json.loads(path.read_text(encoding='utf-8'))
