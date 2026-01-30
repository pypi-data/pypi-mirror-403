# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1]

### Added

- **Links feature**: Associate relevant links (articles, tutorials, videos, etc.) with entries
  - New `link` table with foreign key to entry (cascade delete)
  - `Link` dataclass with `url`, `title`, `link_type`, `note` fields
  - Valid link types: `article`, `tutorial`, `video`, `docs`, `discussion`
  - Links are imported/exported with entries in JSON
  - README generation includes "Relevant Links" subsection
  - New CLI commands:
    - `add-link <entry> <url>`: Add link with optional `-t/--title`, `--type`, `-n/--note`
    - `remove-link <entry> <url>`: Remove a link from an entry
    - `list-links [entry]`: List links (optional entry filter, `-f json` for JSON output)
  - 25 new tests covering all link functionality

- **Logging infrastructure**: Proper logging via Python's `logging` module
  - `logger` instance available throughout codebase
  - `setup_logging()` configures based on verbosity level

- **Verbose/Quiet flags**: Global CLI flags for output control
  - `-v/--verbose`: Increase verbosity (use `-vv` for debug)
  - `-q/--quiet`: Suppress non-error output

- **Confirmation helper**: `confirm()` function for consistent user prompts
  - Handles keyboard interrupts gracefully
  - Configurable default values

- **Entry aliases/tags**: Extended data model with new fields
  - `tags`: Comma-separated tags (distinct from category)
  - `aliases`: Alternative names for entries
  - `mirror_urls`: Multiple URLs per entry
  - Database auto-migrates to add new columns

- **`doctor` command**: Comprehensive data health checks
  - JSON syntax validation
  - Required fields check
  - Missing descriptions detection
  - Duplicate URLs/names detection
  - Database schema verification
  - Repository check freshness (30+ days warning)
  - Category consistency validation
  - Replaces the `validate` command

- **GitHub API caching with TTL**: Reduces API calls and handles rate limits
  - 24-hour default cache TTL (configurable)
  - `github_cache` SQLite table stores responses
  - `--no-cache` flag to bypass cache
  - `github cache stats` shows cache statistics
  - `github cache clear` removes expired/all entries

- **Exponential backoff**: Automatic retry on GitHub API rate limiting (403)
  - Respects `Retry-After` header
  - Random jitter prevents thundering herd
  - Maximum 3 retries with 60s cap

- **Batch operations**:
  - `add --file <path>`: Add multiple entries from file (one URL per line)
  - `remove --category <name>`: Remove all entries in a category

- **Dry-run mode**: Preview destructive operations without making changes
  - `--dry-run` flag on `add`, `remove`, `import`, `backup restore`

- **Interactive mode**: Guided entry creation
  - `add -i/--interactive`: Prompts for all fields with validation

- **Entry deduplication**: `dedupe` command finds entries with same URL/repo
  - Groups duplicates and identifies primary entry
  - `--merge` auto-merges without prompting
  - `--dry-run` shows duplicates without merging

- **List filtering**: Enhanced `list` command options
  - `--stars-min N`: Filter by minimum GitHub stars
  - `--language LANG`: Filter by programming language
  - `--active-only`: Exclude archived/stale repos

- **Backup/Restore**: Full data backup functionality
  - `backup create`: Creates timestamped .tar.gz archive
  - `backup restore`: Restores from archive (with confirmation)
  - `backup list`: Shows available backups

- **History tracking**: Change audit trail
  - `history` command shows all changes
  - `history <entry>` shows changes for specific entry
  - `--since DATE` filters by date
  - `--action` filters by action type (add/remove/update)
  - `--details` shows full change details

- **Environment variable configuration**: Override default paths
  - `CURATOR_JSON`: Override default entries.json path
  - `CURATOR_DB`: Override default database path

### Changed

