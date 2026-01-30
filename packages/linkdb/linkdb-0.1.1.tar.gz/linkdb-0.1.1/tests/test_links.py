"""Tests for links feature."""

import json
import subprocess
import sys

import pytest

from linkdb import (
    Link,
    export_to_json,
    generate_readme,
    get_connection,
    import_from_json,
    init_db,
)


class TestLinkDataclass:
    """Tests for Link dataclass."""

    def test_create_link(self):
        """Should create a Link instance."""
        link = Link(
            id=1,
            entry_id=10,
            url="https://example.com/article",
            title="Example Article",
            link_type="article",
            note="Great read",
        )
        assert link.id == 1
        assert link.entry_id == 10
        assert link.url == "https://example.com/article"
        assert link.title == "Example Article"
        assert link.link_type == "article"
        assert link.note == "Great read"

    def test_link_to_dict_minimal(self):
        """to_dict should return minimal dict with just url."""
        link = Link(
            id=1,
            entry_id=10,
            url="https://example.com",
        )
        d = link.to_dict()
        assert d == {"url": "https://example.com"}

    def test_link_to_dict_full(self):
        """to_dict should include all non-None fields."""
        link = Link(
            id=1,
            entry_id=10,
            url="https://example.com",
            title="Title",
            link_type="tutorial",
            note="Note",
        )
        d = link.to_dict()
        assert d == {
            "url": "https://example.com",
            "title": "Title",
            "link_type": "tutorial",
            "note": "Note",
        }

    def test_link_to_dict_with_id(self):
        """to_dict with include_id=True should include id."""
        link = Link(
            id=5,
            entry_id=10,
            url="https://example.com",
        )
        d = link.to_dict(include_id=True)
        assert d == {"url": "https://example.com", "id": 5}

    def test_validate_type_valid(self):
        """validate_type should accept valid types."""
        for link_type in Link.VALID_TYPES:
            is_valid, error = Link.validate_type(link_type)
            assert is_valid is True
            assert error is None

    def test_validate_type_none(self):
        """validate_type should accept None."""
        is_valid, error = Link.validate_type(None)
        assert is_valid is True
        assert error is None

    def test_validate_type_invalid(self):
        """validate_type should reject invalid types."""
        is_valid, error = Link.validate_type("invalid_type")
        assert is_valid is False
        assert "Invalid link_type" in error
        assert "invalid_type" in error


class TestLinkDatabase:
    """Tests for link database operations."""

    def test_create_link_in_db(self, temp_db):
        """Should be able to insert a link."""
        db_path, conn = temp_db

        cursor = conn.cursor()
        # Create entry first
        cursor.execute(
            "INSERT INTO entry (name, category, description, repo) VALUES (?, ?, ?, ?)",
            ("test-project", "dsp", "Test", "https://github.com/t/t"),
        )
        entry_id = cursor.lastrowid

        # Create link
        cursor.execute(
            "INSERT INTO link (entry_id, url, title, link_type, note) VALUES (?, ?, ?, ?, ?)",
            (entry_id, "https://example.com", "Title", "article", "Note"),
        )
        conn.commit()

        cursor.execute("SELECT * FROM link WHERE entry_id = ?", (entry_id,))
        row = cursor.fetchone()
        assert row is not None
        assert row["url"] == "https://example.com"
        assert row["title"] == "Title"
        assert row["link_type"] == "article"
        assert row["note"] == "Note"

    def test_link_from_row(self, temp_db):
        """Link.from_row should create Link from database row."""
        db_path, conn = temp_db

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO entry (name, category, description, repo) VALUES (?, ?, ?, ?)",
            ("test-project", "dsp", "Test", "https://github.com/t/t"),
        )
        entry_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO link (entry_id, url, title, link_type, note) VALUES (?, ?, ?, ?, ?)",
            (entry_id, "https://example.com", "Title", "video", "Note"),
        )
        conn.commit()

        cursor.execute("SELECT * FROM link WHERE entry_id = ?", (entry_id,))
        row = cursor.fetchone()

        link = Link.from_row(row)
        assert link.entry_id == entry_id
        assert link.url == "https://example.com"
        assert link.title == "Title"
        assert link.link_type == "video"
        assert link.note == "Note"
        assert link.created_at is not None

    def test_cascade_delete(self, temp_db):
        """Deleting entry should cascade delete its links."""
        db_path, conn = temp_db

        cursor = conn.cursor()
        # Create entry with links
        cursor.execute(
            "INSERT INTO entry (name, category, description, repo) VALUES (?, ?, ?, ?)",
            ("test-project", "dsp", "Test", "https://github.com/t/t"),
        )
        entry_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO link (entry_id, url) VALUES (?, ?)",
            (entry_id, "https://link1.com"),
        )
        cursor.execute(
            "INSERT INTO link (entry_id, url) VALUES (?, ?)",
            (entry_id, "https://link2.com"),
        )
        conn.commit()

        # Verify links exist
        cursor.execute("SELECT COUNT(*) FROM link WHERE entry_id = ?", (entry_id,))
        assert cursor.fetchone()[0] == 2

        # Delete entry
        cursor.execute("DELETE FROM entry WHERE id = ?", (entry_id,))
        conn.commit()

        # Links should be gone
        cursor.execute("SELECT COUNT(*) FROM link WHERE entry_id = ?", (entry_id,))
        assert cursor.fetchone()[0] == 0

    def test_multiple_links_per_entry(self, temp_db):
        """Entry should support multiple links."""
        db_path, conn = temp_db

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO entry (name, category, description, repo) VALUES (?, ?, ?, ?)",
            ("test-project", "dsp", "Test", "https://github.com/t/t"),
        )
        entry_id = cursor.lastrowid

        # Add multiple links
        links = [
            ("https://article.com", "article", "Article"),
            ("https://video.com", "video", "Video"),
            ("https://docs.com", "docs", "Docs"),
        ]
        for url, link_type, title in links:
            cursor.execute(
                "INSERT INTO link (entry_id, url, link_type, title) VALUES (?, ?, ?, ?)",
                (entry_id, url, link_type, title),
            )
        conn.commit()

        cursor.execute(
            "SELECT * FROM link WHERE entry_id = ? ORDER BY id", (entry_id,)
        )
        rows = cursor.fetchall()
        assert len(rows) == 3
        assert rows[0]["link_type"] == "article"
        assert rows[1]["link_type"] == "video"
        assert rows[2]["link_type"] == "docs"


