"""Tests for README generator."""

import tempfile
from pathlib import Path


from linkdb import category_anchor, generate_readme, init_db, normalize_category


class TestNormalizeCategory:
    """Tests for normalize_category function."""

    def test_simple_category(self):
        """Should capitalize simple category."""
        assert normalize_category("dsp") == "Dsp"

    def test_hyphenated_category(self):
        """Should handle hyphenated categories."""
        assert normalize_category("audio-interface") == "Audio Interface"

    def test_multi_word_category(self):
        """Should handle multi-word categories."""
        assert (
            normalize_category("music programming language")
            == "Music Programming Language"
        )


class TestCategoryAnchor:
    """Tests for category_anchor function."""

    def test_simple_anchor(self):
        """Should generate simple anchor."""
        assert category_anchor("DSP") == "dsp"

    def test_space_to_hyphen(self):
        """Should convert spaces to hyphens."""
        assert category_anchor("Audio Interface") == "audio-interface"


class TestGenerateReadme:
    """Tests for generate_readme function."""

    def test_generate_from_empty_db(self):
        """Should handle empty database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            init_db(db_path)
            content = generate_readme(db_path)
            assert "No entries yet" in content
        finally:
            db_path.unlink(missing_ok=True)

    def test_generate_with_entries(self):
        """Should generate README with entries."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            conn = init_db(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO entry (name, category, description, repo) VALUES (?, ?, ?, ?)",
                (
                    "test-project",
                    "dsp",
                    "A test project",
                    "https://github.com/test/test",
                ),
            )
            cursor.execute(
                "INSERT INTO entry (name, category, description, url) VALUES (?, ?, ?, ?)",
                (
                    "another-project",
                    "analysis",
                    "Another project",
                    "https://example.com",
                ),
            )
            conn.commit()
            conn.close()

            content = generate_readme(db_path)

            assert "test-project" in content
            assert "another-project" in content
            assert "A test project" in content
            assert "2 projects" in content or "**2**" in content
        finally:
            db_path.unlink(missing_ok=True)

    def test_generate_to_file(self):
        """Should write to output file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            output_path = Path(f.name)

        try:
            conn = init_db(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO entry (name, category, description, repo) VALUES (?, ?, ?, ?)",
                ("test", "dsp", "Test", "https://github.com/test/test"),
            )
            conn.commit()
            conn.close()

            generate_readme(db_path, output_path=output_path, force=True)

            assert output_path.exists()
            content = output_path.read_text()
            assert "test" in content
        finally:
            db_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)

    def test_entries_grouped_by_category(self):
        """Should group entries by category."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            conn = init_db(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO entry (name, category, description, repo) VALUES (?, ?, ?, ?)",
                ("dsp1", "dsp", "DSP 1", "https://github.com/a/a"),
            )
            cursor.execute(
                "INSERT INTO entry (name, category, description, repo) VALUES (?, ?, ?, ?)",
                ("dsp2", "dsp", "DSP 2", "https://github.com/b/b"),
            )
            cursor.execute(
                "INSERT INTO entry (name, category, description, repo) VALUES (?, ?, ?, ?)",
                ("analysis1", "analysis", "Analysis 1", "https://github.com/c/c"),
            )
            conn.commit()
            conn.close()

            content = generate_readme(db_path)

            # Both DSP entries should appear together
            assert "## Dsp" in content
            assert "## Analysis" in content
        finally:
            db_path.unlink(missing_ok=True)
