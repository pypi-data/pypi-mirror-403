"""Tests for entry API (add/remove/update)."""

import json
import tempfile
from pathlib import Path

import pytest

from linkdb import (
    add_entry,
    get_entry,
    load_data,
    load_entries,
    normalize_category_input,
    remove_entry,
    save_entries,
    sort_entries_file,
    update_entry,
    init_db,
    get_connection,
)


@pytest.fixture
def temp_json():
    """Create a temporary JSON file with categories."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        data = {
            "categories": ["analysis", "audio-interface", "dsp", "midi", "synthesis"],
            "entries": [],
        }
        json.dump(data, f)
        return Path(f.name)


@pytest.fixture
def temp_db():
    """Create a temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        return Path(f.name)


@pytest.fixture
def populated_json(temp_json):
    """Create JSON with some entries."""
    data = {
        "categories": ["analysis", "audio-interface", "dsp", "midi", "synthesis"],
        "entries": [
            {
                "name": "project-1",
                "category": "dsp",
                "desc": "First project",
                "url": None,
                "repo": "https://github.com/a/a",
            },
            {
                "name": "project-2",
                "category": "analysis",
                "desc": "Second project",
                "url": "https://example.com",
                "repo": None,
            },
        ],
    }
    with open(temp_json, "w") as f:
        json.dump(data, f)
    return temp_json


class TestNormalizeCategoryInput:
    """Tests for normalize_category_input function."""

    def test_lowercase(self):
        """Should lowercase input."""
        assert normalize_category_input("DSP") == "dsp"
        assert normalize_category_input("Dsp") == "dsp"

    def test_spaces_to_hyphens(self):
        """Should convert spaces to hyphens."""
        assert normalize_category_input("audio interface") == "audio-interface"
        assert normalize_category_input("Audio Interface") == "audio-interface"

    def test_underscores_to_hyphens(self):
        """Should convert underscores to hyphens."""
        assert normalize_category_input("audio_interface") == "audio-interface"

    def test_strip_whitespace(self):
        """Should strip leading/trailing whitespace."""
        assert normalize_category_input("  dsp  ") == "dsp"

    def test_already_normalized(self):
        """Should pass through already normalized input."""
        assert normalize_category_input("audio-interface") == "audio-interface"


class TestLoadSaveEntries:
    """Tests for load_entries and save_entries."""

    def test_load_empty_json(self, temp_json):
        """Should load empty list from empty JSON."""
        entries = load_entries(temp_json)
        assert entries == []

    def test_load_entries(self, populated_json):
        """Should load entries from JSON."""
        entries = load_entries(populated_json)
        assert len(entries) == 2
        assert entries[0]["name"] == "project-1"

    def test_save_entries(self, temp_json):
        """Should save entries to JSON."""
        entries = [
            {
                "name": "test",
                "category": "dsp",
                "desc": "Test",
                "repo": "https://github.com/t/t",
            }
        ]
        save_entries(entries, temp_json)

        with open(temp_json) as f:
            loaded = json.load(f)
        # New format: {categories: [], entries: []}
        assert len(loaded["entries"]) == 1
        assert loaded["entries"][0]["name"] == "test"

    def test_load_nonexistent_file(self, tmp_path):
        """Should return empty list for nonexistent file."""
        entries = load_entries(tmp_path / "nonexistent.json")
        assert entries == []