class TestLinksImportExport:
    """Tests for importing and exporting links via JSON."""

    def test_import_entry_with_links(self, temp_json, temp_db):
        """Should import entry with links."""
        db_path, conn = temp_db
        conn.close()

        data = {
            "categories": ["dsp"],
            "entries": [
                {
                    "name": "project-with-links",
                    "category": "dsp",
                    "desc": "A project",
                    "repo": "https://github.com/t/t",
                    "links": [
                        {
                            "url": "https://article.com",
                            "title": "Article",
                            "link_type": "article",
                            "note": "Great read",
                        },
                        {
                            "url": "https://video.com",
                            "link_type": "video",
                        },
                    ],
                },
            ],
        }
        with open(temp_json, "w") as f:
            json.dump(data, f)

        imported, skipped, errors = import_from_json(temp_json, db_path)

        assert imported == 1
        assert len(errors) == 0

        # Verify links in database
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM entry WHERE name = ?", ("project-with-links",))
        entry_id = cursor.fetchone()["id"]

        cursor.execute(
            "SELECT * FROM link WHERE entry_id = ? ORDER BY id", (entry_id,)
        )
        links = cursor.fetchall()
        assert len(links) == 2
        assert links[0]["title"] == "Article"
        assert links[0]["link_type"] == "article"
        assert links[1]["url"] == "https://video.com"
        conn.close()

    def test_export_entry_with_links(self, temp_db, temp_json):
        """Should export entries with their links."""
        db_path, conn = temp_db

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO entry (name, category, description, repo) VALUES (?, ?, ?, ?)",
            ("project-with-links", "dsp", "Test project", "https://github.com/t/t"),
        )
        entry_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO link (entry_id, url, title, link_type) VALUES (?, ?, ?, ?)",
            (entry_id, "https://article.com", "Article Title", "article"),
        )
        conn.commit()
        conn.close()

        count = export_to_json(db_path, temp_json)
        assert count == 1

        with open(temp_json) as f:
            exported = json.load(f)

        entries = exported["entries"]
        assert len(entries) == 1
        assert "links" in entries[0]
        assert len(entries[0]["links"]) == 1
        assert entries[0]["links"][0]["url"] == "https://article.com"
        assert entries[0]["links"][0]["title"] == "Article Title"
        assert entries[0]["links"][0]["link_type"] == "article"

    def test_import_export_round_trip(self, temp_json, temp_db):
        """Import and export should preserve links."""
        db_path, conn = temp_db
        conn.close()

        original_data = {
            "categories": ["dsp"],
            "entries": [
                {
                    "name": "round-trip-test",
                    "category": "dsp",
                    "desc": "Round trip test",
                    "repo": "https://github.com/t/t",
                    "links": [
                        {
                            "url": "https://link1.com",
                            "title": "Link 1",
                            "link_type": "article",
                            "note": "Note 1",
                        },
                        {
                            "url": "https://link2.com",
                            "link_type": "tutorial",
                        },
                    ],
                },
            ],
        }
        with open(temp_json, "w") as f:
            json.dump(original_data, f)

        # Import
        import_from_json(temp_json, db_path)

        # Export to different file
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            export_path = Path(f.name)

        try:
            export_to_json(db_path, export_path)

            with open(export_path) as f:
                exported = json.load(f)

            entry = exported["entries"][0]
            assert len(entry["links"]) == 2

            # First link should have all fields
            link1 = entry["links"][0]
            assert link1["url"] == "https://link1.com"
            assert link1["title"] == "Link 1"
            assert link1["link_type"] == "article"
            assert link1["note"] == "Note 1"

            # Second link has minimal fields
            link2 = entry["links"][1]
            assert link2["url"] == "https://link2.com"
            assert link2["link_type"] == "tutorial"
        finally:
            export_path.unlink(missing_ok=True)

    def test_import_invalid_link_type(self, temp_json, temp_db):
        """Should report error for invalid link type."""
        db_path, conn = temp_db
        conn.close()

        data = {
            "categories": ["dsp"],
            "entries": [
                {
                    "name": "project",
                    "category": "dsp",
                    "desc": "Test",
                    "repo": "https://github.com/t/t",
                    "links": [
                        {
                            "url": "https://example.com",
                            "link_type": "invalid_type",
                        },
                    ],
                },
            ],
        }
        with open(temp_json, "w") as f:
            json.dump(data, f)

        imported, skipped, errors = import_from_json(temp_json, db_path)

        assert imported == 1  # Entry is still imported
        assert len(errors) == 1  # But link error is reported
        assert "Invalid link_type" in errors[0]


