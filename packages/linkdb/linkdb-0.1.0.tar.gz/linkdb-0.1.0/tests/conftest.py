"""Pytest fixtures for awesome-manager tests."""

import json
import tempfile
from pathlib import Path

import pytest

from linkdb import init_db


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    conn = init_db(db_path)
    yield db_path, conn

    conn.close()
    db_path.unlink(missing_ok=True)


@pytest.fixture
def temp_json():
    """Create a temporary JSON file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json_path = Path(f.name)

    yield json_path

    json_path.unlink(missing_ok=True)


@pytest.fixture
def sample_entries():
    """Sample valid entries for testing."""
    return [
        {
            "name": "test-project-1",
            "category": "dsp",
            "desc": "A test DSP project",
            "url": "https://example.com/test1",
            "repo": "https://github.com/test/test1",
        },
        {
            "name": "test-project-2",
            "category": "analysis",
            "desc": "A test analysis project",
            "url": None,
            "repo": "https://github.com/test/test2",
        },
        {
            "name": "test-project-3",
            "category": "sequencer",
            "desc": "A test MIDI sequencer",
            "url": "https://example.com/test3",
            "repo": None,
        },
    ]


@pytest.fixture
def sample_categories():
    """Sample categories for testing."""
    return ["analysis", "dsp", "midi", "sequencer", "synthesis"]


@pytest.fixture
def sample_json(temp_json, sample_entries, sample_categories):
    """Create a temporary JSON file with sample entries and categories."""
    data = {"categories": sample_categories, "entries": sample_entries}
    with open(temp_json, "w") as f:
        json.dump(data, f)
    return temp_json
