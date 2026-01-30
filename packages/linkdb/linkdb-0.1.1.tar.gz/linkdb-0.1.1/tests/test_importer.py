"""Tests for JSON import functionality."""

import json

from linkdb import export_to_json, get_connection, import_from_json


class TestImportFromJson:
    """Tests for import_from_json function."""

    def test_import_valid_entries(self, sample_json, temp_db):
        """Should import valid entries successfully."""
        db_path, conn = temp_db
        conn.close()

        imported, skipped, errors = import_from_json(sample_json, db_path)

        assert imported == 3
        assert skipped == 0
        assert len(errors) == 0

        # Verify entries in database
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entry")
        entries = cursor.fetchall()
        assert len(entries) == 3
        conn.close()

    def test_import_skips_duplicates(self, temp_json, temp_db):
        """Should skip duplicate entries when skip_duplicates=True."""
        db_path, conn = temp_db
        conn.close()

        data = {
            "categories": ["analysis", "dsp"],
            "entries": [
                {
                    "name": "dupe",
                    "category": "dsp",
                    "desc": "First",
                    "repo": "https://github.com/a/a",
                },
                {
                    "name": "dupe",
                    "category": "analysis",
                    "desc": "Second",
                    "repo": "https://github.com/b/b",
                },
                {
                    "name": "unique",
                    "category": "dsp",
                    "desc": "Unique",
                    "repo": "https://github.com/c/c",
                },
            ],
        }
        with open(temp_json, "w") as f:
            json.dump(data, f)

        imported, skipped, errors = import_from_json(temp_json, db_path)

        assert imported == 2  # dupe + unique
        assert skipped == 1  # second dupe
        assert len(errors) == 0

    def test_import_rejects_invalid_entries(self, temp_json, temp_db):
        """Should reject invalid entries with errors."""
        db_path, conn = temp_db
        conn.close()

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

        imported, skipped, errors = import_from_json(temp_json, db_path)

        assert imported == 0
        assert len(errors) > 0

    def test_import_twice_skips_existing(self, sample_json, temp_db):
        """Importing same file twice should skip existing entries."""
        db_path, conn = temp_db
        conn.close()

        # First import
        imported1, skipped1, errors1 = import_from_json(sample_json, db_path)
        assert imported1 == 3
        assert skipped1 == 0

        # Second import
        imported2, skipped2, errors2 = import_from_json(sample_json, db_path)
        assert imported2 == 0
        assert skipped2 == 3  # All skipped as duplicates


class TestExportToJson:
    """Tests for export_to_json function."""

    def test_export_entries(self, temp_db, temp_json):
        """Should export entries to JSON."""
        db_path, conn = temp_db

        # Add some entries
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO entry (name, category, description, repo) VALUES (?, ?, ?, ?)",
            ("alpha", "dsp", "Alpha project", "https://github.com/a/a"),
        )
        cursor.execute(
            "INSERT INTO entry (name, category, description, url) VALUES (?, ?, ?, ?)",
            ("beta", "analysis", "Beta project", "https://beta.com"),
        )
        conn.commit()
        conn.close()

        # Export
        count = export_to_json(db_path, temp_json)
        assert count == 2

        # Verify JSON content
        with open(temp_json) as f:
            exported = json.load(f)

        # Check structure: should have categories and entries
        assert "categories" in exported
        assert "entries" in exported
        entries = exported["entries"]
        assert len(entries) == 2
        # Should be sorted by name
        assert entries[0]["name"] == "alpha"
        assert entries[1]["name"] == "beta"
        # Categories should be derived from entries
        assert set(exported["categories"]) == {"analysis", "dsp"}

    def test_export_empty_database(self, temp_db, temp_json):
        """Should handle empty database gracefully."""
        db_path, conn = temp_db
        conn.close()

        count = export_to_json(db_path, temp_json)
        assert count == 0
