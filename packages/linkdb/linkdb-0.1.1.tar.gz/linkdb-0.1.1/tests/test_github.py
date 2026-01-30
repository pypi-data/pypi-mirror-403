"""Tests for GitHub API integration."""

import json
import tempfile
from pathlib import Path

import pytest

from linkdb import RepoResult, RepoStats, parse_github_url


@pytest.fixture
def temp_json():
    """Create a temporary JSON file with categories."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        data = {
            "categories": [
                "analysis",
                "audio-interface",
                "dsp",
                "frameworks",
                "midi",
                "synthesis",
            ],
            "entries": [],
        }
        json.dump(data, f)
        json_path = Path(f.name)

    yield json_path

    json_path.unlink(missing_ok=True)


@pytest.fixture
def temp_db():
    """Create a temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    yield db_path

    db_path.unlink(missing_ok=True)


class TestParseGithubUrl:
    """Tests for parse_github_url function."""

    def test_parse_https_url(self):
        """Should parse standard HTTPS URL."""
        result = parse_github_url("https://github.com/owner/repo")
        assert result == ("owner", "repo")

    def test_parse_https_url_with_www(self):
        """Should parse URL with www prefix."""
        result = parse_github_url("https://www.github.com/owner/repo")
        assert result == ("owner", "repo")

    def test_parse_http_url(self):
        """Should parse HTTP URL."""
        result = parse_github_url("http://github.com/owner/repo")
        assert result == ("owner", "repo")

    def test_parse_url_with_trailing_slash(self):
        """Should handle trailing slash."""
        result = parse_github_url("https://github.com/owner/repo/")
        assert result == ("owner", "repo")

    def test_parse_url_with_subpath(self):
        """Should handle URLs with subpaths."""
        result = parse_github_url("https://github.com/owner/repo/tree/main")
        assert result == ("owner", "repo")

    def test_parse_url_with_git_suffix(self):
        """Should handle .git suffix."""
        result = parse_github_url("https://github.com/owner/repo.git")
        assert result == ("owner", "repo")

    def test_parse_non_github_url(self):
        """Should return None for non-GitHub URLs."""
        result = parse_github_url("https://gitlab.com/owner/repo")
        assert result is None

    def test_parse_empty_url(self):
        """Should return None for empty URL."""
        result = parse_github_url("")
        assert result is None

    def test_parse_none_url(self):
        """Should return None for None."""
        result = parse_github_url(None)
        assert result is None


class TestRepoStats:
    """Tests for RepoStats dataclass."""

    def test_days_since_push(self):
        """Should calculate days since last push."""
        from datetime import datetime, timedelta

        yesterday = datetime.now() - timedelta(days=1)
        stats = RepoStats(
            owner="test",
            name="repo",
            full_name="test/repo",
            description="Test repo",
            stars=100,
            forks=10,
            open_issues=5,
            watchers=50,
            language="Python",
            license="MIT",
            created_at=datetime.now() - timedelta(days=365),
            updated_at=datetime.now(),
            pushed_at=yesterday,
            archived=False,
            fork=False,
            default_branch="main",
            topics=["audio", "python"],
        )
        assert stats.days_since_push == 1

    def test_is_active_recent_push(self):
        """Should be active if pushed recently."""
        from datetime import datetime, timedelta

        stats = RepoStats(
            owner="test",
            name="repo",
            full_name="test/repo",
            description=None,
            stars=0,
            forks=0,
            open_issues=0,
            watchers=0,
            language=None,
            license=None,
            created_at=None,
            updated_at=None,
            pushed_at=datetime.now() - timedelta(days=30),
            archived=False,
            fork=False,
            default_branch="main",
            topics=[],
        )
        assert stats.is_active

    def test_is_not_active_old_push(self):
        """Should not be active if not pushed in over a year."""
        from datetime import datetime, timedelta

        stats = RepoStats(
            owner="test",
            name="repo",
            full_name="test/repo",
            description=None,
            stars=0,
            forks=0,
            open_issues=0,
            watchers=0,
            language=None,
            license=None,
            created_at=None,
            updated_at=None,
            pushed_at=datetime.now() - timedelta(days=400),
            archived=False,
            fork=False,
            default_branch="main",
            topics=[],
        )
        assert not stats.is_active

    def test_activity_status_archived(self):
        """Archived repos should have archived status."""
        from datetime import datetime

        stats = RepoStats(
            owner="test",
            name="repo",
            full_name="test/repo",
            description=None,
            stars=0,
            forks=0,
            open_issues=0,
            watchers=0,
            language=None,
            license=None,
            created_at=None,
            updated_at=None,
            pushed_at=datetime.now(),
            archived=True,
            fork=False,
            default_branch="main",
            topics=[],
        )
        assert stats.activity_status == "archived"

    def test_activity_status_very_active(self):
        """Recently pushed repos should be very active."""
        from datetime import datetime, timedelta

        stats = RepoStats(
            owner="test",
            name="repo",
            full_name="test/repo",
            description=None,
            stars=0,
            forks=0,
            open_issues=0,
            watchers=0,
            language=None,
            license=None,
            created_at=None,
            updated_at=None,
            pushed_at=datetime.now() - timedelta(days=7),
            archived=False,
            fork=False,
            default_branch="main",
            topics=[],
        )
        assert stats.activity_status == "very active"

    def test_activity_status_stale(self):
        """Old repos should be stale."""
        from datetime import datetime, timedelta

        stats = RepoStats(
            owner="test",
            name="repo",
            full_name="test/repo",
            description=None,
            stars=0,
            forks=0,
            open_issues=0,
            watchers=0,
            language=None,
            license=None,
            created_at=None,
            updated_at=None,
            pushed_at=datetime.now() - timedelta(days=500),
            archived=False,
            fork=False,
            default_branch="main",
            topics=[],
        )
        assert stats.activity_status == "stale"