class TestAddEntry:
    """Tests for add_entry function."""

    def test_add_valid_entry(self, temp_json, temp_db):
        """Should add a valid entry and return it."""
        entry = add_entry(
            name="new-project",
            category="dsp",
            desc="A new project",
            repo="https://github.com/new/project",
            json_path=temp_json,
            db_path=temp_db,
        )
        assert entry["name"] == "new-project"
        assert entry["category"] == "dsp"

        entries = load_entries(temp_json)
        assert len(entries) == 1
        assert entries[0]["name"] == "new-project"

    def test_add_entry_syncs_to_db(self, temp_json, temp_db):
        """Should sync entry to database."""
        add_entry(
            name="synced-project",
            category="analysis",
            desc="Synced project",
            url="https://example.com",
            json_path=temp_json,
            db_path=temp_db,
        )

        conn = get_connection(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entry WHERE name = ?", ("synced-project",))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row["name"] == "synced-project"
        assert row["category"] == "analysis"

    def test_add_duplicate_raises_keyerror(self, populated_json, temp_db):
        """Should raise KeyError for duplicate entry names."""
        with pytest.raises(KeyError, match="already exists"):
            add_entry(
                name="project-1",
                category="dsp",
                desc="Duplicate",
                repo="https://github.com/d/d",
                json_path=populated_json,
                db_path=temp_db,
            )

    def test_add_without_url_or_repo_raises_valueerror(self, temp_json, temp_db):
        """Should raise ValueError when missing url and repo."""
        with pytest.raises(ValueError, match="url or repo"):
            add_entry(
                name="no-links",
                category="dsp",
                desc="No links",
                json_path=temp_json,
                db_path=temp_db,
            )

    def test_add_invalid_category_raises_valueerror(self, temp_json, temp_db):
        """Should raise ValueError for invalid categories."""
        with pytest.raises(ValueError, match="Unknown category"):
            add_entry(
                name="bad-category",
                category="invalid-category",
                desc="Bad category",
                repo="https://github.com/b/b",
                json_path=temp_json,
                db_path=temp_db,
            )

    def test_add_normalizes_category(self, temp_json, temp_db):
        """Should normalize category input."""
        entry = add_entry(
            name="normalized",
            category="Audio Interface",  # Not normalized
            desc="Test",
            repo="https://github.com/n/n",
            json_path=temp_json,
            db_path=temp_db,
        )
        assert entry["category"] == "audio-interface"  # Normalized

    def test_add_without_sync(self, temp_json, tmp_path):
        """Should add without syncing to DB when sync=False."""
        db_path = tmp_path / "nosync.db"

        add_entry(
            name="no-sync",
            category="dsp",
            desc="No sync",
            repo="https://github.com/n/n",
            json_path=temp_json,
            db_path=db_path,
            sync=False,
        )

        # Entry should be in JSON
        entries = load_entries(temp_json)
        assert len(entries) == 1

        # But not in DB (DB doesn't exist yet)
        assert not db_path.exists()


class TestRemoveEntry:
    """Tests for remove_entry function."""

    def test_remove_existing_entry(self, populated_json, temp_db):
        """Should remove an existing entry and return it."""
        # First sync to DB
        init_db(temp_db)
        from linkdb import import_from_json

        import_from_json(populated_json, temp_db)

        removed = remove_entry(
            name="project-1",
            json_path=populated_json,
            db_path=temp_db,
        )
        assert removed["name"] == "project-1"

        # Verify removed from JSON
        entries = load_entries(populated_json)
        assert len(entries) == 1
        assert entries[0]["name"] == "project-2"

        # Verify removed from DB
        conn = get_connection(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entry WHERE name = ?", ("project-1",))
        assert cursor.fetchone() is None
        conn.close()

    def test_remove_nonexistent_raises_keyerror(self, populated_json, temp_db):
        """Should raise KeyError for nonexistent entry."""
        with pytest.raises(KeyError, match="not found"):
            remove_entry(
                name="nonexistent",
                json_path=populated_json,
                db_path=temp_db,
            )


class TestUpdateEntry:
    """Tests for update_entry function."""

    def test_update_category(self, populated_json, temp_db):
        """Should update entry category and return updated entry."""
        updated = update_entry(
            name="project-1",
            category="synthesis",
            json_path=populated_json,
            db_path=temp_db,
        )
        assert updated["category"] == "synthesis"

        entry = get_entry("project-1", populated_json)
        assert entry["category"] == "synthesis"

    def test_update_description(self, populated_json, temp_db):
        """Should update entry description."""
        updated = update_entry(
            name="project-1",
            desc="Updated description",
            json_path=populated_json,
            db_path=temp_db,
        )
        assert updated["desc"] == "Updated description"

    def test_update_url(self, populated_json, temp_db):
        """Should update entry URL."""
        updated = update_entry(
            name="project-1",
            url="https://new-url.com",
            json_path=populated_json,
            db_path=temp_db,
        )
        assert updated["url"] == "https://new-url.com"

    def test_update_nonexistent_raises_keyerror(self, populated_json, temp_db):
        """Should raise KeyError for nonexistent entry."""
        with pytest.raises(KeyError, match="not found"):
            update_entry(
                name="nonexistent",
                category="dsp",
                json_path=populated_json,
                db_path=temp_db,
            )

    def test_update_invalid_category_raises_valueerror(self, populated_json, temp_db):
        """Should raise ValueError for invalid categories."""
        with pytest.raises(ValueError, match="Unknown category"):
            update_entry(
                name="project-1",
                category="invalid-category",
                json_path=populated_json,
                db_path=temp_db,
            )

    def test_update_normalizes_category(self, populated_json, temp_db):
        """Should normalize category input."""
        updated = update_entry(
            name="project-1",
            category="Audio Interface",  # Not normalized
            json_path=populated_json,
            db_path=temp_db,
        )
        assert updated["category"] == "audio-interface"  # Normalized

    def test_update_syncs_to_db(self, populated_json, temp_db):
        """Should sync updates to database."""
        # First import to DB
        init_db(temp_db)
        from linkdb import import_from_json

        import_from_json(populated_json, temp_db)

        update_entry(
            name="project-1",
            desc="Synced update",
            json_path=populated_json,
            db_path=temp_db,
        )

        conn = get_connection(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT description FROM entry WHERE name = ?", ("project-1",))
        row = cursor.fetchone()
        conn.close()

        assert row["description"] == "Synced update"


class TestGetEntry:
    """Tests for get_entry function."""

    def test_get_existing_entry(self, populated_json):
        """Should return existing entry."""
        entry = get_entry("project-1", populated_json)
        assert entry is not None
        assert entry["name"] == "project-1"
        assert entry["category"] == "dsp"

    def test_get_nonexistent_entry(self, populated_json):
        """Should return None for nonexistent entry."""
        entry = get_entry("nonexistent", populated_json)
        assert entry is None


class TestSortEntriesFile:
    """Tests for sort_entries_file function."""

    @pytest.fixture
    def unsorted_json(self):
        """Create a JSON file with unsorted categories and entries."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            data = {
                "categories": ["synthesis", "analysis", "dsp", "midi"],
                "entries": [
                    {
                        "name": "Zebra",
                        "category": "synthesis",
                        "desc": "Z synth",
                        "repo": "https://github.com/z/z",
                    },
                    {
                        "name": "Alpha",
                        "category": "dsp",
                        "desc": "A dsp",
                        "repo": "https://github.com/a/a",
                    },
                    {
                        "name": "Beta",
                        "category": "analysis",
                        "desc": "B analyzer",
                        "repo": "https://github.com/b/b",
                    },
                    {
                        "name": "Gamma",
                        "category": "dsp",
                        "desc": "G dsp",
                        "repo": "https://github.com/g/g",
                    },
                ],
            }
            json.dump(data, f)
            return Path(f.name)

    def test_sort_categories_alphabetically(self, unsorted_json):
        """Should sort categories in ascending alphabetical order."""
        sort_entries_file(unsorted_json)
        data = load_data(unsorted_json)
        assert data["categories"] == ["analysis", "dsp", "midi", "synthesis"]

    def test_sort_entries_by_name(self, unsorted_json):
        """Should sort entries by name in ascending order (default)."""
        sort_entries_file(unsorted_json)
        data = load_data(unsorted_json)
        names = [e["name"] for e in data["entries"]]
        assert names == ["Alpha", "Beta", "Gamma", "Zebra"]

    def test_sort_entries_by_category_then_name(self, unsorted_json):
        """Should sort entries by category first, then by name when by_category=True."""
        sort_entries_file(unsorted_json, by_category=True)
        data = load_data(unsorted_json)
        entries = [(e["category"], e["name"]) for e in data["entries"]]
        assert entries == [
            ("analysis", "Beta"),
            ("dsp", "Alpha"),
            ("dsp", "Gamma"),
            ("synthesis", "Zebra"),
        ]

    def test_sort_returns_counts(self, unsorted_json):
        """Should return counts of sorted categories and entries."""
        num_cats, num_entries = sort_entries_file(unsorted_json)
        assert num_cats == 4
        assert num_entries == 4

    def test_sort_case_insensitive(self):
        """Should sort case-insensitively."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            data = {
                "categories": ["Zebra", "alpha", "Beta"],
                "entries": [
                    {
                        "name": "zebra",
                        "category": "dsp",
                        "desc": "z",
                        "repo": "https://github.com/z/z",
                    },
                    {
                        "name": "ALPHA",
                        "category": "dsp",
                        "desc": "a",
                        "repo": "https://github.com/a/a",
                    },
                    {
                        "name": "Beta",
                        "category": "dsp",
                        "desc": "b",
                        "repo": "https://github.com/b/b",
                    },
                ],
            }
            json.dump(data, f)
            json_path = Path(f.name)

        sort_entries_file(json_path)
        data = load_data(json_path)

        assert data["categories"] == ["alpha", "Beta", "Zebra"]
        names = [e["name"] for e in data["entries"]]
        assert names == ["ALPHA", "Beta", "zebra"]
