"""Tests for webloc parser functionality."""

import plistlib
import tempfile
from pathlib import Path

import pytest

from linkdb import (
    WeblocEntry,
    WeblocScanResult,
    parse_webloc_file,
    scan_webloc_directory,
    import_webloc_entries,
)


@pytest.fixture
def temp_webloc_dir():
    """Create a temporary directory for webloc files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_webloc(temp_webloc_dir):
    """Create a sample .webloc file."""
    webloc_path = temp_webloc_dir / "Example Project.webloc"
    plist_data = {"URL": "https://example.com/project"}
    with open(webloc_path, "wb") as f:
        plistlib.dump(plist_data, f)
    return webloc_path


@pytest.fixture
def github_webloc(temp_webloc_dir):
    """Create a GitHub .webloc file."""
    webloc_path = temp_webloc_dir / "awesome-repo.webloc"
    plist_data = {"URL": "https://github.com/owner/awesome-repo"}
    with open(webloc_path, "wb") as f:
        plistlib.dump(plist_data, f)
    return webloc_path


class TestParseWeblocFile:
    """Tests for parse_webloc_file function."""

    def test_parse_valid_webloc(self, sample_webloc):
        """Test parsing a valid webloc file."""
        entry = parse_webloc_file(sample_webloc)

        assert entry.url == "https://example.com/project"
        assert entry.name == "Example Project"
        assert entry.path == sample_webloc
        assert not entry.is_github

    def test_parse_github_webloc(self, github_webloc):
        """Test parsing a GitHub webloc file."""
        entry = parse_webloc_file(github_webloc)

        assert entry.url == "https://github.com/owner/awesome-repo"
        assert entry.name == "awesome-repo"
        assert entry.is_github

    def test_parse_nonexistent_file(self, temp_webloc_dir):
        """Test parsing a file that doesn't exist."""
        fake_path = temp_webloc_dir / "nonexistent.webloc"

        with pytest.raises(ValueError, match="File not found"):
            parse_webloc_file(fake_path)

    def test_parse_non_webloc_extension(self, temp_webloc_dir):
        """Test parsing a file without .webloc extension."""
        txt_file = temp_webloc_dir / "test.txt"
        txt_file.write_text("not a webloc")

        with pytest.raises(ValueError, match="Not a webloc file"):
            parse_webloc_file(txt_file)

    def test_parse_invalid_plist(self, temp_webloc_dir):
        """Test parsing an invalid plist file."""
        invalid_webloc = temp_webloc_dir / "invalid.webloc"
        invalid_webloc.write_text("not valid plist data")

        with pytest.raises(ValueError, match="Failed to parse plist"):
            parse_webloc_file(invalid_webloc)

    def test_parse_webloc_without_url(self, temp_webloc_dir):
        """Test parsing a webloc file without URL key."""
        no_url_webloc = temp_webloc_dir / "no-url.webloc"
        plist_data = {"SomeOtherKey": "value"}
        with open(no_url_webloc, "wb") as f:
            plistlib.dump(plist_data, f)

        with pytest.raises(ValueError, match="No URL found"):
            parse_webloc_file(no_url_webloc)

    def test_parse_binary_plist(self, temp_webloc_dir):
        """Test parsing a binary plist webloc file."""
        binary_webloc = temp_webloc_dir / "binary.webloc"
        plist_data = {"URL": "https://example.com/binary"}
        with open(binary_webloc, "wb") as f:
            plistlib.dump(plist_data, f, fmt=plistlib.FMT_BINARY)

        entry = parse_webloc_file(binary_webloc)
        assert entry.url == "https://example.com/binary"


class TestScanWeblocDirectory:
    """Tests for scan_webloc_directory function."""

    def test_scan_empty_directory(self, temp_webloc_dir):
        """Test scanning an empty directory."""
        result = scan_webloc_directory(temp_webloc_dir)

        assert result.success_count == 0
        assert result.error_count == 0
        assert len(result.entries) == 0

    def test_scan_directory_with_weblocs(self, temp_webloc_dir):
        """Test scanning a directory with multiple webloc files."""
        # Create multiple webloc files
        for i in range(3):
            webloc_path = temp_webloc_dir / f"project{i}.webloc"
            plist_data = {"URL": f"https://example.com/project{i}"}
            with open(webloc_path, "wb") as f:
                plistlib.dump(plist_data, f)

        result = scan_webloc_directory(temp_webloc_dir)

        assert result.success_count == 3
        assert result.error_count == 0
        assert len(result.entries) == 3

    def test_scan_nonexistent_directory(self, temp_webloc_dir):
        """Test scanning a directory that doesn't exist."""
        fake_dir = temp_webloc_dir / "nonexistent"
        result = scan_webloc_directory(fake_dir)

        assert result.success_count == 0
        assert result.error_count == 1
        assert "Directory not found" in result.errors[0][1]

    def test_scan_file_instead_of_directory(self, sample_webloc):
        """Test scanning a file instead of a directory."""
        result = scan_webloc_directory(sample_webloc)

        assert result.success_count == 0
        assert result.error_count == 1
        assert "Not a directory" in result.errors[0][1]

    def test_scan_recursive(self, temp_webloc_dir):
        """Test recursive scanning of subdirectories."""
        # Create webloc in root
        root_webloc = temp_webloc_dir / "root.webloc"
        plist_data = {"URL": "https://example.com/root"}
        with open(root_webloc, "wb") as f:
            plistlib.dump(plist_data, f)

        # Create webloc in subdirectory
        subdir = temp_webloc_dir / "subdir"
        subdir.mkdir()
        sub_webloc = subdir / "nested.webloc"
        plist_data = {"URL": "https://example.com/nested"}
        with open(sub_webloc, "wb") as f:
            plistlib.dump(plist_data, f)

        # Non-recursive should only find root
        result_flat = scan_webloc_directory(temp_webloc_dir, recursive=False)
        assert result_flat.success_count == 1

        # Recursive should find both
        result_recursive = scan_webloc_directory(temp_webloc_dir, recursive=True)
        assert result_recursive.success_count == 2

    def test_scan_with_mixed_valid_invalid(self, temp_webloc_dir):
        """Test scanning with mix of valid and invalid webloc files."""
        # Valid webloc
        valid_webloc = temp_webloc_dir / "valid.webloc"
        plist_data = {"URL": "https://example.com/valid"}
        with open(valid_webloc, "wb") as f:
            plistlib.dump(plist_data, f)

        # Invalid webloc (no URL)
        invalid_webloc = temp_webloc_dir / "invalid.webloc"
        plist_data = {"NotURL": "something"}
        with open(invalid_webloc, "wb") as f:
            plistlib.dump(plist_data, f)

        result = scan_webloc_directory(temp_webloc_dir)

        assert result.success_count == 1
        assert result.error_count == 1