- **`export` command**: Enhanced to preserve data structure
  - `--source-json`: Preserve categories from source JSON file
  - `--include-github`: Include GitHub metadata (stars, forks, language, etc.)
  - Exports full JSON structure with `categories` and `entries` keys
  - Includes new fields (tags, aliases, mirror_urls) when present

- **CLI consolidation**: Reduced from 24 to 17 commands
  - `validate` removed (use `doctor`)
  - `stale` moved to `github stale`
  - `cache` moved to `github cache`
  - `add-many` merged into `add --file`
  - `remove-category` merged into `remove --category`
  - `scan-webloc` merged into `import --webloc`
  - `restore` moved to `backup restore`
  - `diff` merged into `history`

- **`import` command**: Now supports webloc files
  - `--webloc DIR`: Import from .webloc files in directory
  - `-r/--recursive`: Scan subdirectories
  - `-c/--category`: Required for webloc import

- **`import --update`**: Now prompts for confirmation
  - `-y/--yes` skips confirmation

- **SSL verification**: Now opt-in insecure mode
  - `--insecure` flag on `check` command
  - Default is secure (certificate verification enabled)

- **Version strings**: Standardized User-Agent to use `__version__`

- **Database connections**: All use context managers (no leaks)

- **Progress callbacks**: Null-object pattern (simplified code)

### Fixed

- Connection leaks on database exceptions
- Duplicate code in URL checking
- Inconsistent error handling patterns

### Removed

- `validate` command (use `doctor` instead)
- `stale` top-level command (use `github stale`)
- `cache` top-level command (use `github cache`)
- `add-many` command (use `add --file`)
- `remove-category` command (use `remove --category`)
- `scan-webloc` command (use `import --webloc`)
- `restore` top-level command (use `backup restore`)
- `diff` command (use `history`)

## [0.1.0] - 2026-01-25

### Added

- **Single-file architecture**: Entire tool consolidated into `linkdb.py`
- **Zero external dependencies**: Uses only Python standard library
- **Python 3.8+ support**

- **CLI tool** (`linkdb`) with commands:
  - `validate` - Validate entries JSON file with strict category checking
  - `import` - Import entries from JSON to SQLite database
  - `export` - Export entries from database to JSON
  - `list` - List entries with optional category filter and format options
  - `search` - Search entries by name, description, or category
  - `stats` - Show database statistics including category breakdown
  - `category list` - List all categories from JSON file
  - `category add NAME` - Add a new category
  - `category rm NAME` - Remove a category (with `--force` if in use)
  - `add` - Add new entry to JSON file with automatic database sync
  - `remove` - Remove entry from JSON file and database
  - `update` - Update existing entry in JSON file with database sync
  - `check` - Check all URLs for broken links (concurrent)
  - `github` - Fetch GitHub repository statistics
  - `stale` - Find unmaintained/archived projects
  - `generate` - Generate README.md from database

- **Entry API** for programmatic access:
  - `add_entry()` - Add entry to JSON, validate, sync to database
  - `remove_entry()` - Remove entry from JSON and database
  - `update_entry()` - Update entry in JSON, validate, sync to database
  - `get_entry()` - Get entry by name from JSON
  - `load_entries()` / `save_entries()` - Low-level JSON I/O
  - `load_categories()` / `save_categories()` - Category management
  - `sync_to_db()` - Sync JSON to database

- **Dynamic categories**: Stored in JSON file, manageable via CLI/API
- **Schema validation**: Duplicate detection, URL/repo requirement
- **Link checker**: Concurrent URL validation
- **GitHub API integration**: Stats, activity status, authentication
- **README generation**: Template-based with TOC
- **Database** (SQLite): Entry storage with unique names
- **Testing**: 137 pytest tests
- **Build system**: Makefile + pyproject.toml

### Technical Details

Standard library replacements:
- `argparse` instead of click
- `sqlite3` instead of SQLAlchemy
- `urllib.request` + `ThreadPoolExecutor` instead of httpx async
- `string.Template` instead of Jinja2
- `json` instead of pyyaml
- Manual validation instead of Pydantic
