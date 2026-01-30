"""Tests for schema validation."""

from linkdb import load_categories, validate_entry, validate_entries


class TestValidateEntry:
    """Tests for validate_entry function."""

    def test_valid_entry_with_url_and_repo(self):
        """Entry with both url and repo should be valid."""
        entry = {
            "name": "test-project",
            "category": "dsp",
            "desc": "A test project",
            "url": "https://example.com",
            "repo": "https://github.com/test/test",
        }
        is_valid, error = validate_entry(entry)
        assert is_valid
        assert error is None

    def test_valid_entry_with_only_repo(self):
        """Entry with only repo should be valid."""
        entry = {
            "name": "test-project",
            "category": "dsp",
            "desc": "A test project",
            "repo": "https://github.com/test/test",
        }
        is_valid, error = validate_entry(entry)
        assert is_valid

    def test_valid_entry_with_only_url(self):
        """Entry with only url should be valid."""
        entry = {
            "name": "test-project",
            "category": "dsp",
            "desc": "A test project",
            "url": "https://example.com",
        }
        is_valid, error = validate_entry(entry)
        assert is_valid

    def test_invalid_entry_no_url_or_repo(self):
        """Entry without url or repo should be invalid."""
        entry = {
            "name": "test-project",
            "category": "dsp",
            "desc": "A test project",
        }
        is_valid, error = validate_entry(entry)
        assert not is_valid
        assert "must have url or repo" in error

    def test_invalid_entry_name_is_url(self):
        """Entry with URL as name should be invalid."""
        entry = {
            "name": "https://github.com/test/test",
            "category": "dsp",
            "desc": "A test project",
            "repo": "https://github.com/test/test",
        }
        is_valid, error = validate_entry(entry)
        assert not is_valid
        assert "name should not be a URL" in error

    def test_invalid_entry_empty_name(self):
        """Entry with empty name should be invalid."""
        entry = {
            "name": "",
            "category": "dsp",
            "desc": "A test project",
            "repo": "https://github.com/test/test",
        }
        is_valid, error = validate_entry(entry)
        assert not is_valid
        assert "cannot be empty" in error


class TestValidateEntries:
    """Tests for validate_entries function."""

    def test_valid_entries(self, sample_entries):
        """Valid entries should pass validation."""
        result = validate_entries(sample_entries)
        assert result.is_valid
        assert len(result.valid) == 3
        assert len(result.errors) == 0

    def test_duplicate_detection(self):
        """Duplicate entries should be detected."""
        entries = [
            {
                "name": "dupe",
                "category": "dsp",
                "desc": "First",
                "repo": "https://github.com/a/a",
            },
            {
                "name": "unique",
                "category": "dsp",
                "desc": "Unique",
                "repo": "https://github.com/b/b",
            },
            {
                "name": "dupe",
                "category": "analysis",
                "desc": "Second",
                "repo": "https://github.com/c/c",
            },
        ]
        result = validate_entries(entries)
        assert len(result.duplicates) == 1
        assert result.duplicates[0][0] == "dupe"
        assert result.duplicates[0][1] == [1, 3]

    def test_invalid_category_error(self):
        """Invalid categories should produce errors by default."""
        entries = [
            {
                "name": "test",
                "category": "weird-category",
                "desc": "Test",
                "repo": "https://github.com/a/a",
            },
        ]
        result = validate_entries(entries)
        assert not result.is_valid
        assert len(result.errors) == 1
        assert "invalid category" in result.errors[0][2]

    def test_invalid_category_warning_non_strict(self):
        """Invalid categories should produce warnings in non-strict mode."""
        entries = [
            {
                "name": "test",
                "category": "weird-category",
                "desc": "Test",
                "repo": "https://github.com/a/a",
            },
        ]
        result = validate_entries(entries, strict_categories=False)
        assert result.is_valid  # Warnings don't make it invalid
        assert len(result.warnings) == 1
        assert "invalid category" in result.warnings[0][2]

    def test_canonical_category_no_warning(self):
        """Canonical categories should not produce warnings."""
        entries = [
            {
                "name": "test",
                "category": "dsp",
                "desc": "Test",
                "repo": "https://github.com/a/a",
            },
        ]
        result = validate_entries(entries)
        assert result.is_valid
        assert len(result.warnings) == 0

    def test_non_canonical_category_warns(self):
        """Non-canonical category format should produce a warning."""
        entries = [
            {
                "name": "test",
                "category": "Audio Interface",  # Should be "audio-interface"
                "desc": "Test",
                "repo": "https://github.com/a/a",
            },
        ]
        result = validate_entries(entries)
        assert result.is_valid  # Still valid, just a warning
        assert len(result.valid) == 1
        assert len(result.warnings) == 1
        assert "should be 'audio-interface'" in result.warnings[0][2]

    def test_error_propagation(self):
        """Invalid entries should produce errors."""
        entries = [
            {
                "name": "",
                "category": "dsp",
                "desc": "Bad name",
                "repo": "https://github.com/a/a",
            },
            {
                "name": "good",
                "category": "dsp",
                "desc": "Good",
                "repo": "https://github.com/b/b",
            },
        ]
        result = validate_entries(entries)
        assert not result.is_valid
        assert len(result.errors) == 1
        assert len(result.valid) == 1


class TestCategories:
    """Tests for category loading from JSON."""

    def test_categories_are_lowercase(self):
        """All canonical categories should be lowercase."""
        categories = load_categories()
        for cat in categories:
            assert cat == cat.lower(), f"Category '{cat}' should be lowercase"

    def test_essential_categories_present(self):
        """Essential categories should be in the set."""
        categories = load_categories()
        essential = {"dsp", "analysis", "midi", "daw", "synthesis", "plugins"}
        assert essential.issubset(categories)