class TestLinksReadmeGeneration:
    """Tests for README generation with links."""

    def test_readme_includes_links(self, temp_db):
        """README should include relevant links section."""
        db_path, conn = temp_db

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO entry (name, category, description, repo) VALUES (?, ?, ?, ?)",
            ("test-project", "dsp", "Test description", "https://github.com/t/t"),
        )
        entry_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO link (entry_id, url, title, link_type, note) VALUES (?, ?, ?, ?, ?)",
            (entry_id, "https://article.com", "Getting Started", "article", "Great intro"),
        )
        conn.commit()
        conn.close()

        readme = generate_readme(db_path)

        assert "test-project" in readme
        assert "Relevant Links:" in readme
        assert "[Getting Started](https://article.com)" in readme
        assert "[article]" in readme
        assert "Great intro" in readme

    def test_readme_entry_without_links(self, temp_db):
        """README should not show links section for entries without links."""
        db_path, conn = temp_db

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO entry (name, category, description, repo) VALUES (?, ?, ?, ?)",
            ("no-links-project", "dsp", "No links", "https://github.com/t/t"),
        )
        conn.commit()
        conn.close()

        readme = generate_readme(db_path)

        assert "no-links-project" in readme
        assert "Relevant Links:" not in readme

    def test_readme_multiple_links(self, temp_db):
        """README should show all links for an entry."""
        db_path, conn = temp_db

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO entry (name, category, description, repo) VALUES (?, ?, ?, ?)",
            ("multi-link-project", "dsp", "Multiple links", "https://github.com/t/t"),
        )
        entry_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO link (entry_id, url, title, link_type) VALUES (?, ?, ?, ?)",
            (entry_id, "https://docs.com", "Documentation", "docs"),
        )
        cursor.execute(
            "INSERT INTO link (entry_id, url, title, link_type) VALUES (?, ?, ?, ?)",
            (entry_id, "https://video.com", "Tutorial Video", "video"),
        )
        conn.commit()
        conn.close()

        readme = generate_readme(db_path)

        assert "[Documentation](https://docs.com)" in readme
        assert "[docs]" in readme
        assert "[Tutorial Video](https://video.com)" in readme
        assert "[video]" in readme