class TestRepoResult:
    """Tests for RepoResult dataclass."""

    def test_success_with_stats(self):
        """Should be successful when stats are present."""
        from datetime import datetime

        stats = RepoStats(
            owner="test",
            name="repo",
            full_name="test/repo",
            description=None,
            stars=0,
            forks=0,
            open_issues=0,
            watchers=0,
            language=None,
            license=None,
            created_at=None,
            updated_at=None,
            pushed_at=datetime.now(),
            archived=False,
            fork=False,
            default_branch="main",
            topics=[],
        )
        result = RepoResult(
            entry_name="test",
            repo_url="https://github.com/test/repo",
            stats=stats,
        )
        assert result.success

    def test_not_success_with_error(self):
        """Should not be successful when there's an error."""
        result = RepoResult(
            entry_name="test",
            repo_url="https://github.com/test/repo",
            error="Not found",
        )
        assert not result.success


class TestRepoStatsHomepage:
    """Tests for RepoStats homepage field."""

    def test_homepage_field(self):
        """Should have homepage field."""
        from datetime import datetime

        stats = RepoStats(
            owner="test",
            name="repo",
            full_name="test/repo",
            description="Test repo",
            stars=100,
            forks=10,
            open_issues=5,
            watchers=50,
            language="Python",
            license="MIT",
            created_at=None,
            updated_at=None,
            pushed_at=datetime.now(),
            archived=False,
            fork=False,
            default_branch="main",
            topics=[],
            homepage="https://example.com",
        )
        assert stats.homepage == "https://example.com"

    def test_homepage_none(self):
        """Homepage should default to None."""
        from datetime import datetime

        stats = RepoStats(
            owner="test",
            name="repo",
            full_name="test/repo",
            description=None,
            stars=0,
            forks=0,
            open_issues=0,
            watchers=0,
            language=None,
            license=None,
            created_at=None,
            updated_at=None,
            pushed_at=datetime.now(),
            archived=False,
            fork=False,
            default_branch="main",
            topics=[],
        )
        assert stats.homepage is None


class TestAddEntryFromGithub:
    """Tests for add_entry_from_github function."""

    def test_invalid_url_raises_valueerror(self, temp_json, temp_db):
        """Should raise ValueError for non-GitHub URLs."""
        from linkdb import add_entry_from_github

        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            add_entry_from_github(
                github_url="https://gitlab.com/foo/bar",
                category="dsp",
                json_path=temp_json,
                db_path=temp_db,
            )

    def test_empty_url_raises_valueerror(self, temp_json, temp_db):
        """Should raise ValueError for empty URLs."""
        from linkdb import add_entry_from_github

        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            add_entry_from_github(
                github_url="",
                category="dsp",
                json_path=temp_json,
                db_path=temp_db,
            )


