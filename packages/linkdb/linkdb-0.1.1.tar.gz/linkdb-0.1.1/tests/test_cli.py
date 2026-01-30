"""Tests for CLI commands."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


class TestDoctorCommand:
    """Tests for doctor command (replaces validate)."""

    def test_doctor_valid_file(self, sample_json):
        """Should pass checks on a correct JSON file."""
        result = subprocess.run(
            [sys.executable, "linkdb.py", "doctor", "--json", str(sample_json)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "[OK]" in result.stdout

    def test_doctor_file_with_errors(self, temp_json):
        """Should report errors for invalid entries."""
        data = {
            "categories": ["dsp"],
            "entries": [
                {
                    "name": "",
                    "category": "dsp",
                    "desc": "Bad",
                    "repo": "https://github.com/a/a",
                },
            ],
        }
        with open(temp_json, "w") as f:
            json.dump(data, f)

        result = subprocess.run(
            [sys.executable, "linkdb.py", "doctor", "--json", str(temp_json)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "[ERR]" in result.stdout

    def test_doctor_file_with_duplicates(self, temp_json):
        """Should report duplicates."""
        data = {
            "categories": ["dsp"],
            "entries": [
                {
                    "name": "dupe",
                    "category": "dsp",
                    "desc": "First",
                    "repo": "https://github.com/a/a",
                },
                {
                    "name": "dupe",
                    "category": "dsp",
                    "desc": "Second",
                    "repo": "https://github.com/b/b",
                },
            ],
        }
        with open(temp_json, "w") as f:
            json.dump(data, f)

        result = subprocess.run(
            [sys.executable, "linkdb.py", "doctor", "--json", str(temp_json)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "duplicate" in result.stdout.lower()


class TestImportCommand:
    """Tests for import command."""

    def test_import_creates_database(self, sample_json):
        """Should create database from JSON."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "linkdb.py",
                    "import",
                    "--json",
                    str(sample_json),
                    "--db",
                    str(db_path),
                ],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            assert "Import complete" in result.stdout
            assert "Imported: 3" in result.stdout
        finally:
            db_path.unlink(missing_ok=True)


class TestListCommand:
    """Tests for list command."""

    def test_list_entries(self, sample_json):
        """Should list entries from database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            # First import
            subprocess.run(
                [
                    sys.executable,
                    "linkdb.py",
                    "import",
                    "--json",
                    str(sample_json),
                    "--db",
                    str(db_path),
                ],
                capture_output=True,
                text=True,
            )

            # Then list
            result = subprocess.run(
                [sys.executable, "linkdb.py", "list", "--db", str(db_path)],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            assert "test-project-1" in result.stdout
            assert "Total: 3" in result.stdout
        finally:
            db_path.unlink(missing_ok=True)

    def test_list_with_category_filter(self, sample_json):
        """Should filter by category."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            subprocess.run(
                [
                    sys.executable,
                    "linkdb.py",
                    "import",
                    "--json",
                    str(sample_json),
                    "--db",
                    str(db_path),
                ],
                capture_output=True,
                text=True,
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "linkdb.py",
                    "list",
                    "--db",
                    str(db_path),
                    "-c",
                    "dsp",
                ],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            assert "test-project-1" in result.stdout
            assert "Total: 1" in result.stdout
        finally:
            db_path.unlink(missing_ok=True)

    def test_list_json_format(self, sample_json):
        """Should output JSON format."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            subprocess.run(
                [
                    sys.executable,
                    "linkdb.py",
                    "import",
                    "--json",
                    str(sample_json),
                    "--db",
                    str(db_path),
                ],
                capture_output=True,
                text=True,
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "linkdb.py",
                    "list",
                    "--db",
                    str(db_path),
                    "-f",
                    "json",
                ],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert len(data) == 3
        finally:
            db_path.unlink(missing_ok=True)


class TestSearchCommand:
    """Tests for search command."""

    def test_search_by_name(self, sample_json):
        """Should find entries by name."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            subprocess.run(
                [
                    sys.executable,
                    "linkdb.py",
                    "import",
                    "--json",
                    str(sample_json),
                    "--db",
                    str(db_path),
                ],
                capture_output=True,
                text=True,
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "linkdb.py",
                    "search",
                    "project-1",
                    "--db",
                    str(db_path),
                ],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            assert "test-project-1" in result.stdout
            assert "Found 1" in result.stdout
        finally:
            db_path.unlink(missing_ok=True)

    def test_search_no_results(self, sample_json):
        """Should handle no results gracefully."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            subprocess.run(
                [
                    sys.executable,
                    "linkdb.py",
                    "import",
                    "--json",
                    str(sample_json),
                    "--db",
                    str(db_path),
                ],
                capture_output=True,
                text=True,
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "linkdb.py",
                    "search",
                    "nonexistent",
                    "--db",
                    str(db_path),
                ],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            assert "No entries found" in result.stdout
        finally:
            db_path.unlink(missing_ok=True)


class TestStatsCommand:
    """Tests for stats command."""

    def test_stats_shows_counts(self, sample_json):
        """Should show database statistics."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            subprocess.run(
                [
                    sys.executable,
                    "linkdb.py",
                    "import",
                    "--json",
                    str(sample_json),
                    "--db",
                    str(db_path),
                ],
                capture_output=True,
                text=True,
            )

            result = subprocess.run(
                [sys.executable, "linkdb.py", "stats", "--db", str(db_path)],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            assert "Total entries: 3" in result.stdout
            assert "Categories:" in result.stdout
        finally:
            db_path.unlink(missing_ok=True)


class TestCategoriesCommand:
    """Tests for category command."""

    def test_categories_lists_all(self, sample_json):
        """Should list categories from JSON file."""
        result = subprocess.run(
            [
                sys.executable,
                "linkdb.py",
                "category",
                "list",
                "--json",
                str(sample_json),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "dsp" in result.stdout
        assert "analysis" in result.stdout
        assert "Categories:" in result.stdout