class TestLinksCLI:
    """Tests for link CLI commands."""

    @pytest.fixture
    def cli_setup(self, temp_db, temp_json):
        """Set up database and JSON for CLI tests."""
        db_path, conn = temp_db

        # Create entry
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO entry (name, category, description, repo) VALUES (?, ?, ?, ?)",
            ("cli-test-project", "dsp", "CLI test", "https://github.com/t/t"),
        )
        conn.commit()

        # Create matching JSON
        data = {
            "categories": ["dsp"],
            "entries": [
                {
                    "name": "cli-test-project",
                    "category": "dsp",
                    "desc": "CLI test",
                    "repo": "https://github.com/t/t",
                },
            ],
        }
        with open(temp_json, "w") as f:
            json.dump(data, f)

        yield db_path, temp_json

        conn.close()

    def test_add_link_command(self, cli_setup):
        """add-link should add a link to an entry."""
        db_path, json_path = cli_setup

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "linkdb",
                "add-link",
                "cli-test-project",
                "https://example.com/article",
                "-t",
                "Test Article",
                "--type",
                "article",
                "-n",
                "Test note",
                "--db",
                str(db_path),
                "-j",
                str(json_path),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Added link" in result.stdout

        # Verify in database
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM link")
        link = cursor.fetchone()
        assert link["url"] == "https://example.com/article"
        assert link["title"] == "Test Article"
        assert link["link_type"] == "article"
        conn.close()

        # Verify in JSON
        with open(json_path) as f:
            data = json.load(f)
        entry = data["entries"][0]
        assert "links" in entry
        assert len(entry["links"]) == 1
        assert entry["links"][0]["url"] == "https://example.com/article"

    def test_remove_link_command(self, cli_setup):
        """remove-link should remove a link from an entry."""
        db_path, json_path = cli_setup

        # First add a link
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM entry WHERE name = ?", ("cli-test-project",))
        entry_id = cursor.fetchone()["id"]
        cursor.execute(
            "INSERT INTO link (entry_id, url) VALUES (?, ?)",
            (entry_id, "https://to-remove.com"),
        )
        conn.commit()
        conn.close()

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "linkdb",
                "remove-link",
                "cli-test-project",
                "https://to-remove.com",
                "--db",
                str(db_path),
                "-j",
                str(json_path),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Removed link" in result.stdout

        # Verify link is gone
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM link")
        assert cursor.fetchone()[0] == 0
        conn.close()

    def test_list_links_command(self, cli_setup):
        """list-links should show links for an entry."""
        db_path, json_path = cli_setup

        # Add links
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM entry WHERE name = ?", ("cli-test-project",))
        entry_id = cursor.fetchone()["id"]
        cursor.execute(
            "INSERT INTO link (entry_id, url, title, link_type) VALUES (?, ?, ?, ?)",
            (entry_id, "https://docs.com", "Documentation", "docs"),
        )
        conn.commit()
        conn.close()

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "linkdb",
                "list-links",
                "cli-test-project",
                "--db",
                str(db_path),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "https://docs.com" in result.stdout
        assert "[docs]" in result.stdout
        assert "Documentation" in result.stdout

    def test_list_links_json_format(self, cli_setup):
        """list-links with json format should output valid JSON."""
        db_path, json_path = cli_setup

        # Add link
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM entry WHERE name = ?", ("cli-test-project",))
        entry_id = cursor.fetchone()["id"]
        cursor.execute(
            "INSERT INTO link (entry_id, url, link_type) VALUES (?, ?, ?)",
            (entry_id, "https://test.com", "article"),
        )
        conn.commit()
        conn.close()

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "linkdb",
                "list-links",
                "cli-test-project",
                "-f",
                "json",
                "--db",
                str(db_path),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "entry" in output
        assert "links" in output
        assert len(output["links"]) == 1
        assert output["links"][0]["url"] == "https://test.com"

    def test_add_link_duplicate_error(self, cli_setup):
        """add-link should error on duplicate link."""
        db_path, json_path = cli_setup

        # Add link first time
        subprocess.run(
            [
                sys.executable,
                "-m",
                "linkdb",
                "add-link",
                "cli-test-project",
                "https://duplicate.com",
                "--db",
                str(db_path),
                "-j",
                str(json_path),
            ],
            capture_output=True,
        )

        # Try to add same link again
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "linkdb",
                "add-link",
                "cli-test-project",
                "https://duplicate.com",
                "--db",
                str(db_path),
                "-j",
                str(json_path),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "already exists" in result.stdout

    def test_add_link_invalid_type_error(self, cli_setup):
        """add-link should error on invalid link type."""
        db_path, json_path = cli_setup

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "linkdb",
                "add-link",
                "cli-test-project",
                "https://example.com",
                "--type",
                "invalid",
                "--db",
                str(db_path),
                "-j",
                str(json_path),
            ],
            capture_output=True,
            text=True,
        )

        # argparse should reject invalid choice
        assert result.returncode != 0

    def test_add_link_entry_not_found(self, cli_setup):
        """add-link should error for nonexistent entry."""
        db_path, json_path = cli_setup

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "linkdb",
                "add-link",
                "nonexistent-entry",
                "https://example.com",
                "--db",
                str(db_path),
                "-j",
                str(json_path),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "not found" in result.stdout
