# linkdb - terminal-first bookmarking.

linkdb is a simple, zero-dependency CLI tool for collecting and managing interesting project links (like "awesome" lists).

It lets you build a personal database of project URLs you want to remember and organize them locally with search, tags, and export tools.

Designed for people who enjoy discovering things on the internet and keeping track of what matters.

It consists of a single-file Python script using only the standard library. Python 3.8+.

## Installation

```sh
pip install linkdb
```

or

```bash
# Clone and install
git clone https://github.com/user/linkdb.git
cd linkdb
uv sync

# Or just run directly
./linkdb.py --help
```

## Quick Start

```bash
# Check data health
linkdb doctor

# Import to database
linkdb import

# List entries
linkdb list

# List with filters
linkdb list --stars-min 100 --language python --active-only

# Search
linkdb search synthesizer

# Add a new entry (auto-fetches GitHub metadata)
linkdb add -r "https://github.com/user/my-project" -c synthesis

# Add interactively
linkdb add -i

# Add multiple entries from file
linkdb add --file urls.txt -c synthesis

# Update an entry
linkdb update my-project -d "An awesome synth"

# Remove an entry
linkdb remove my-project

# Remove all entries in a category
linkdb remove --category obsolete-category

# Sort entries.json
linkdb sort
linkdb sort --by-category

# Generate README
linkdb generate -o README.md

# Create backup
linkdb backup create

# View change history
linkdb history
linkdb history my-project
```

## CLI Commands Reference

| Command | Description |
|---------|-------------|
| `add` | Add entry (supports `--file` for batch, `-i` for interactive) |
| `add-link` | Add a link to an entry |
| `backup create` | Create a backup of JSON and database |
| `backup restore` | Restore from a backup |
| `backup list` | List available backups |
| `category list` | List all categories |
| `category add` | Add a new category |
| `category rm` | Remove a category |
| `check` | Validate URLs for broken links |
| `dedupe` | Find and merge duplicate entries |
| `doctor` | Check data integrity and health |
| `export` | Export database to JSON |
| `generate` | Generate README from database |
| `github fetch` | Fetch GitHub repository stats |
| `github stale` | Find unmaintained projects |
| `github cache` | Manage GitHub API cache |
| `history` | Show change history (optional entry filter) |
| `import` | Import JSON to database (supports `--webloc` for .webloc files) |
| `list` | List entries with filters |
| `list-links` | List links for an entry or all entries |
| `remove` | Remove entry (supports `--category` for bulk removal) |
| `remove-link` | Remove a link from an entry |
| `search` | Search entries |
| `sort` | Sort entries.json file |
| `stats` | Show database statistics |
| `update` | Update an existing entry |

### GitHub Subcommands

```bash
linkdb github fetch          # Fetch stats for all repos
linkdb github fetch --no-cache  # Bypass cache
linkdb github stale          # Find unmaintained projects
linkdb github cache stats    # Show cache statistics
linkdb github cache clear    # Clear expired cache entries
```

### Backup Subcommands

```bash
linkdb backup create         # Create new backup
linkdb backup list           # List available backups
linkdb backup restore <file> # Restore from backup
```

### Link Commands

Associate relevant links (articles, tutorials, videos) with entries:

```bash
# Add a link to an entry
linkdb add-link my-project https://example.com/article -t "Getting Started" --type article

# Add with note
linkdb add-link my-project https://youtube.com/watch?v=xyz -t "Tutorial" --type video -n "Great intro"

# List links for an entry
linkdb list-links my-project

# List all links (JSON format)
linkdb list-links -f json

# Remove a link
linkdb remove-link my-project https://example.com/article
```

Valid link types: `article`, `tutorial`, `video`, `docs`, `discussion`

## Global Options

```bash
-v, --verbose    # Increase verbosity (use -vv for debug)
-q, --quiet      # Suppress non-error output
--version        # Show version
```

## Environment Variables

```bash
LINKDB_JSON      # Override default entries.json path
LINKDB_DB        # Override default database path
GITHUB_TOKEN     # GitHub API token for higher rate limits
```

## Data Format

Entries are stored in `data/entries.json`:

```json
{
  "categories": ["synthesis", "dsp", "midi"],
  "entries": [
    {
      "name": "project-name",
      "category": "synthesis",
      "desc": "Project description",
      "url": "https://example.com",
      "repo": "https://github.com/user/project",
      "links": [
        {
          "url": "https://example.com/tutorial",
          "title": "Getting Started Guide",
          "link_type": "tutorial",
          "note": "Great introduction"
        }
      ]
    }
  ]
}
```

Each entry must have:
- `name` - unique project name
- `category` - from defined categories list
- `desc` - description
- `url` and/or `repo` - at least one link

Optional fields:
- `links` - array of related links (articles, tutorials, videos, docs, discussions)
- `tags` - comma-separated tags
- `aliases` - alternative names
- `mirror_urls` - additional URLs

## Programmatic API

```python
from linkdb import (
    add_entry, update_entry, remove_entry, get_entry,
    sort_entries_file, find_duplicates, create_backup
)

# Add entry (returns entry dict, raises ValueError/KeyError on error)
entry = add_entry("my-project", "dsp", "Description",
                  repo="https://github.com/...")

# Add from GitHub URL (auto-fetches metadata)
from linkdb import add_entry_from_github
entry = add_entry_from_github("https://github.com/user/repo", "dsp")

# Update entry
entry = update_entry("my-project", desc="New description")

# Get entry (returns dict or None)
entry = get_entry("my-project")

# Remove entry
entry = remove_entry("my-project")

# Sort entries file
sort_entries_file()                      # Sort by name
sort_entries_file(by_category=True)      # Sort by category, then name

# Find duplicates
duplicates = find_duplicates()

# Create backup
backup_path = create_backup()
```

## Development

```bash
# Install dev dependencies
uv sync

# Run tests
make test

# Run full QA (test + lint + typecheck + format)
make qa

# Lint only
make lint

# Type check
make typecheck
```

## License

MIT