class TestEntryGithubFields:
    """Tests for Entry dataclass GitHub fields."""

    def test_entry_has_github_fields(self):
        """Entry should have GitHub-specific fields."""
        from linkdb import Entry

        entry = Entry(
            id=1,
            name="test",
            category="dsp",
            url=None,
            repo="https://github.com/test/repo",
            description="Test",
            stars=100,
            forks=10,
            language="Python",
            license="MIT",
            archived=False,
            last_pushed="2024-01-15",
        )
        assert entry.stars == 100
        assert entry.forks == 10
        assert entry.language == "Python"
        assert entry.license == "MIT"
        assert entry.archived is False
        assert entry.last_pushed == "2024-01-15"

    def test_entry_to_dict_includes_github_fields(self):
        """Entry.to_dict() should include GitHub fields."""
        from linkdb import Entry

        entry = Entry(
            id=1,
            name="test",
            category="dsp",
            url=None,
            repo="https://github.com/test/repo",
            description="Test",
            stars=500,
            forks=25,
            language="C++",
            license="GPL-3.0",
            archived=True,
            last_pushed="2023-06-01",
        )
        d = entry.to_dict()
        assert d["stars"] == 500
        assert d["forks"] == 25
        assert d["language"] == "C++"
        assert d["license"] == "GPL-3.0"
        assert d["archived"] is True
        assert d["last_pushed"] == "2023-06-01"

    def test_entry_github_fields_default_to_none(self):
        """GitHub fields should default to None."""
        from linkdb import Entry

        entry = Entry(
            id=1,
            name="test",
            category="dsp",
            url=None,
            repo="https://github.com/test/repo",
            description="Test",
        )
        assert entry.stars is None
        assert entry.forks is None
        assert entry.language is None
        assert entry.license is None
        assert entry.archived is None
        assert entry.last_pushed is None


class TestDatabaseMigration:
    """Tests for database schema migration."""

    def test_init_db_creates_new_columns(self, temp_db):
        """init_db should create all GitHub columns."""
        from linkdb import init_db, get_connection

        conn = init_db(temp_db)
        conn.close()

        conn = get_connection(temp_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(entry)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        assert "stars" in columns
        assert "forks" in columns
        assert "language" in columns
        assert "license" in columns
        assert "archived" in columns
        assert "last_pushed" in columns

    def test_migrate_existing_db(self, temp_db):
        """Migration should add columns to existing database without them."""
        import sqlite3
        from linkdb import _migrate_db, get_connection

        # Create old-style database manually (without new columns)
        conn = sqlite3.connect(temp_db)
        conn.execute("""
            CREATE TABLE entry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL,
                url TEXT,
                repo TEXT,
                description TEXT NOT NULL,
                keywords TEXT,
                last_updated DATE,
                last_checked DATE
            )
        """)
        conn.execute(
            "INSERT INTO entry (name, category, description, repo) VALUES (?, ?, ?, ?)",
            ("old-entry", "dsp", "An old entry", "https://github.com/old/repo"),
        )
        conn.commit()

        # Run migration
        _migrate_db(conn)
        conn.close()

        # Verify columns exist and data preserved
        conn = get_connection(temp_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(entry)")
        columns = {row[1] for row in cursor.fetchall()}

        assert "stars" in columns
        assert "forks" in columns
        assert "language" in columns

        # Verify data preserved
        cursor.execute(
            "SELECT name, description FROM entry WHERE name = ?", ("old-entry",)
        )
        row = cursor.fetchone()
        assert row["name"] == "old-entry"
        assert row["description"] == "An old entry"
        conn.close()

    def test_entry_from_row_with_github_fields(self, temp_db):
        """Entry.from_row should handle GitHub fields from database."""
        from linkdb import init_db, Entry

        conn = init_db(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO entry
               (name, category, description, repo, stars, forks, language, license, archived, last_pushed)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "test-repo",
                "dsp",
                "Test",
                "https://github.com/t/t",
                1000,
                50,
                "Rust",
                "MIT",
                0,
                "2024-01-15",
            ),
        )
        conn.commit()

        cursor.execute("SELECT * FROM entry WHERE name = ?", ("test-repo",))
        row = cursor.fetchone()
        conn.close()

        entry = Entry.from_row(row)
        assert entry.stars == 1000
        assert entry.forks == 50
        assert entry.language == "Rust"
        assert entry.license == "MIT"
        assert entry.archived is False
        assert entry.last_pushed == "2024-01-15"

    def test_entry_from_row_archived_true(self, temp_db):
        """Entry.from_row should correctly convert archived=1 to True."""
        from linkdb import init_db, Entry

        conn = init_db(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO entry
               (name, category, description, repo, archived)
               VALUES (?, ?, ?, ?, ?)""",
            ("archived-repo", "dsp", "Archived", "https://github.com/a/a", 1),
        )
        conn.commit()

        cursor.execute("SELECT * FROM entry WHERE name = ?", ("archived-repo",))
        row = cursor.fetchone()
        conn.close()

        entry = Entry.from_row(row)
        assert entry.archived is True
