"""Tests for database model."""

import sqlite3

import pytest

from linkdb import Entry


class TestEntry:
    """Tests for Entry model."""

    def test_create_entry(self, temp_db):
        """Should be able to create an entry."""
        db_path, conn = temp_db

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO entry (name, category, url, repo, description) VALUES (?, ?, ?, ?, ?)",
            (
                "test-project",
                "dsp",
                "https://example.com",
                "https://github.com/test/test",
                "A test project",
            ),
        )
        conn.commit()

        cursor.execute("SELECT * FROM entry WHERE name = ?", ("test-project",))
        row = cursor.fetchone()

        assert row is not None
        assert row["name"] == "test-project"

    def test_entry_from_row(self, temp_db):
        """Entry.from_row should create Entry from database row."""
        db_path, conn = temp_db

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO entry (name, category, url, repo, description) VALUES (?, ?, ?, ?, ?)",
            (
                "test-project",
                "dsp",
                "https://example.com",
                "https://github.com/test/test",
                "A test project",
            ),
        )
        conn.commit()

        cursor.execute("SELECT * FROM entry WHERE name = ?", ("test-project",))
        row = cursor.fetchone()

        entry = Entry.from_row(row)
        assert entry.name == "test-project"
        assert entry.category == "dsp"

    def test_entry_to_dict(self, temp_db):
        """Entry should convert to dict properly."""
        db_path, conn = temp_db

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO entry (name, category, url, repo, description, keywords) VALUES (?, ?, ?, ?, ?, ?)",
            (
                "test-project",
                "dsp",
                "https://example.com",
                "https://github.com/test/test",
                "A test project",
                "test,dsp",
            ),
        )
        conn.commit()

        cursor.execute("SELECT * FROM entry WHERE name = ?", ("test-project",))
        row = cursor.fetchone()

        entry = Entry.from_row(row)
        d = entry.to_dict()
        assert d["name"] == "test-project"
        assert d["category"] == "dsp"
        assert d["url"] == "https://example.com"
        assert d["repo"] == "https://github.com/test/test"
        assert d["description"] == "A test project"
        assert d["keywords"] == "test,dsp"

    def test_unique_name_constraint(self, temp_db):
        """Duplicate names should raise an error."""
        db_path, conn = temp_db

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO entry (name, category, description, repo) VALUES (?, ?, ?, ?)",
            ("duplicate", "dsp", "First", "https://github.com/test/test1"),
        )
        conn.commit()

        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO entry (name, category, description, repo) VALUES (?, ?, ?, ?)",
                ("duplicate", "analysis", "Second", "https://github.com/test/test2"),
            )
            conn.commit()

    def test_query_by_category(self, temp_db):
        """Should be able to query entries by category."""
        db_path, conn = temp_db

        cursor = conn.cursor()
        entries = [
            ("dsp1", "dsp", "DSP 1", "https://github.com/a/a"),
            ("dsp2", "dsp", "DSP 2", "https://github.com/b/b"),
            ("analysis1", "analysis", "Analysis 1", "https://github.com/c/c"),
        ]
        for name, cat, desc, repo in entries:
            cursor.execute(
                "INSERT INTO entry (name, category, description, repo) VALUES (?, ?, ?, ?)",
                (name, cat, desc, repo),
            )
        conn.commit()

        cursor.execute("SELECT * FROM entry WHERE category = ?", ("dsp",))
        dsp_entries = cursor.fetchall()
        assert len(dsp_entries) == 2

        cursor.execute("SELECT * FROM entry WHERE category = ?", ("analysis",))
        analysis_entries = cursor.fetchall()
        assert len(analysis_entries) == 1

    def test_nullable_fields(self, temp_db):
        """Optional fields should be nullable."""
        db_path, conn = temp_db

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO entry (name, category, description) VALUES (?, ?, ?)",
            ("minimal", "dsp", "Minimal entry"),
        )
        conn.commit()

        cursor.execute("SELECT * FROM entry WHERE name = ?", ("minimal",))
        row = cursor.fetchone()

        assert row["url"] is None
        assert row["repo"] is None
        assert row["keywords"] is None
        assert row["last_updated"] is None
        assert row["last_checked"] is None