class TestWeblocEntry:
    """Tests for WeblocEntry dataclass."""

    def test_is_github_true(self):
        """Test is_github property for GitHub URLs."""
        entry = WeblocEntry(
            path=Path("/test.webloc"),
            url="https://github.com/owner/repo",
            name="repo",
        )
        assert entry.is_github is True

    def test_is_github_false(self):
        """Test is_github property for non-GitHub URLs."""
        entry = WeblocEntry(
            path=Path("/test.webloc"),
            url="https://example.com/project",
            name="project",
        )
        assert entry.is_github is False

    def test_is_github_gitlab(self):
        """Test is_github property for GitLab URLs (should be False)."""
        entry = WeblocEntry(
            path=Path("/test.webloc"),
            url="https://gitlab.com/owner/repo",
            name="repo",
        )
        assert entry.is_github is False


class TestWeblocScanResult:
    """Tests for WeblocScanResult dataclass."""

    def test_counts(self):
        """Test success_count and error_count properties."""
        result = WeblocScanResult()
        assert result.success_count == 0
        assert result.error_count == 0

        result.entries.append(WeblocEntry(Path("/a.webloc"), "https://a.com", "a"))
        result.entries.append(WeblocEntry(Path("/b.webloc"), "https://b.com", "b"))
        result.errors.append((Path("/c.webloc"), "error"))

        assert result.success_count == 2
        assert result.error_count == 1


class TestImportWeblocEntries:
    """Tests for import_webloc_entries function."""

    def test_import_basic_entries(self, sample_json, temp_db):
        """Test importing basic webloc entries."""
        db_path, _ = temp_db

        entries = [
            WeblocEntry(
                path=Path("/test1.webloc"),
                url="https://example.com/test1",
                name="test-webloc-1",
            ),
            WeblocEntry(
                path=Path("/test2.webloc"),
                url="https://example.com/test2",
                name="test-webloc-2",
            ),
        ]

        imported, skipped, errors = import_webloc_entries(
            webloc_entries=entries,
            category="dsp",
            json_path=sample_json,
            db_path=db_path,
            use_github_metadata=False,
            default_description="Test description",
        )

        assert imported == 2
        assert skipped == 0
        assert len(errors) == 0

    def test_import_skips_duplicates(self, sample_json, temp_db):
        """Test that importing skips entries that already exist."""
        db_path, _ = temp_db

        # First entry has same name as existing entry
        entries = [
            WeblocEntry(
                path=Path("/test.webloc"),
                url="https://example.com/dup",
                name="test-project-1",  # Already exists in sample_entries
            ),
        ]

        imported, skipped, errors = import_webloc_entries(
            webloc_entries=entries,
            category="dsp",
            json_path=sample_json,
            db_path=db_path,
            use_github_metadata=False,
        )

        assert imported == 0
        assert skipped == 1
        assert len(errors) == 0

    def test_import_detects_repo_urls(self, sample_json, temp_db):
        """Test that repo hosting URLs are set as repo field, not url."""
        db_path, _ = temp_db
        from linkdb import get_entry

        entries = [
            WeblocEntry(
                path=Path("/gitlab.webloc"),
                url="https://gitlab.com/owner/repo",
                name="gitlab-project",
            ),
        ]

        imported, skipped, errors = import_webloc_entries(
            webloc_entries=entries,
            category="dsp",
            json_path=sample_json,
            db_path=db_path,
            use_github_metadata=False,
            default_description="Test",
        )

        assert imported == 1
        entry = get_entry("gitlab-project", sample_json)
        assert entry is not None
        assert entry["repo"] == "https://gitlab.com/owner/repo"
        assert entry["url"] is None

    def test_import_invalid_category(self, sample_json, temp_db):
        """Test importing with invalid category returns errors."""
        db_path, _ = temp_db

        entries = [
            WeblocEntry(
                path=Path("/test.webloc"),
                url="https://example.com/test",
                name="invalid-cat-test",
            ),
        ]

        imported, skipped, errors = import_webloc_entries(
            webloc_entries=entries,
            category="nonexistent-category",
            json_path=sample_json,
            db_path=db_path,
            use_github_metadata=False,
        )

        assert imported == 0
        assert len(errors) == 1
        assert "Unknown category" in errors[0]
