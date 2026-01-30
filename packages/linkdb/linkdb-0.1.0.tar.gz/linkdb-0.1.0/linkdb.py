#!/usr/bin/env python3
"""
linkdb: A zero-dependency CLI tool for managing curated project lists.

Zero external dependencies - stdlib only.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import plistlib
import random
import re
import shutil
import sqlite3
import ssl
import tarfile
import time
import urllib.error
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from string import Template
from typing import Any, Callable, Optional

# -----------------------------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------------------------

logger = logging.getLogger("linkdb")


def setup_logging(verbose: int = 0, quiet: bool = False) -> None:
    """Configure logging based on verbosity level.

    Args:
        verbose: Verbosity level (0=normal, 1=info, 2+=debug)
        quiet: If True, suppress all non-error output
    """
    if quiet:
        level = logging.ERROR
    elif verbose >= 2:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(level)


__version__ = "0.1.0"

# Type alias for progress callbacks
ProgressCallback = Callable[[int, int, str], None]


def _noop_progress(_current: int, _total: int, _name: str) -> None:
    """Null-object progress callback that does nothing."""
    pass


# =============================================================================
# Configuration
# =============================================================================

# Auto-detect project root: if linkdb.py is in scripts/, go up one level
_SCRIPT_DIR = Path(__file__).parent
_PROJECT_ROOT = _SCRIPT_DIR.parent if _SCRIPT_DIR.name == "scripts" else _SCRIPT_DIR

# Default paths can be overridden via environment variables
DEFAULT_JSON = Path(
    os.environ.get("CURATOR_JSON", _PROJECT_ROOT / "data" / "entries.json")
)
DEFAULT_DB = Path(os.environ.get("CURATOR_DB", _PROJECT_ROOT / "data" / "linkdb.db"))


def load_data(json_path: Optional[Path] = None) -> dict[str, Any]:
    """Load the full data structure (categories + entries) from JSON."""
    path = json_path or DEFAULT_JSON
    if not path.exists():
        return {"categories": [], "entries": []}
    with open(path) as f:
        data: dict[str, Any] = json.load(f)
    # Handle legacy format (just a list of entries)
    if isinstance(data, list):
        return {"categories": [], "entries": data}
    return data


def save_data(data: dict[str, Any], json_path: Optional[Path] = None) -> None:
    """Save the full data structure to JSON."""
    path = json_path or DEFAULT_JSON
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def load_categories(json_path: Optional[Path] = None) -> set[str]:
    """Load categories from JSON file."""
    data = load_data(json_path)
    return set(data.get("categories", []))


def save_categories(categories: set[str], json_path: Optional[Path] = None) -> None:
    """Save categories to JSON file."""
    data = load_data(json_path)
    data["categories"] = sorted(categories)
    save_data(data, json_path)


def sort_entries_file(
    json_path: Optional[Path] = None, by_category: bool = False
) -> tuple[int, int]:
    """Sort entries.json file: categories alphabetically, entries by name or category+name.

    Args:
        json_path: Path to JSON file (defaults to DEFAULT_JSON)
        by_category: If True, sort entries by category first, then by name.
                     If False, sort entries by name only.

    Returns:
        Tuple of (num_categories, num_entries) sorted.
    """
    data = load_data(json_path)

    # Sort categories alphabetically
    categories = data.get("categories", [])
    data["categories"] = sorted(categories, key=str.lower)

    # Sort entries
    entries = data.get("entries", [])
    if by_category:
        data["entries"] = sorted(
            entries,
            key=lambda e: (e.get("category", "").lower(), e.get("name", "").lower()),
        )
    else:
        data["entries"] = sorted(entries, key=lambda e: e.get("name", "").lower())

    save_data(data, json_path)
    return len(data["categories"]), len(data["entries"])


# =============================================================================
# Database (sqlite3)
# =============================================================================

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS entry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    url TEXT,
    repo TEXT,
    description TEXT NOT NULL,
    keywords TEXT,
    last_updated DATE,
    last_checked DATE,
    stars INTEGER,
    forks INTEGER,
    language TEXT,
    license TEXT,
    archived BOOLEAN DEFAULT 0,
    last_pushed DATE
)
"""

HISTORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    action TEXT NOT NULL,
    entry_name TEXT NOT NULL,
    category TEXT,
    details TEXT
)
"""

GITHUB_CACHE_SCHEMA = """
CREATE TABLE IF NOT EXISTS github_cache (
    repo_key TEXT PRIMARY KEY,
    data TEXT NOT NULL,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL
)
"""

# Default cache TTL: 24 hours
GITHUB_CACHE_TTL_HOURS = 24

# Columns added in schema migration
_MIGRATION_COLUMNS = [
    ("stars", "INTEGER"),
    ("forks", "INTEGER"),
    ("language", "TEXT"),
    ("license", "TEXT"),
    ("archived", "BOOLEAN DEFAULT 0"),
    ("last_pushed", "DATE"),
    ("tags", "TEXT"),  # Comma-separated tags (distinct from category)
    ("aliases", "TEXT"),  # Comma-separated alternative names
    ("mirror_urls", "TEXT"),  # Comma-separated mirror URLs
]


def init_db(db_path: Path) -> sqlite3.Connection:
    """Initialize database and return connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(DB_SCHEMA)
    conn.execute(HISTORY_SCHEMA)
    conn.execute(GITHUB_CACHE_SCHEMA)
    conn.commit()
    _migrate_db(conn)
    return conn


def _migrate_db(conn: sqlite3.Connection) -> None:
    """Add missing columns to existing database tables."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(entry)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    for col_name, col_type in _MIGRATION_COLUMNS:
        if col_name not in existing_columns:
            cursor.execute(f"ALTER TABLE entry ADD COLUMN {col_name} {col_type}")

    # Ensure history table exists
    cursor.execute(HISTORY_SCHEMA)
    conn.commit()


def record_history(
    conn: sqlite3.Connection,
    action: str,
    entry_name: str,
    category: Optional[str] = None,
    details: Optional[str] = None,
) -> None:
    """Record an action in the history table."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO history (action, entry_name, category, details) VALUES (?, ?, ?, ?)",
        (action, entry_name, category, details),
    )
    conn.commit()


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Get database connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


@dataclass
class Entry:
    """Database entry."""

    id: Optional[int]
    name: str
    category: str
    url: Optional[str]
    repo: Optional[str]
    description: str
    keywords: Optional[str] = None
    last_updated: Optional[str] = None
    last_checked: Optional[str] = None
    stars: Optional[int] = None
    forks: Optional[int] = None
    language: Optional[str] = None
    license: Optional[str] = None
    archived: Optional[bool] = None
    last_pushed: Optional[str] = None
    tags: Optional[str] = None  # Comma-separated tags
    aliases: Optional[str] = None  # Comma-separated alternative names
    mirror_urls: Optional[str] = None  # Comma-separated mirror URLs

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Entry:
        keys = row.keys()
        return cls(
            id=row["id"],
            name=row["name"],
            category=row["category"],
            url=row["url"],
            repo=row["repo"],
            description=row["description"],
            keywords=row["keywords"],
            last_updated=row["last_updated"],
            last_checked=row["last_checked"],
            stars=row["stars"] if "stars" in keys else None,
            forks=row["forks"] if "forks" in keys else None,
            language=row["language"] if "language" in keys else None,
            license=row["license"] if "license" in keys else None,
            archived=bool(row["archived"])
            if "archived" in keys and row["archived"] is not None
            else None,
            last_pushed=row["last_pushed"] if "last_pushed" in keys else None,
            tags=row["tags"] if "tags" in keys else None,
            aliases=row["aliases"] if "aliases" in keys else None,
            mirror_urls=row["mirror_urls"] if "mirror_urls" in keys else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "url": self.url,
            "repo": self.repo,
            "description": self.description,
            "keywords": self.keywords,
            "last_updated": self.last_updated,
            "last_checked": self.last_checked,
            "stars": self.stars,
            "forks": self.forks,
            "language": self.language,
            "license": self.license,
            "archived": self.archived,
            "last_pushed": self.last_pushed,
            "tags": self.tags,
            "aliases": self.aliases,
            "mirror_urls": self.mirror_urls,
        }


# =============================================================================
# Category Helpers
# =============================================================================


def normalize_category_input(category: str) -> str:
    """Normalize user input to canonical category format (lowercase, hyphenated)."""
    return category.strip().lower().replace(" ", "-").replace("_", "-")


# =============================================================================
# Schema Validation
# =============================================================================


@dataclass
class ValidationResult:
    """Result of validating entries."""

    valid: list[dict[str, Any]] = field(default_factory=list)
    errors: list[tuple[int, dict[str, Any], str]] = field(default_factory=list)
    warnings: list[tuple[int, dict[str, Any], str]] = field(default_factory=list)
    duplicates: list[tuple[str, list[int]]] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        return "\n".join(
            [
                f"Valid entries: {len(self.valid)}",
                f"Errors: {len(self.errors)}",
                f"Warnings: {len(self.warnings)}",
                f"Duplicates: {len(self.duplicates)}",
            ]
        )


def validate_entry(entry: dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate a single entry. Returns (is_valid, error_message)."""
    name = entry.get("name", "")

    if not name or not str(name).strip():
        return False, "name cannot be empty"

    name = str(name).strip()
    if name.startswith("http://") or name.startswith("https://"):
        return False, f"name should not be a URL: {name}"

    desc = entry.get("desc", "")
    if not desc or not str(desc).strip():
        return False, "desc cannot be empty"

    url = entry.get("url")
    repo = entry.get("repo")
    if not url and not repo:
        return False, f"entry '{name}' must have url or repo"

    return True, None


def validate_entries(
    entries: list[dict[str, Any]],
    strict_categories: bool = True,
    json_path: Optional[Path] = None,
) -> ValidationResult:
    """Validate a list of entry dictionaries.

    Args:
        entries: List of entry dictionaries to validate
        strict_categories: If True, invalid categories are errors; if False, warnings
        json_path: Path to JSON file (for loading categories)
    """
    result = ValidationResult()
    seen_names: dict[str, list[int]] = {}
    categories = load_categories(json_path)

    for idx, entry in enumerate(entries):
        name = entry.get("name", "")

        if name:
            if name not in seen_names:
                seen_names[name] = []
            seen_names[name].append(idx + 1)

        is_valid, error = validate_entry(entry)
        if not is_valid:
            result.errors.append((idx + 1, entry, error or "Unknown error"))
            continue

        # Check category
        category = entry.get("category", "")
        normalized_cat = normalize_category_input(category)
        if normalized_cat not in categories:
            msg = f"invalid category: '{category}'"
            if strict_categories:
                result.errors.append((idx + 1, entry, msg))
            else:
                result.warnings.append((idx + 1, entry, msg))
                result.valid.append(entry)
        else:
            # Warn if category is not in canonical format
            if category != normalized_cat:
                msg = f"category '{category}' should be '{normalized_cat}'"
                result.warnings.append((idx + 1, entry, msg))
            result.valid.append(entry)

    for name, indices in seen_names.items():
        if len(indices) > 1:
            result.duplicates.append((name, indices))

    return result


def load_and_validate(path: Path) -> ValidationResult:
    """Load a JSON file and validate its entries."""
    entries = load_entries(path)
    return validate_entries(entries, json_path=path)


# =============================================================================
# Import/Export
# =============================================================================


def import_from_json(
    json_path: Path,
    db_path: Path,
    skip_duplicates: bool = True,
    dry_run: bool = False,
) -> tuple[int, int, list[str]]:
    """Import entries from JSON to database.

    Args:
        json_path: Path to JSON file
        db_path: Path to database
        skip_duplicates: If True, skip existing entries; if False, update them
        dry_run: If True, report what would happen without making changes

    Returns:
        Tuple of (imported/would_import, skipped, errors)
    """
    raw_entries = load_entries(json_path)

    result = validate_entries(raw_entries, json_path=json_path)
    if not result.is_valid:
        validation_errors = [
            f"{entry.get('name', 'UNKNOWN')}: {err}" for _, entry, err in result.errors
        ]
        return 0, 0, validation_errors

    imported = 0
    skipped = 0
    errors: list[str] = []
    processed_names: set[str] = set()

    with init_db(db_path) as conn:
        cursor = conn.cursor()

        for entry in result.valid:
            name = entry["name"]
            if name in processed_names:
                skipped += 1
                continue
            processed_names.add(name)

            cursor.execute("SELECT id FROM entry WHERE name = ?", (name,))
            existing = cursor.fetchone()

            if existing:
                if skip_duplicates:
                    skipped += 1
                else:
                    if not dry_run:
                        cursor.execute(
                            """UPDATE entry SET category=?, url=?, repo=?, description=?
                               WHERE name=?""",
                            (
                                entry["category"],
                                entry.get("url"),
                                entry.get("repo"),
                                entry["desc"],
                                name,
                            ),
                        )
                    imported += 1
            else:
                if not dry_run:
                    cursor.execute(
                        """INSERT INTO entry (name, category, url, repo, description)
                           VALUES (?, ?, ?, ?, ?)""",
                        (
                            name,
                            entry["category"],
                            entry.get("url"),
                            entry.get("repo"),
                            entry["desc"],
                        ),
                    )
                imported += 1

        if not dry_run:
            conn.commit()

    return imported, skipped, errors


def export_to_json(
    db_path: Path,
    output_path: Path,
    source_json: Optional[Path] = None,
    include_github_metadata: bool = False,
) -> int:
    """Export entries from database to JSON.

    Args:
        db_path: Path to SQLite database
        output_path: Path to write JSON output
        source_json: If provided, preserve categories from this JSON file
        include_github_metadata: If True, include stars, forks, language, etc.

    Returns:
        Number of entries exported
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entry ORDER BY name")
        rows = cursor.fetchall()

    # Preserve categories from source JSON if available
    categories: list[str] = []
    if source_json and source_json.exists():
        source_data = load_data(source_json)
        categories = source_data.get("categories", [])
    else:
        # Extract unique categories from entries
        categories = sorted(set(row["category"] for row in rows if row["category"]))

    json_entries = []
    for row in rows:
        entry: dict[str, Any] = {
            "name": row["name"],
            "category": row["category"],
            "desc": row["description"],
        }

        # Include url and repo only if present
        if row["url"]:
            entry["url"] = row["url"]
        if row["repo"]:
            entry["repo"] = row["repo"]

        # Include new fields if present
        if row["tags"]:
            entry["tags"] = row["tags"]
        if row["aliases"]:
            entry["aliases"] = row["aliases"]
        if row["mirror_urls"]:
            entry["mirror_urls"] = row["mirror_urls"]

        # Include GitHub metadata if requested
        if include_github_metadata:
            if row["stars"] is not None:
                entry["stars"] = row["stars"]
            if row["forks"] is not None:
                entry["forks"] = row["forks"]
            if row["language"]:
                entry["language"] = row["language"]
            if row["license"]:
                entry["license"] = row["license"]
            if row["archived"]:
                entry["archived"] = bool(row["archived"])
            if row["last_pushed"]:
                entry["last_pushed"] = row["last_pushed"]

        json_entries.append(entry)

    # Build full data structure with categories
    output_data = {
        "categories": categories,
        "entries": json_entries,
    }

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)
        f.write("\n")  # Trailing newline for POSIX compliance

    return len(json_entries)


# =============================================================================
# Link Checker (using urllib + ThreadPoolExecutor)
# =============================================================================


class LinkStatus(Enum):
    """Status of a checked link."""

    OK = "ok"
    REDIRECT = "redirect"
    NOT_FOUND = "not_found"
    TIMEOUT = "timeout"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class LinkResult:
    """Result of checking a single link."""

    url: str
    status: LinkStatus
    status_code: Optional[int] = None
    redirect_url: Optional[str] = None
    error_message: Optional[str] = None
    response_time_ms: Optional[float] = None


@dataclass
class CheckResult:
    """Result of checking all links for an entry."""

    entry_name: str
    url_result: Optional[LinkResult] = None
    repo_result: Optional[LinkResult] = None
    checked_at: datetime = field(default_factory=datetime.now)

    @property
    def has_issues(self) -> bool:
        for result in [self.url_result, self.repo_result]:
            if result and result.status not in (
                LinkStatus.OK,
                LinkStatus.REDIRECT,
                LinkStatus.SKIPPED,
            ):
                return True
        return False


def _get_ssl_context(insecure: bool = False) -> ssl.SSLContext:
    """Get SSL context for HTTP requests.

    Args:
        insecure: If True, disable certificate verification (not recommended).
    """
    ctx = ssl.create_default_context()
    if insecure:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _make_link_result(
    url: str,
    response: urllib.response.addinfourl,
    elapsed_ms: float,
) -> LinkResult:
    """Create LinkResult from a successful HTTP response."""
    final_url = response.geturl()
    if final_url != url:
        return LinkResult(
            url=url,
            status=LinkStatus.REDIRECT,
            status_code=response.status,
            redirect_url=final_url,
            response_time_ms=elapsed_ms,
        )
    return LinkResult(
        url=url,
        status=LinkStatus.OK,
        status_code=response.status,
        response_time_ms=elapsed_ms,
    )


def _fetch_url(
    url: str,
    timeout: float,
    ssl_context: ssl.SSLContext,
    method: Optional[str] = "HEAD",
) -> urllib.response.addinfourl:
    """Fetch URL and return response. Caller must close response."""
    req = urllib.request.Request(
        url,
        method=method,
        headers={"User-Agent": f"linkdb/{__version__}"},
    )
    response: urllib.response.addinfourl = urllib.request.urlopen(
        req, timeout=timeout, context=ssl_context
    )
    return response


def check_url(url: str, timeout: float = 10.0, insecure: bool = False) -> LinkResult:
    """Check a single URL.

    Args:
        url: URL to check
        timeout: Request timeout in seconds
        insecure: If True, disable SSL certificate verification
    """
    if not url:
        return LinkResult(url="", status=LinkStatus.SKIPPED)

    import time

    start_time = time.time()
    ssl_context = _get_ssl_context(insecure)

    try:
        with _fetch_url(url, timeout, ssl_context, method="HEAD") as response:
            elapsed_ms = (time.time() - start_time) * 1000
            return _make_link_result(url, response, elapsed_ms)
    except urllib.error.HTTPError as e:
        elapsed_ms = (time.time() - start_time) * 1000
        if e.code == 404:
            return LinkResult(
                url=url,
                status=LinkStatus.NOT_FOUND,
                status_code=e.code,
                response_time_ms=elapsed_ms,
            )
        elif e.code == 405:
            # Method not allowed - try GET
            try:
                with _fetch_url(url, timeout, ssl_context, method=None) as response:
                    elapsed_ms = (time.time() - start_time) * 1000
                    return _make_link_result(url, response, elapsed_ms)
            except Exception as e2:
                return LinkResult(
                    url=url,
                    status=LinkStatus.ERROR,
                    error_message=str(e2),
                    response_time_ms=elapsed_ms,
                )
        return LinkResult(
            url=url,
            status=LinkStatus.ERROR,
            status_code=e.code,
            error_message=f"HTTP {e.code}",
            response_time_ms=elapsed_ms,
        )
    except TimeoutError:
        return LinkResult(url=url, status=LinkStatus.TIMEOUT, error_message="Timeout")
    except Exception as e:
        return LinkResult(url=url, status=LinkStatus.ERROR, error_message=str(e))


def check_entry(
    name: str,
    url: Optional[str],
    repo: Optional[str],
    timeout: float,
    insecure: bool = False,
) -> CheckResult:
    """Check all links for a single entry."""
    url_result = check_url(url, timeout, insecure) if url else None
    repo_result = check_url(repo, timeout, insecure) if repo else None
    return CheckResult(entry_name=name, url_result=url_result, repo_result=repo_result)


def run_check(
    entries: list[dict[str, Any]],
    concurrency: int = 10,
    timeout: float = 10.0,
    progress_callback: Optional[ProgressCallback] = None,
    insecure: bool = False,
) -> list[CheckResult]:
    """Check all entries using thread pool.

    Args:
        entries: List of entry dictionaries to check
        concurrency: Number of concurrent requests
        timeout: Request timeout in seconds
        progress_callback: Callback for progress updates (default: no-op)
        insecure: If True, disable SSL certificate verification
    """
    callback = progress_callback or _noop_progress
    results = []

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(
                check_entry,
                entry.get("name", "unknown"),
                entry.get("url"),
                entry.get("repo"),
                timeout,
                insecure,
            ): (i, entry)
            for i, entry in enumerate(entries)
        }

        for future in as_completed(futures):
            i, entry = futures[future]
            result = future.result()
            results.append(result)
            callback(len(results), len(entries), entry.get("name", ""))

    return results


# =============================================================================
# GitHub API (using urllib + ThreadPoolExecutor)
# =============================================================================

GITHUB_API = "https://api.github.com"
GITHUB_REPO_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/.*)?$"
)


@dataclass
class RepoStats:
    """Statistics for a GitHub repository."""

    owner: str
    name: str
    full_name: str
    description: Optional[str]
    stars: int
    forks: int
    open_issues: int
    watchers: int
    language: Optional[str]
    license: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    pushed_at: Optional[datetime]
    archived: bool
    fork: bool
    default_branch: str
    topics: list[str]
    homepage: Optional[str] = None

    @property
    def days_since_push(self) -> Optional[int]:
        if self.pushed_at:
            return (datetime.now() - self.pushed_at).days
        return None

    @property
    def is_active(self) -> bool:
        days = self.days_since_push
        return days is not None and days < 365

    @property
    def activity_status(self) -> str:
        if self.archived:
            return "archived"
        days = self.days_since_push
        if days is None:
            return "unknown"
        if days < 30:
            return "very active"
        if days < 90:
            return "active"
        if days < 365:
            return "maintained"
        return "stale"


@dataclass
class RepoResult:
    """Result of fetching repo stats."""

    entry_name: str
    repo_url: str
    stats: Optional[RepoStats] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.stats is not None


def parse_github_url(url: str) -> Optional[tuple[str, str]]:
    """Extract owner and repo name from a GitHub URL."""
    if not url:
        return None
    match = GITHUB_REPO_PATTERN.match(url)
    if match:
        return match.group(1), match.group(2)
    return None


def get_github_token() -> Optional[str]:
    """Get GitHub token from environment."""
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


# -----------------------------------------------------------------------------
# GitHub API Cache
# -----------------------------------------------------------------------------


def _get_cache_key(owner: str, repo: str) -> str:
    """Generate cache key for a repository."""
    return f"{owner.lower()}/{repo.lower()}"


def _get_cached_response(
    db_path: Path, owner: str, repo: str
) -> Optional[dict[str, Any]]:
    """Get cached GitHub API response if still valid."""
    if not db_path.exists():
        return None

    cache_key = _get_cache_key(owner, repo)

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        # Ensure cache table exists
        cursor.execute(GITHUB_CACHE_SCHEMA)
        cursor.execute(
            """SELECT data FROM github_cache
               WHERE repo_key = ? AND expires_at > datetime('now')""",
            (cache_key,),
        )
        row = cursor.fetchone()
        if row:
            try:
                result: dict[str, Any] = json.loads(row["data"])
                return result
            except json.JSONDecodeError:
                return None
    return None


def _set_cached_response(
    db_path: Path,
    owner: str,
    repo: str,
    data: dict[str, Any],
    ttl_hours: int = GITHUB_CACHE_TTL_HOURS,
) -> None:
    """Store GitHub API response in cache."""
    cache_key = _get_cache_key(owner, repo)
    expires_at = datetime.now() + timedelta(hours=ttl_hours)

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(GITHUB_CACHE_SCHEMA)
        cursor.execute(
            """INSERT OR REPLACE INTO github_cache (repo_key, data, fetched_at, expires_at)
               VALUES (?, ?, datetime('now'), ?)""",
            (cache_key, json.dumps(data), expires_at.isoformat()),
        )
        conn.commit()


def clear_github_cache(
    db_path: Optional[Path] = None, expired_only: bool = True
) -> int:
    """Clear GitHub API cache.

    Args:
        db_path: Path to database
        expired_only: If True, only clear expired entries; if False, clear all

    Returns:
        Number of entries cleared
    """
    db_file = db_path or DEFAULT_DB
    if not db_file.exists():
        return 0

    with get_connection(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute(GITHUB_CACHE_SCHEMA)

        if expired_only:
            cursor.execute(
                "DELETE FROM github_cache WHERE expires_at <= datetime('now')"
            )
        else:
            cursor.execute("DELETE FROM github_cache")

        deleted = cursor.rowcount
        conn.commit()
        return deleted


def get_cache_stats(db_path: Optional[Path] = None) -> dict[str, Any]:
    """Get statistics about the GitHub cache."""
    db_file = db_path or DEFAULT_DB
    if not db_file.exists():
        return {"total": 0, "valid": 0, "expired": 0}

    with get_connection(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute(GITHUB_CACHE_SCHEMA)

        cursor.execute("SELECT COUNT(*) FROM github_cache")
        total = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM github_cache WHERE expires_at > datetime('now')"
        )
        valid = cursor.fetchone()[0]

        return {"total": total, "valid": valid, "expired": total - valid}


# -----------------------------------------------------------------------------
# Exponential Backoff for Rate Limiting
# -----------------------------------------------------------------------------


def _exponential_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
) -> float:
    """Calculate delay for exponential backoff.

    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Add random jitter to prevent thundering herd

    Returns:
        Delay in seconds
    """
    delay: float = min(base_delay * (2**attempt), max_delay)
    if jitter:
        delay = delay * (0.5 + random.random())  # 50-150% of calculated delay
    return delay


def _fetch_with_backoff(
    url: str,
    headers: dict[str, str],
    max_retries: int = 3,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Fetch URL with exponential backoff on rate limiting.

    Args:
        url: URL to fetch
        headers: HTTP headers
        max_retries: Maximum number of retries on 403
        timeout: Request timeout in seconds

    Returns:
        Parsed JSON response

    Raises:
        urllib.error.HTTPError: On non-retryable errors or max retries exceeded
    """
    last_error: Optional[urllib.error.HTTPError] = None

    for attempt in range(max_retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                result: dict[str, Any] = json.loads(response.read().decode())
                return result
        except urllib.error.HTTPError as e:
            if e.code == 403:
                last_error = e
                if attempt < max_retries:
                    delay = _exponential_backoff(attempt)
                    # Check for Retry-After header
                    retry_after = e.headers.get("Retry-After")
                    if retry_after:
                        try:
                            delay = max(delay, float(retry_after))
                        except ValueError:
                            pass
                    time.sleep(delay)
                    continue
            raise

    # Max retries exceeded
    if last_error:
        raise last_error
    raise RuntimeError("Unexpected state in backoff loop")


def _parse_repo_data(data: dict[str, Any]) -> RepoStats:
    """Parse GitHub API response into RepoStats."""

    def parse_date(date_str: Optional[str]) -> Optional[datetime]:
        if date_str:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00")).replace(
                tzinfo=None
            )
        return None

    license_name = None
    if data.get("license"):
        license_name = data["license"].get("spdx_id") or data["license"].get("name")

    return RepoStats(
        owner=data["owner"]["login"],
        name=data["name"],
        full_name=data["full_name"],
        description=data.get("description"),
        stars=data.get("stargazers_count", 0),
        forks=data.get("forks_count", 0),
        open_issues=data.get("open_issues_count", 0),
        watchers=data.get("subscribers_count", 0),
        language=data.get("language"),
        license=license_name,
        created_at=parse_date(data.get("created_at")),
        updated_at=parse_date(data.get("updated_at")),
        pushed_at=parse_date(data.get("pushed_at")),
        archived=data.get("archived", False),
        fork=data.get("fork", False),
        default_branch=data.get("default_branch", "main"),
        topics=data.get("topics", []),
        homepage=data.get("homepage") or None,
    )


def fetch_repo_stats(
    owner: str,
    repo: str,
    use_cache: bool = True,
    db_path: Optional[Path] = None,
) -> RepoStats:
    """Fetch repository statistics from GitHub API.

    Args:
        owner: Repository owner
        repo: Repository name
        use_cache: Whether to use cached responses (default: True)
        db_path: Path to database for cache storage

    Returns:
        RepoStats with repository information

    Features:
        - Caches responses for 24 hours to reduce API calls
        - Uses exponential backoff on rate limiting (403)
    """
    db_file = db_path or DEFAULT_DB

    # Check cache first
    if use_cache:
        cached = _get_cached_response(db_file, owner, repo)
        if cached:
            return _parse_repo_data(cached)

    # Prepare request
    token = get_github_token()
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": f"linkdb/{__version__}",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{GITHUB_API}/repos/{owner}/{repo}"

    # Fetch with exponential backoff on rate limiting
    data = _fetch_with_backoff(url, headers, max_retries=3, timeout=30.0)

    # Cache the response
    if use_cache:
        _set_cached_response(db_file, owner, repo, data)

    return _parse_repo_data(data)


def fetch_entry_stats(
    entry_name: str,
    repo_url: str,
    use_cache: bool = True,
    db_path: Optional[Path] = None,
) -> RepoResult:
    """Fetch stats for a single entry's repository.

    Args:
        entry_name: Name of the entry
        repo_url: GitHub repository URL
        use_cache: Whether to use cached responses
        db_path: Path to database for cache storage
    """
    parsed = parse_github_url(repo_url)
    if not parsed:
        return RepoResult(entry_name=entry_name, repo_url=repo_url, error="Not GitHub")

    owner, repo = parsed
    try:
        stats = fetch_repo_stats(owner, repo, use_cache=use_cache, db_path=db_path)
        return RepoResult(entry_name=entry_name, repo_url=repo_url, stats=stats)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return RepoResult(
                entry_name=entry_name, repo_url=repo_url, error="Not found"
            )
        elif e.code == 403:
            return RepoResult(
                entry_name=entry_name,
                repo_url=repo_url,
                error="Rate limited (retries exhausted)",
            )
        return RepoResult(
            entry_name=entry_name, repo_url=repo_url, error=f"HTTP {e.code}"
        )
    except Exception as e:
        return RepoResult(entry_name=entry_name, repo_url=repo_url, error=str(e))


def run_fetch_stats(
    entries: list[dict[str, Any]],
    concurrency: int = 5,
    progress_callback: Optional[ProgressCallback] = None,
    use_cache: bool = True,
    db_path: Optional[Path] = None,
) -> list[RepoResult]:
    """Fetch stats for all entries with GitHub repos using thread pool.

    Args:
        entries: List of entry dictionaries
        concurrency: Number of concurrent requests
        progress_callback: Callback for progress updates
        use_cache: Whether to use cached responses (default: True)
        db_path: Path to database for cache storage
    """
    callback = progress_callback or _noop_progress
    github_entries = [
        e for e in entries if e.get("repo") and "github.com" in e.get("repo", "")
    ]

    results = []

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(
                fetch_entry_stats,
                entry.get("name", "unknown"),
                entry.get("repo", ""),
                use_cache,
                db_path,
            ): (i, entry)
            for i, entry in enumerate(github_entries)
        }

        for future in as_completed(futures):
            i, entry = futures[future]
            result = future.result()
            results.append(result)
            callback(len(results), len(github_entries), entry.get("name", ""))

    return results


# =============================================================================
# Webloc Parser (macOS .webloc bookmark files)
# =============================================================================


@dataclass
class WeblocEntry:
    """Parsed webloc file entry."""

    path: Path
    url: str
    name: str  # Derived from filename

    @property
    def is_github(self) -> bool:
        """Check if this webloc points to a GitHub URL."""
        return "github.com" in self.url


@dataclass
class WeblocScanResult:
    """Result of scanning a directory for webloc files."""

    entries: list[WeblocEntry] = field(default_factory=list)
    errors: list[tuple[Path, str]] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return len(self.entries)

    @property
    def error_count(self) -> int:
        return len(self.errors)


def parse_webloc_file(path: Path) -> WeblocEntry:
    """
    Parse a macOS .webloc file and extract the URL.

    Webloc files are Apple plist files (XML or binary) containing a URL key.

    Args:
        path: Path to the .webloc file

    Returns:
        WeblocEntry with the parsed URL and name derived from filename

    Raises:
        ValueError: If the file cannot be parsed or doesn't contain a URL
    """
    if not path.exists():
        raise ValueError(f"File not found: {path}")

    if not path.suffix.lower() == ".webloc":
        raise ValueError(f"Not a webloc file: {path}")

    try:
        with open(path, "rb") as f:
            plist_data = plistlib.load(f)
    except Exception as e:
        raise ValueError(f"Failed to parse plist: {e}")

    url = plist_data.get("URL")
    if not url:
        raise ValueError("No URL found in webloc file")

    # Derive name from filename (without extension)
    name = path.stem

    return WeblocEntry(path=path, url=url, name=name)


def scan_webloc_directory(
    directory: Path,
    recursive: bool = False,
) -> WeblocScanResult:
    """
    Scan a directory for .webloc files and parse them.

    Args:
        directory: Directory to scan
        recursive: If True, scan subdirectories recursively

    Returns:
        WeblocScanResult containing parsed entries and any errors
    """
    result = WeblocScanResult()

    if not directory.exists():
        result.errors.append((directory, "Directory not found"))
        return result

    if not directory.is_dir():
        result.errors.append((directory, "Not a directory"))
        return result

    # Find all .webloc files
    pattern = "**/*.webloc" if recursive else "*.webloc"
    webloc_files = list(directory.glob(pattern))

    for webloc_path in webloc_files:
        try:
            entry = parse_webloc_file(webloc_path)
            result.entries.append(entry)
        except ValueError as e:
            result.errors.append((webloc_path, str(e)))

    return result


def import_webloc_entries(
    webloc_entries: list[WeblocEntry],
    category: str,
    json_path: Optional[Path] = None,
    db_path: Optional[Path] = None,
    use_github_metadata: bool = True,
    default_description: str = "Imported from webloc bookmark",
) -> tuple[int, int, list[str]]:
    """
    Import webloc entries into the linkdb system.

    Args:
        webloc_entries: List of WeblocEntry objects to import
        category: Category to assign to all entries
        json_path: Path to JSON file
        db_path: Path to database
        use_github_metadata: If True, fetch metadata for GitHub URLs
        default_description: Default description for non-GitHub entries

    Returns:
        Tuple of (imported_count, skipped_count, error_messages)
    """
    imported = 0
    skipped = 0
    errors: list[str] = []

    for entry in webloc_entries:
        try:
            # Check if entry already exists
            existing = get_entry(entry.name, json_path)
            if existing:
                skipped += 1
                continue

            # Try GitHub auto-population for GitHub URLs
            if use_github_metadata and entry.is_github:
                try:
                    add_entry_from_github(
                        github_url=entry.url,
                        category=category,
                        name=entry.name,
                        json_path=json_path,
                        db_path=db_path,
                        sync=True,
                    )
                    imported += 1
                    continue
                except ValueError:
                    # Fall back to regular add if GitHub fetch fails
                    pass

            # Regular add for non-GitHub or if GitHub fetch failed
            # Determine if URL is likely a repo or a website
            is_repo = any(
                host in entry.url
                for host in [
                    "github.com",
                    "gitlab.com",
                    "bitbucket.org",
                    "codeberg.org",
                ]
            )

            add_entry(
                name=entry.name,
                category=category,
                desc=default_description,
                url=None if is_repo else entry.url,
                repo=entry.url if is_repo else None,
                json_path=json_path,
                db_path=db_path,
                sync=True,
            )
            imported += 1

        except (ValueError, KeyError) as e:
            errors.append(f"{entry.name}: {e}")

    return imported, skipped, errors


# =============================================================================
# Entry API (CRUD operations on JSON file with DB sync)
# =============================================================================


def load_entries(json_path: Optional[Path] = None) -> list[dict[str, Any]]:
    """Load entries from JSON file."""
    data = load_data(json_path)
    entries: list[dict[str, Any]] = data.get("entries", [])
    return entries


def save_entries(
    entries: list[dict[str, Any]], json_path: Optional[Path] = None
) -> None:
    """Save entries to JSON file (preserves categories)."""
    data = load_data(json_path)
    data["entries"] = entries
    save_data(data, json_path)


def sync_to_db(
    json_path: Optional[Path] = None, db_path: Optional[Path] = None
) -> tuple[int, int]:
    """Sync JSON entries to database. Returns (imported, skipped)."""
    json_file = json_path or DEFAULT_JSON
    db_file = db_path or DEFAULT_DB
    imported, skipped, _ = import_from_json(json_file, db_file, skip_duplicates=False)
    return imported, skipped


def add_entry(
    name: str,
    category: str,
    desc: str,
    url: Optional[str] = None,
    repo: Optional[str] = None,
    json_path: Optional[Path] = None,
    db_path: Optional[Path] = None,
    sync: bool = True,
) -> dict[str, Any]:
    """
    Add a new entry to the JSON file.

    Args:
        name: Project name
        category: Category (should be from CATEGORIES)
        desc: Project description
        url: Optional project URL
        repo: Optional repository URL
        json_path: Path to JSON file (default: data/entries.json)
        db_path: Path to database (default: linkdb.db)
        sync: Whether to sync to database after adding

    Returns:
        The added entry dict

    Raises:
        ValueError: If validation fails (missing url/repo, invalid category, etc.)
        KeyError: If entry with same name already exists
    """
    if not url and not repo:
        raise ValueError("Must provide at least url or repo")

    # Normalize category input
    category = normalize_category_input(category)

    # Check category
    categories = load_categories(json_path)
    if category not in categories:
        raise ValueError(f"Unknown category: {category}")

    entry = {
        "name": name,
        "category": category,
        "desc": desc,
        "url": url,
        "repo": repo,
    }

    # Validate the entry
    is_valid, error = validate_entry(entry)
    if not is_valid:
        raise ValueError(error)

    # Load existing entries
    entries = load_entries(json_path)

    # Check for duplicates
    for existing in entries:
        if existing.get("name") == name:
            raise KeyError(f"Entry '{name}' already exists")

    # Add and save
    entries.append(entry)
    save_entries(entries, json_path)

    # Sync to database and record history
    if sync:
        sync_to_db(json_path, db_path)
        db_file = db_path or DEFAULT_DB
        if db_file.exists():
            with get_connection(db_file) as conn:
                record_history(
                    conn,
                    action="add",
                    entry_name=name,
                    category=category,
                    details=f"url={url or ''}, repo={repo or ''}",
                )

    return entry


def remove_entry(
    name: str,
    json_path: Optional[Path] = None,
    db_path: Optional[Path] = None,
    sync: bool = True,
) -> dict[str, Any]:
    """
    Remove an entry from the JSON file.

    Args:
        name: Project name to remove
        json_path: Path to JSON file (default: data/entries.json)
        db_path: Path to database (default: linkdb.db)
        sync: Whether to sync to database after removing

    Returns:
        The removed entry dict

    Raises:
        KeyError: If entry not found
    """
    entries = load_entries(json_path)

    # Find the entry
    removed = None
    for e in entries:
        if e.get("name") == name:
            removed = e
            break

    if removed is None:
        raise KeyError(f"Entry '{name}' not found")

    # Remove and save
    entries = [e for e in entries if e.get("name") != name]
    save_entries(entries, json_path)

    # Sync to database (remove from DB too) and record history
    if sync:
        db_file = db_path or DEFAULT_DB
        if db_file.exists():
            with get_connection(db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM entry WHERE name = ?", (name,))
                record_history(
                    conn,
                    action="remove",
                    entry_name=name,
                    category=removed.get("category"),
                    details=f"Removed entry: {removed.get('desc', '')[:50]}",
                )
                conn.commit()

    return removed


def update_entry(
    name: str,
    category: Optional[str] = None,
    desc: Optional[str] = None,
    url: Optional[str] = None,
    repo: Optional[str] = None,
    json_path: Optional[Path] = None,
    db_path: Optional[Path] = None,
    sync: bool = True,
) -> dict[str, Any]:
    """
    Update an existing entry in the JSON file.

    Args:
        name: Project name to update
        category: New category (optional)
        desc: New description (optional)
        url: New URL (optional, use empty string to clear)
        repo: New repo (optional, use empty string to clear)
        json_path: Path to JSON file (default: data/entries.json)
        db_path: Path to database (default: linkdb.db)
        sync: Whether to sync to database after updating

    Returns:
        The updated entry dict

    Raises:
        KeyError: If entry not found
        ValueError: If validation fails
    """
    entries = load_entries(json_path)

    # Find the entry
    found_idx = None
    for i, e in enumerate(entries):
        if e.get("name") == name:
            found_idx = i
            break

    if found_idx is None:
        raise KeyError(f"Entry '{name}' not found")

    entry = entries[found_idx]

    # Apply updates
    if category is not None:
        category = normalize_category_input(category)
        categories = load_categories(json_path)
        if category not in categories:
            raise ValueError(f"Unknown category: {category}")
        entry["category"] = category
    if desc is not None:
        entry["desc"] = desc
    if url is not None:
        entry["url"] = url if url else None
    if repo is not None:
        entry["repo"] = repo if repo else None

    # Validate the updated entry
    is_valid, error = validate_entry(entry)
    if not is_valid:
        raise ValueError(error)

    # Build change details
    changes = []
    if category is not None:
        changes.append(f"category={category}")
    if desc is not None:
        changes.append("desc changed")
    if url is not None:
        changes.append(f"url={url or '(cleared)'}")
    if repo is not None:
        changes.append(f"repo={repo or '(cleared)'}")

    # Save
    entries[found_idx] = entry
    save_entries(entries, json_path)

    # Sync to database and record history
    if sync:
        sync_to_db(json_path, db_path)
        db_file = db_path or DEFAULT_DB
        if db_file.exists():
            with get_connection(db_file) as conn:
                record_history(
                    conn,
                    action="update",
                    entry_name=name,
                    category=entry.get("category"),
                    details=", ".join(changes) if changes else "no changes",
                )

    return entry


def get_entry(name: str, json_path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    """Get an entry by name from the JSON file."""
    entries = load_entries(json_path)
    for e in entries:
        if e.get("name") == name:
            return e
    return None


def add_entry_from_github(
    github_url: str,
    category: str,
    name: Optional[str] = None,
    desc: Optional[str] = None,
    json_path: Optional[Path] = None,
    db_path: Optional[Path] = None,
    sync: bool = True,
) -> dict[str, Any]:
    """
    Add a new entry by fetching metadata from a GitHub URL.

    Args:
        github_url: GitHub repository URL
        category: Category (should be from CATEGORIES)
        name: Override for project name (default: repo name)
        desc: Override for description (default: GitHub description)
        json_path: Path to JSON file (default: data/entries.json)
        db_path: Path to database (default: linkdb.db)
        sync: Whether to sync to database after adding

    Returns:
        The added entry dict

    Raises:
        ValueError: If URL is invalid, not a GitHub URL, or API fetch fails
        KeyError: If entry with same name already exists
    """
    # Parse GitHub URL
    parsed = parse_github_url(github_url)
    if not parsed:
        raise ValueError(f"Invalid GitHub URL: {github_url}")

    owner, repo = parsed

    # Fetch metadata from GitHub API
    try:
        stats = fetch_repo_stats(owner, repo)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise ValueError(f"Repository not found: {github_url}")
        elif e.code == 403:
            raise ValueError("GitHub API rate limit exceeded. Set GITHUB_TOKEN.")
        raise ValueError(f"GitHub API error: HTTP {e.code}")
    except Exception as e:
        raise ValueError(f"Failed to fetch GitHub data: {e}")

    # Use provided values or defaults from GitHub
    entry_name = name or stats.name
    entry_desc = (
        desc or stats.description or f"A {stats.language or 'software'} project"
    )

    # Build the GitHub repo URL (canonical form)
    repo_url = f"https://github.com/{stats.full_name}"

    # Use homepage if available, otherwise None
    entry_url = stats.homepage if stats.homepage else None

    # Convert topics to comma-separated keywords
    keywords = ", ".join(stats.topics) if stats.topics else None

    # Format last_pushed as date string
    last_pushed = stats.pushed_at.strftime("%Y-%m-%d") if stats.pushed_at else None

    # Add to JSON via existing add_entry
    entry = add_entry(
        name=entry_name,
        category=category,
        desc=entry_desc,
        url=entry_url,
        repo=repo_url,
        json_path=json_path,
        db_path=db_path,
        sync=False,  # We'll sync manually to include GitHub fields
    )

    # Now update the database with GitHub-specific fields
    if sync:
        db_file = db_path or DEFAULT_DB

        # First sync the basic entry
        sync_to_db(json_path, db_file)

        # Then update with GitHub fields
        with init_db(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE entry SET
                   keywords = ?,
                   stars = ?,
                   forks = ?,
                   language = ?,
                   license = ?,
                   archived = ?,
                   last_pushed = ?
                   WHERE name = ?""",
                (
                    keywords,
                    stats.stars,
                    stats.forks,
                    stats.language,
                    stats.license,
                    1 if stats.archived else 0,
                    last_pushed,
                    entry_name,
                ),
            )
            conn.commit()

    return entry


@dataclass
class BatchAddResult:
    """Result of a batch add operation."""

    added: list[str] = field(default_factory=list)
    skipped: list[tuple[str, str]] = field(default_factory=list)  # (url, reason)
    errors: list[tuple[str, str]] = field(default_factory=list)  # (url, error)

    @property
    def total_processed(self) -> int:
        return len(self.added) + len(self.skipped) + len(self.errors)


def add_many_entries(
    urls: list[str],
    category: str,
    json_path: Optional[Path] = None,
    db_path: Optional[Path] = None,
    dry_run: bool = False,
) -> BatchAddResult:
    """
    Add multiple entries from a list of URLs.

    Args:
        urls: List of URLs (GitHub URLs will auto-populate metadata)
        category: Category for all entries
        json_path: Path to JSON file
        db_path: Path to database
        dry_run: If True, don't actually add entries

    Returns:
        BatchAddResult with added, skipped, and error lists
    """
    result = BatchAddResult()

    # Validate category first
    categories = load_categories(json_path)
    normalized_cat = normalize_category_input(category)
    if normalized_cat not in categories:
        result.errors.append(("*", f"Unknown category: {category}"))
        return result

    for url in urls:
        url = url.strip()
        if not url or url.startswith("#"):
            continue

        # Check if it's a GitHub URL
        is_github = "github.com" in url

        try:
            if dry_run:
                # Check for duplicates
                parsed = parse_github_url(url) if is_github else None
                name = parsed[1] if parsed else url.split("/")[-1]
                existing = get_entry(name, json_path)
                if existing:
                    result.skipped.append((url, f"Entry '{name}' already exists"))
                else:
                    result.added.append(url)
            else:
                if is_github:
                    entry = add_entry_from_github(
                        github_url=url,
                        category=normalized_cat,
                        json_path=json_path,
                        db_path=db_path,
                        sync=True,
                    )
                    result.added.append(entry["name"])
                else:
                    # Non-GitHub URL - derive name from URL
                    name = url.rstrip("/").split("/")[-1]
                    entry = add_entry(
                        name=name,
                        category=normalized_cat,
                        desc=f"Project from {url}",
                        url=url,
                        json_path=json_path,
                        db_path=db_path,
                        sync=True,
                    )
                    result.added.append(entry["name"])
        except KeyError as e:
            result.skipped.append((url, str(e)))
        except ValueError as e:
            result.errors.append((url, str(e)))
        except Exception as e:
            result.errors.append((url, str(e)))

    return result


@dataclass
class BatchRemoveResult:
    """Result of a batch remove operation."""

    removed: list[str] = field(default_factory=list)
    entries_to_remove: list[dict[str, Any]] = field(default_factory=list)


def remove_entries_by_category(
    category: str,
    json_path: Optional[Path] = None,
    db_path: Optional[Path] = None,
    dry_run: bool = False,
) -> BatchRemoveResult:
    """
    Remove all entries in a category.

    Args:
        category: Category to remove entries from
        json_path: Path to JSON file
        db_path: Path to database
        dry_run: If True, return entries that would be removed without removing them

    Returns:
        BatchRemoveResult with removed entries
    """
    result = BatchRemoveResult()
    normalized_cat = normalize_category_input(category)

    entries = load_entries(json_path)

    # Find entries to remove
    result.entries_to_remove = [
        e for e in entries if e.get("category") == normalized_cat
    ]

    if dry_run or not result.entries_to_remove:
        return result

    # Remove entries
    remaining = [e for e in entries if e.get("category") != normalized_cat]
    save_entries(remaining, json_path)

    # Sync to database
    db_file = db_path or DEFAULT_DB
    if db_file.exists():
        with get_connection(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM entry WHERE category = ?", (normalized_cat,))
            conn.commit()

    result.removed = [e["name"] for e in result.entries_to_remove]
    return result


# =============================================================================
# Deduplication
# =============================================================================


@dataclass
class DuplicateGroup:
    """A group of entries that appear to be duplicates."""

    key: str  # The URL or repo that's duplicated
    key_type: str  # "repo" or "url"
    entries: list[dict[str, Any]] = field(default_factory=list)

    @property
    def primary(self) -> dict[str, Any]:
        """Return the entry that should be kept (most complete)."""

        # Score entries by completeness
        def score(e: dict[str, Any]) -> int:
            s = 0
            if e.get("url"):
                s += 1
            if e.get("repo"):
                s += 1
            if e.get("desc") and len(e.get("desc", "")) > 20:
                s += 1
            return s

        return max(self.entries, key=score)

    @property
    def duplicates(self) -> list[dict[str, Any]]:
        """Return entries that should be removed."""
        primary = self.primary
        return [e for e in self.entries if e["name"] != primary["name"]]


@dataclass
class DedupeResult:
    """Result of deduplication scan."""

    duplicate_groups: list[DuplicateGroup] = field(default_factory=list)

    @property
    def total_duplicates(self) -> int:
        return sum(len(g.duplicates) for g in self.duplicate_groups)

    @property
    def has_duplicates(self) -> bool:
        return len(self.duplicate_groups) > 0


def find_duplicates(json_path: Optional[Path] = None) -> DedupeResult:
    """
    Find entries that point to the same URL or repository.

    Returns:
        DedupeResult with groups of duplicate entries
    """
    entries = load_entries(json_path)
    result = DedupeResult()

    # Group by repo URL
    repo_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        repo = entry.get("repo")
        if repo:
            # Normalize repo URL
            normalized = repo.lower().rstrip("/").removesuffix(".git")
            repo_map[normalized].append(entry)

    # Group by URL (only if no repo)
    url_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        if not entry.get("repo"):
            url = entry.get("url")
            if url:
                normalized = url.lower().rstrip("/")
                url_map[normalized].append(entry)

    # Find duplicates in repo groups
    for repo_url, group_entries in repo_map.items():
        if len(group_entries) > 1:
            result.duplicate_groups.append(
                DuplicateGroup(key=repo_url, key_type="repo", entries=group_entries)
            )

    # Find duplicates in URL groups
    for url, group_entries in url_map.items():
        if len(group_entries) > 1:
            result.duplicate_groups.append(
                DuplicateGroup(key=url, key_type="url", entries=group_entries)
            )

    return result


def merge_duplicates(
    group: DuplicateGroup,
    json_path: Optional[Path] = None,
    db_path: Optional[Path] = None,
    dry_run: bool = False,
) -> list[str]:
    """
    Merge a group of duplicates by keeping the primary and removing others.

    Returns:
        List of removed entry names
    """
    _primary = group.primary  # kept for reference, may be used in future
    to_remove = group.duplicates
    removed_names = []

    if dry_run:
        return [e["name"] for e in to_remove]

    for entry in to_remove:
        try:
            remove_entry(entry["name"], json_path, db_path, sync=True)
            removed_names.append(entry["name"])
        except KeyError:
            pass  # Already removed

    return removed_names


# =============================================================================
# Interactive Mode
# =============================================================================


def prompt_with_default(prompt: str, default: Optional[str] = None) -> str:
    """Prompt for input with an optional default value."""
    if default:
        result = input(f"{prompt} [{default}]: ").strip()
        return result if result else default
    return input(f"{prompt}: ").strip()


def prompt_choice(
    prompt: str,
    choices: list[str],
    allow_custom: bool = False,
) -> str:
    """Prompt user to select from a list of choices."""
    print(f"\n{prompt}")
    for i, choice in enumerate(choices, 1):
        print(f"  {i}. {choice}")
    if allow_custom:
        print(f"  {len(choices) + 1}. [Enter custom value]")

    while True:
        try:
            selection = input("Select (number): ").strip()
            if not selection:
                continue
            idx = int(selection) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
            if allow_custom and idx == len(choices):
                return input("Enter custom value: ").strip()
            print(f"Please enter a number between 1 and {len(choices)}")
        except ValueError:
            # Allow typing the choice directly
            if selection.lower() in [c.lower() for c in choices]:
                return next(c for c in choices if c.lower() == selection.lower())
            print("Invalid selection")


def interactive_add(
    json_path: Optional[Path] = None,
    db_path: Optional[Path] = None,
) -> Optional[dict[str, Any]]:
    """
    Interactively create a new entry with prompts.

    Returns:
        The created entry, or None if cancelled
    """
    print("\n=== Add New Entry (Interactive Mode) ===\n")

    # Get URL or repo first (for auto-population)
    print("Enter the project URL or GitHub repository URL.")
    print("(GitHub URLs will auto-populate name and description)")
    url_or_repo = input("URL/Repo: ").strip()

    if not url_or_repo:
        print("Cancelled - no URL provided")
        return None

    # Check if it's a GitHub URL
    is_github = "github.com" in url_or_repo

    # Get category
    categories = sorted(load_categories(json_path))
    category = prompt_choice(
        "Select category:",
        categories,
        allow_custom=False,
    )

    if is_github:
        # Try to auto-populate from GitHub
        print("\nFetching metadata from GitHub...")
        parsed = parse_github_url(url_or_repo)
        if parsed:
            try:
                stats = fetch_repo_stats(parsed[0], parsed[1])
                print(f"  Found: {stats.name}")
                print(f"  Description: {stats.description or '(none)'}")
                print(f"  Stars: {stats.stars}, Language: {stats.language}")

                # Confirm or override
                name = prompt_with_default("Name", stats.name)
                desc = prompt_with_default(
                    "Description",
                    stats.description or f"A {stats.language or 'software'} project",
                )

                # Confirm
                print("\n--- Entry Preview ---")
                print(f"  Name: {name}")
                print(f"  Category: {category}")
                print(f"  Description: {desc}")
                print(f"  Repo: {url_or_repo}")
                if stats.homepage:
                    print(f"  URL: {stats.homepage}")

                confirm = input("\nAdd this entry? [Y/n]: ").strip().lower()
                if confirm and confirm != "y":
                    print("Cancelled")
                    return None

                entry = add_entry_from_github(
                    github_url=url_or_repo,
                    category=category,
                    name=name,
                    desc=desc,
                    json_path=json_path,
                    db_path=db_path,
                    sync=True,
                )
                return entry

            except Exception as e:
                print(f"  Could not fetch GitHub data: {e}")
                print("  Falling back to manual entry...")

    # Manual entry (non-GitHub or GitHub fetch failed)
    name = input("Project name: ").strip()
    if not name:
        print("Cancelled - no name provided")
        return None

    desc = input("Description: ").strip()
    if not desc:
        print("Cancelled - no description provided")
        return None

    # Determine if URL is a repo or website
    is_repo = any(
        host in url_or_repo
        for host in ["github.com", "gitlab.com", "bitbucket.org", "codeberg.org"]
    )

    url: Optional[str]
    repo: Optional[str]
    if is_repo:
        repo = url_or_repo
        url_input = input(
            "Project website URL (optional, press Enter to skip): "
        ).strip()
        url = url_input if url_input else None
    else:
        url = url_or_repo
        repo_input = input("Repository URL (optional, press Enter to skip): ").strip()
        repo = repo_input if repo_input else None

    # Confirm
    print("\n--- Entry Preview ---")
    print(f"  Name: {name}")
    print(f"  Category: {category}")
    print(f"  Description: {desc}")
    if url:
        print(f"  URL: {url}")
    if repo:
        print(f"  Repo: {repo}")

    confirm = input("\nAdd this entry? [Y/n]: ").strip().lower()
    if confirm and confirm != "y":
        print("Cancelled")
        return None

    entry = add_entry(
        name=name,
        category=category,
        desc=desc,
        url=url,
        repo=repo,
        json_path=json_path,
        db_path=db_path,
        sync=True,
    )
    return entry


# =============================================================================
# Backup / Restore
# =============================================================================

DEFAULT_BACKUP_DIR = _PROJECT_ROOT / "data" / "backups"


@dataclass
class BackupInfo:
    """Information about a backup."""

    path: Path
    timestamp: datetime
    has_json: bool
    has_db: bool

    @property
    def name(self) -> str:
        return self.path.name


def create_backup(
    json_path: Optional[Path] = None,
    db_path: Optional[Path] = None,
    backup_dir: Optional[Path] = None,
) -> Path:
    """
    Create a timestamped backup of JSON and database files.

    Returns:
        Path to the created backup archive
    """
    json_file = json_path or DEFAULT_JSON
    db_file = db_path or DEFAULT_DB
    backup_directory = backup_dir or DEFAULT_BACKUP_DIR

    # Create backup directory if needed
    backup_directory.mkdir(parents=True, exist_ok=True)

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}.tar.gz"
    backup_path = backup_directory / backup_name

    # Create tar archive
    with tarfile.open(backup_path, "w:gz") as tar:
        if json_file.exists():
            tar.add(json_file, arcname=json_file.name)
        if db_file.exists():
            tar.add(db_file, arcname=db_file.name)

    return backup_path


def list_backups(backup_dir: Optional[Path] = None) -> list[BackupInfo]:
    """List all available backups, sorted by timestamp (newest first)."""
    backup_directory = backup_dir or DEFAULT_BACKUP_DIR

    if not backup_directory.exists():
        return []

    backups = []
    for path in backup_directory.glob("backup_*.tar.gz"):
        # Parse timestamp from filename
        try:
            name = path.stem.replace(".tar", "")  # Remove .tar from backup_*.tar
            ts_str = name.replace("backup_", "")
            timestamp = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")

            # Check contents
            has_json = False
            has_db = False
            with tarfile.open(path, "r:gz") as tar:
                names = tar.getnames()
                has_json = any(n.endswith(".json") for n in names)
                has_db = any(n.endswith(".db") for n in names)

            backups.append(
                BackupInfo(
                    path=path,
                    timestamp=timestamp,
                    has_json=has_json,
                    has_db=has_db,
                )
            )
        except (ValueError, tarfile.TarError):
            continue

    return sorted(backups, key=lambda b: b.timestamp, reverse=True)


def restore_backup(
    backup_path: Path,
    json_path: Optional[Path] = None,
    db_path: Optional[Path] = None,
    dry_run: bool = False,
) -> tuple[bool, bool]:
    """
    Restore from a backup archive.

    Args:
        backup_path: Path to backup archive
        json_path: Where to restore JSON file
        db_path: Where to restore database
        dry_run: If True, don't actually restore

    Returns:
        Tuple of (json_restored, db_restored)
    """
    json_file = json_path or DEFAULT_JSON
    db_file = db_path or DEFAULT_DB

    json_restored = False
    db_restored = False

    with tarfile.open(backup_path, "r:gz") as tar:
        for member in tar.getmembers():
            if member.name.endswith(".json"):
                if not dry_run:
                    # Extract to temp then move
                    tar.extract(member, path=json_file.parent)
                    extracted = json_file.parent / member.name
                    if extracted != json_file:
                        shutil.move(str(extracted), str(json_file))
                json_restored = True
            elif member.name.endswith(".db"):
                if not dry_run:
                    tar.extract(member, path=db_file.parent)
                    extracted = db_file.parent / member.name
                    if extracted != db_file:
                        shutil.move(str(extracted), str(db_file))
                db_restored = True

    return json_restored, db_restored


# =============================================================================
# History / Diff
# =============================================================================


@dataclass
class HistoryEntry:
    """A single history entry."""

    id: int
    timestamp: datetime
    action: str
    entry_name: str
    category: Optional[str]
    details: Optional[str]


def get_history(
    db_path: Optional[Path] = None,
    since: Optional[datetime] = None,
    action: Optional[str] = None,
    limit: int = 100,
) -> list[HistoryEntry]:
    """
    Get history entries from the database.

    Args:
        db_path: Path to database
        since: Only return entries after this timestamp
        action: Filter by action type (add, remove, update)
        limit: Maximum number of entries to return
    """
    db_file = db_path or DEFAULT_DB
    if not db_file.exists():
        return []

    conditions = []
    params: list[Any] = []

    if since:
        conditions.append("timestamp >= ?")
        params.append(since.isoformat())
    if action:
        conditions.append("action = ?")
        params.append(action)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    with get_connection(db_file) as conn:
        cursor = conn.cursor()

        # Ensure history table exists (migrate if needed)
        cursor.execute(HISTORY_SCHEMA)
        conn.commit()

        query = f"""
            SELECT id, timestamp, action, entry_name, category, details
            FROM history
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
        """
        params.append(limit)
        cursor.execute(query, params)
        rows = cursor.fetchall()

    entries = []
    for row in rows:
        try:
            ts = datetime.fromisoformat(row["timestamp"])
        except (ValueError, TypeError):
            ts = datetime.now()
        entries.append(
            HistoryEntry(
                id=row["id"],
                timestamp=ts,
                action=row["action"],
                entry_name=row["entry_name"],
                category=row["category"],
                details=row["details"],
            )
        )

    return entries


def get_entry_history(
    entry_name: str,
    db_path: Optional[Path] = None,
) -> list[HistoryEntry]:
    """Get all history for a specific entry."""
    db_file = db_path or DEFAULT_DB
    if not db_file.exists():
        return []

    with get_connection(db_file) as conn:
        cursor = conn.cursor()

        # Ensure history table exists (migrate if needed)
        cursor.execute(HISTORY_SCHEMA)
        conn.commit()

        cursor.execute(
            """SELECT id, timestamp, action, entry_name, category, details
               FROM history WHERE entry_name = ? ORDER BY timestamp DESC""",
            (entry_name,),
        )
        rows = cursor.fetchall()

    entries = []
    for row in rows:
        try:
            ts = datetime.fromisoformat(row["timestamp"])
        except (ValueError, TypeError):
            ts = datetime.now()
        entries.append(
            HistoryEntry(
                id=row["id"],
                timestamp=ts,
                action=row["action"],
                entry_name=row["entry_name"],
                category=row["category"],
                details=row["details"],
            )
        )

    return entries


# =============================================================================
# README Generator (string.Template)
# =============================================================================

DEFAULT_TEMPLATE = Template("""# Awesome Audio

> A curated guide to open-source audio and music projects.

[![License: CC0-1.0](https://img.shields.io/badge/License-CC0_1.0-lightgrey.svg)](http://creativecommons.org/publicdomain/zero/1.0/)

This list contains **$total_entries** projects across **$total_categories** categories.

*Last updated: $generated_at*

## Contents

$toc

---

$sections

---

## Contributing

Contributions welcome! Please read the contribution guidelines first.

## License

[![CC0](https://licensebuttons.net/p/zero/1.0/88x31.png)](http://creativecommons.org/publicdomain/zero/1.0/)

To the extent possible under law, the authors have waived all copyright and related rights to this work.
""")


def normalize_category(category: str) -> str:
    """Normalize a category string for display."""
    words = category.replace("-", " ").replace("_", " ").split()
    return " ".join(word.capitalize() for word in words)


def category_anchor(category: str) -> str:
    """Generate a markdown anchor from a category name."""
    return category.lower().replace(" ", "-").replace("_", "-")


def generate_readme(
    db_path: Path,
    template_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    force: bool = False,
) -> str:
    """Generate README.md from database entries."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entry ORDER BY category, name")
        rows = cursor.fetchall()

    if not rows:
        return "# Awesome Audio\n\nNo entries yet.\n"

    groups: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        groups[row["category"]].append(row)

    toc_lines = []
    for cat_name in sorted(groups.keys()):
        title = normalize_category(cat_name)
        anchor = category_anchor(title)
        toc_lines.append(f"- [{title}](#{anchor})")

    section_lines = []
    for cat_name in sorted(groups.keys()):
        title = normalize_category(cat_name)
        section_lines.append(f"## {title}\n")

        for row in sorted(groups[cat_name], key=lambda r: r["name"].lower()):
            url = row["url"] or row["repo"]
            section_lines.append(
                f"- **[{row['name']}]({url})** - {row['description']}\n"
            )

        section_lines.append("")

    content = DEFAULT_TEMPLATE.substitute(
        total_entries=len(rows),
        total_categories=len(groups),
        generated_at=datetime.now().strftime("%Y-%m-%d"),
        toc="\n".join(toc_lines),
        sections="\n".join(section_lines),
    )

    if output_path:
        if output_path.exists() and not force:
            response = input(f"{output_path} already exists. Overwrite? [y/N]: ")
            if response.lower() not in ("y", "yes"):
                print("Aborted.")
                return content
        with open(output_path, "w") as f:
            f.write(content)

    return content


# =============================================================================
# Terminal Colors (ANSI)
# =============================================================================


class Color:
    """ANSI color codes."""

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def cprint(msg: str, color: str = "", bold: bool = False) -> None:
    """Print with color."""
    prefix = ""
    if bold:
        prefix += Color.BOLD
    prefix += color
    suffix = Color.RESET if (color or bold) else ""
    print(f"{prefix}{msg}{suffix}")


def confirm(message: str, default: bool = False) -> bool:
    """Prompt user for confirmation.

    Args:
        message: The confirmation message to display
        default: Default value if user presses Enter without input

    Returns:
        True if user confirms, False otherwise
    """
    suffix = " [Y/n]" if default else " [y/N]"
    try:
        response = input(message + suffix + ": ")
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    if not response:
        return default
    return response.lower() in ("y", "yes")


# =============================================================================
# CLI Commands
# =============================================================================


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate the entries JSON file."""
    path = Path(args.json) if args.json else DEFAULT_JSON
    result = load_and_validate(path)

    print(result.summary())
    print()

    if result.errors:
        cprint("ERRORS:", Color.RED, bold=True)
        for idx, entry, error in result.errors:
            print(f"  Entry {idx}: {entry.get('name', 'UNKNOWN')}")
            print(f"    {error}")
        print()

    if result.duplicates:
        cprint("DUPLICATES:", Color.YELLOW, bold=True)
        for name, indices in result.duplicates:
            print(f"  '{name}' appears at entries: {indices}")
        print()

    if result.warnings:
        cprint("WARNINGS:", Color.YELLOW)
        for idx, entry, warning in result.warnings:
            print(f"  Entry {idx}: {entry.get('name', 'UNKNOWN')}: {warning}")

    if result.is_valid and not result.duplicates:
        cprint("Validation passed!", Color.GREEN, bold=True)
        return 0
    return 1


def _cmd_import_webloc(args: argparse.Namespace, json_file: Path, db_file: Path) -> int:
    """Handle webloc import (internal helper)."""
    directory = Path(args.webloc)

    if not args.category:
        cprint("Error: --category is required when using --webloc", Color.RED)
        return 1

    print(f"Scanning {directory} for .webloc files...")
    recursive = getattr(args, "recursive", False)
    result = scan_webloc_directory(directory, recursive=recursive)

    if result.error_count > 0:
        cprint(f"Encountered {result.error_count} errors:", Color.YELLOW)
        for path, error in result.errors[:5]:
            print(f"  {path}: {error}")
        if result.error_count > 5:
            print(f"  ... and {result.error_count - 5} more")
        print()

    if not result.entries:
        print("No .webloc files found.")
        return 0

    print(f"Found {result.success_count} .webloc files:")
    for entry in result.entries[:10]:
        github_marker = " [GitHub]" if entry.is_github else ""
        print(f"  {entry.name}{github_marker}")
    if len(result.entries) > 10:
        print(f"  ... and {len(result.entries) - 10} more")
    print()

    print(f"Importing {result.success_count} entries to category '{args.category}'...")

    no_github = getattr(args, "no_github", False)
    description = getattr(args, "description", None) or "Imported from webloc bookmark"
    imported, skipped, errors = import_webloc_entries(
        webloc_entries=result.entries,
        category=args.category,
        json_path=json_file,
        db_path=db_file,
        use_github_metadata=not no_github,
        default_description=description,
    )

    print()
    cprint("Import Results:", Color.BLUE, bold=True)
    print(f"  Imported: {imported}")
    print(f"  Skipped (duplicates): {skipped}")

    if errors:
        cprint(f"  Errors: {len(errors)}", Color.RED)
        for err in errors[:5]:
            print(f"    {err}")
        if len(errors) > 5:
            print(f"    ... and {len(errors) - 5} more")
        return 1

    cprint("Import complete.", Color.GREEN)
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    """Import entries from JSON to SQLite database, or from .webloc files."""
    json_file = Path(args.json) if args.json else DEFAULT_JSON
    db_file = Path(args.db) if args.db else DEFAULT_DB
    dry_run = getattr(args, "dry_run", False)
    force = getattr(args, "yes", False)

    # Webloc import mode
    if getattr(args, "webloc", None):
        return _cmd_import_webloc(args, json_file, db_file)

    if dry_run:
        cprint("[DRY RUN] No changes will be made", Color.YELLOW, bold=True)

    # Confirm if updating existing entries
    if args.update and not dry_run and not force:
        if not confirm("This will overwrite existing entries. Continue?"):
            print("Cancelled.")
            return 0

    print(f"Importing from {json_file} to {db_file}...")
    logger.info("Source JSON: %s", json_file)
    logger.info("Target DB: %s", db_file)
    imported, skipped, errors = import_from_json(
        json_file, db_file, not args.update, dry_run=dry_run
    )

    action = "Would import" if dry_run else "Imported"
    print(f"{action}: {imported}")
    print(f"Skipped: {skipped}")

    if errors:
        cprint("Errors:", Color.RED)
        for err in errors:
            print(f"  {err}")
        return 1

    if dry_run:
        cprint("[DRY RUN] Complete - no changes made", Color.YELLOW)
    else:
        cprint("Import complete.", Color.GREEN)
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Export entries from SQLite database to JSON."""
    db_file = Path(args.db) if args.db else DEFAULT_DB
    out_file = Path(args.output)
    source_json = Path(args.source_json) if getattr(args, "source_json", None) else None
    include_github = getattr(args, "include_github", False)

    count = export_to_json(
        db_file,
        out_file,
        source_json=source_json,
        include_github_metadata=include_github,
    )
    print(f"Exported {count} entries to {out_file}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List all entries in the database."""
    db_file = Path(args.db) if args.db else DEFAULT_DB

    if not db_file.exists():
        cprint(f"Database not found: {db_file}", Color.RED)
        print("Run 'linkdb import' first to create the database.")
        return 1

    # Build dynamic query with filters
    conditions: list[str] = []
    params: list[Any] = []

    if args.category:
        conditions.append("category LIKE ?")
        params.append(f"%{args.category}%")

    stars_min = getattr(args, "stars_min", None)
    if stars_min is not None:
        conditions.append("stars >= ?")
        params.append(stars_min)

    language = getattr(args, "language", None)
    if language:
        conditions.append("LOWER(language) = LOWER(?)")
        params.append(language)

    active_only = getattr(args, "active_only", False)
    if active_only:
        # Filter out archived repos and those with no push in 365+ days
        conditions.append("(archived IS NULL OR archived = 0)")
        conditions.append(
            "(last_pushed IS NULL OR julianday('now') - julianday(last_pushed) < 365)"
        )

    # Build WHERE clause
    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    with get_connection(db_file) as conn:
        cursor = conn.cursor()
        query = f"SELECT * FROM entry {where_clause} ORDER BY name"
        cursor.execute(query, params)
        rows = cursor.fetchall()

    if not rows:
        print("No entries found matching filters.")
        return 0

    # Determine if we should show extended columns
    show_extended = stars_min is not None or language or active_only

    if args.format == "json":
        data = [dict(row) for row in rows]
        print(json.dumps(data, indent=2))
    elif show_extended:
        # Extended format with stars and language
        print(
            f"{'Name':<25} {'Category':<15} {'Stars':>7} {'Language':<12} {'URL/Repo':<40}"
        )
        print("-" * 105)
        for r in rows:
            url = r["url"] or r["repo"] or ""
            if len(url) > 37:
                url = url[:37] + "..."
            stars = r["stars"] if r["stars"] is not None else "-"
            lang = r["language"] or "-"
            if len(lang) > 10:
                lang = lang[:10] + ".."
            print(
                f"{r['name']:<25} {r['category']:<15} {stars:>7} {lang:<12} {url:<40}"
            )
        print(f"\nTotal: {len(rows)} entries")
        if stars_min:
            total_stars = sum(r["stars"] or 0 for r in rows)
            print(f"Combined stars: {total_stars:,}")
    else:
        # Standard format
        print(f"{'Name':<30} {'Category':<20} {'URL/Repo':<50}")
        print("-" * 100)
        for r in rows:
            url = r["url"] or r["repo"] or ""
            if len(url) > 47:
                url = url[:47] + "..."
            print(f"{r['name']:<30} {r['category']:<20} {url:<50}")
        print(f"\nTotal: {len(rows)} entries")

    return 0


def cmd_search(args: argparse.Namespace) -> int:
    """Search entries by name or description."""
    db_file = Path(args.db) if args.db else DEFAULT_DB

    if not db_file.exists():
        cprint(f"Database not found: {db_file}", Color.RED)
        return 1

    with get_connection(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT * FROM entry WHERE name LIKE ? OR description LIKE ? OR category LIKE ?
               ORDER BY name""",
            (f"%{args.query}%", f"%{args.query}%", f"%{args.query}%"),
        )
        rows = cursor.fetchall()

    if not rows:
        print(f"No entries found matching '{args.query}'")
        return 0

    for r in rows:
        cprint(r["name"], Color.GREEN, bold=True)
        print(f"  Category: {r['category']}")
        print(f"  {r['description']}")
        if r["url"]:
            print(f"  URL: {r['url']}")
        if r["repo"]:
            print(f"  Repo: {r['repo']}")
        print()

    print(f"Found {len(rows)} entries matching '{args.query}'")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    """Show statistics about the database."""
    db_file = Path(args.db) if args.db else DEFAULT_DB

    if not db_file.exists():
        cprint(f"Database not found: {db_file}", Color.RED)
        return 1

    with get_connection(db_file) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM entry")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM entry WHERE url IS NOT NULL")
        with_url = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM entry WHERE repo IS NOT NULL")
        with_repo = cursor.fetchone()[0]

        cursor.execute(
            "SELECT category, COUNT(*) as cnt FROM entry GROUP BY category ORDER BY cnt DESC"
        )
        categories = cursor.fetchall()

    cprint("Database Statistics", Color.BLUE, bold=True)
    print(f"Total entries: {total}")
    print(f"With URL: {with_url}")
    print(f"With repo: {with_repo}")
    print()

    cprint("Categories:", Color.BLUE, bold=True)
    for row in categories:
        print(f"  {row['category']}: {row['cnt']}")

    return 0


def cmd_category_list(args: argparse.Namespace) -> int:
    """List all categories."""
    json_file = Path(args.json) if args.json else None
    categories = load_categories(json_file)

    cprint("Categories:", Color.BLUE, bold=True)
    for cat in sorted(categories):
        print(f"  {cat}")
    print(f"\nTotal: {len(categories)} categories")
    return 0


def cmd_category_add(args: argparse.Namespace) -> int:
    """Add a new category."""
    json_file = Path(args.json) if args.json else None
    name = normalize_category_input(args.name)

    categories = load_categories(json_file)
    if name in categories:
        cprint(f"Category '{name}' already exists", Color.YELLOW)
        return 1

    categories.add(name)
    save_categories(categories, json_file)
    cprint(f"Added category '{name}'", Color.GREEN)
    return 0


def cmd_category_rm(args: argparse.Namespace) -> int:
    """Remove a category."""
    json_file = Path(args.json) if args.json else None
    name = normalize_category_input(args.name)

    categories = load_categories(json_file)
    if name not in categories:
        cprint(f"Category '{name}' not found", Color.YELLOW)
        return 1

    # Check if category is in use
    entries = load_entries(json_file)
    in_use = [e["name"] for e in entries if e.get("category") == name]
    if in_use and not args.force:
        cprint(f"Category '{name}' is used by {len(in_use)} entries:", Color.RED)
        for entry_name in in_use[:5]:
            print(f"  {entry_name}")
        if len(in_use) > 5:
            print(f"  ... and {len(in_use) - 5} more")
        print("Use --force to remove anyway")
        return 1

    categories.remove(name)
    save_categories(categories, json_file)
    cprint(f"Removed category '{name}'", Color.GREEN)
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Check all URLs for broken links."""
    json_file = Path(args.json) if args.json else None
    entries = load_entries(json_file)

    if args.insecure:
        cprint(
            "Warning: SSL certificate verification disabled (--insecure)",
            Color.YELLOW,
        )

    print(f"Checking {len(entries)} entries...")

    def progress(current: int, total: int, name: str) -> None:
        print(f"  [{current}/{total}] {name}")

    results = run_check(
        entries, args.concurrency, args.timeout, progress, insecure=args.insecure
    )

    ok_count = 0
    redirect_count = 0
    issues = []

    for result in results:
        for link_result in [result.url_result, result.repo_result]:
            if link_result is None:
                continue
            if link_result.status == LinkStatus.OK:
                ok_count += 1
            elif link_result.status == LinkStatus.REDIRECT:
                redirect_count += 1
            elif link_result.status != LinkStatus.SKIPPED:
                issues.append((result.entry_name, link_result))

    print()
    cprint("Results:", Color.BLUE, bold=True)
    print(f"  OK: {ok_count}")
    print(f"  Redirects: {redirect_count}")
    print(f"  Issues: {len(issues)}")

    if issues:
        print()
        cprint("Issues found:", Color.RED, bold=True)
        for entry_name, link_result in issues:
            color = (
                Color.RED
                if link_result.status == LinkStatus.NOT_FOUND
                else Color.YELLOW
            )
            cprint(f"  {entry_name}", color)
            print(f"    URL: {link_result.url}")
            print(f"    Status: {link_result.status.value}")
            if link_result.error_message:
                print(f"    Error: {link_result.error_message}")
        return 1

    return 0


def cmd_github(args: argparse.Namespace) -> int:
    """Fetch GitHub statistics for all repositories."""
    json_file = Path(args.json) if args.json else None
    entries = load_entries(json_file)

    github_entries = [
        e for e in entries if e.get("repo") and "github.com" in e.get("repo", "")
    ]

    if not github_entries:
        print("No GitHub repositories found.")
        return 0

    token = get_github_token()
    if not token:
        cprint(
            "Warning: No GITHUB_TOKEN set. Rate limits will be strict.", Color.YELLOW
        )
        print("Set GITHUB_TOKEN or GH_TOKEN environment variable for higher limits.")
        print()

    use_cache = not getattr(args, "no_cache", False)
    db_file = Path(args.db) if args.db else DEFAULT_DB

    if use_cache:
        cache_stats = get_cache_stats(db_file)
        print(
            f"Fetching stats for {len(github_entries)} GitHub repos "
            f"(cache: {cache_stats['valid']} valid entries)..."
        )
    else:
        print(
            f"Fetching stats for {len(github_entries)} GitHub repos (cache disabled)..."
        )

    def progress(current: int, total: int, name: str) -> None:
        print(f"  [{current}/{total}] {name}")

    results = run_fetch_stats(
        entries, args.concurrency, progress, use_cache=use_cache, db_path=db_file
    )

    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    if not successful:
        cprint("No stats retrieved.", Color.RED)
        if failed:
            print("Errors:")
            for r in failed:
                print(f"  {r.entry_name}: {r.error}")
        return 1

    if args.sort == "stars":
        successful.sort(key=lambda r: r.stats.stars if r.stats else 0, reverse=True)
    elif args.sort == "activity":
        successful.sort(
            key=lambda r: (r.stats.days_since_push or 9999) if r.stats else 9999
        )
    else:
        successful.sort(key=lambda r: r.entry_name.lower())

    print()
    cprint("GitHub Statistics:", Color.BLUE, bold=True)
    print(f"{'Name':<25} {'Stars':>8} {'Forks':>7} {'Activity':<15} {'Language':<12}")
    print("-" * 75)

    for r in successful:
        s = r.stats
        if s is None:
            continue
        print(
            f"{r.entry_name:<25} {s.stars:>8} {s.forks:>7} "
            f"{s.activity_status:<15} {(s.language or 'N/A'):<12}"
        )
        if args.show_topics and s.topics:
            print(f"  Topics: {', '.join(s.topics)}")

    print()
    print(f"Total: {len(successful)} repos")
    total_stars = sum(r.stats.stars for r in successful if r.stats is not None)
    print(f"Combined stars: {total_stars:,}")

    stale = [
        r
        for r in successful
        if r.stats is not None and r.stats.activity_status in ("stale", "archived")
    ]
    if stale:
        print()
        cprint("Stale/Archived repos:", Color.YELLOW)
        for r in stale:
            if r.stats is None:
                continue
            days = r.stats.days_since_push
            print(
                f"  {r.entry_name}: {r.stats.activity_status} ({days} days since push)"
            )

    if failed:
        print()
        cprint(f"Failed to fetch {len(failed)} repos:", Color.RED)
        for r in failed:
            print(f"  {r.entry_name}: {r.error}")

    if args.update_db:
        db_file = Path(args.db) if args.db else DEFAULT_DB
        if not db_file.exists():
            cprint(f"Database not found: {db_file}", Color.RED)
            return 1

        with get_connection(db_file) as conn:
            cursor = conn.cursor()
            updated = 0
            for r in successful:
                if r.stats is not None and r.stats.topics:
                    cursor.execute(
                        "UPDATE entry SET keywords = ? WHERE name = ?",
                        (", ".join(r.stats.topics), r.entry_name),
                    )
                    if cursor.rowcount > 0:
                        updated += 1
            conn.commit()
        print()
        cprint(f"Updated {updated} entries with topics in database", Color.GREEN)

    return 0


def cmd_github_help(args: argparse.Namespace) -> int:
    """Show help for github command."""
    print("Usage: linkdb github <command>")
    print()
    print("Commands:")
    print("  fetch   Fetch GitHub statistics (default)")
    print("  stale   Find stale/unmaintained projects")
    print("  cache   Manage GitHub API response cache")
    print()
    print("Run 'linkdb github <command> --help' for more information.")
    return 0


def cmd_cache(args: argparse.Namespace) -> int:
    """Manage the GitHub API response cache."""
    db_file = Path(args.db) if args.db else DEFAULT_DB

    if args.cache_action == "stats":
        stats = get_cache_stats(db_file)
        cprint("GitHub Cache Statistics:", Color.BLUE, bold=True)
        print(f"  Total entries: {stats['total']}")
        print(f"  Valid entries: {stats['valid']}")
        print(f"  Expired entries: {stats['expired']}")
        if stats.get("oldest"):
            print(f"  Oldest entry: {stats['oldest']}")
        if stats.get("newest"):
            print(f"  Newest entry: {stats['newest']}")
        return 0

    elif args.cache_action == "clear":
        expired_only = not args.all
        if not expired_only and not args.force:
            response = input("Clear ALL cached responses? [y/N]: ")
            if response.lower() not in ("y", "yes"):
                print("Cancelled.")
                return 0
        cleared = clear_github_cache(db_file, expired_only=expired_only)
        if expired_only:
            cprint(f"Cleared {cleared} expired cache entries", Color.GREEN)
        else:
            cprint(f"Cleared {cleared} cache entries", Color.GREEN)
        return 0

    return 0


@dataclass
class DiagnosticResult:
    """Result of a single diagnostic check."""

    status: str  # "OK", "WARN", "ERR"
    message: str
    details: list[str] = field(default_factory=list)


def cmd_doctor(args: argparse.Namespace) -> int:
    """Run diagnostics to check data health."""
    json_file = Path(args.json) if args.json else DEFAULT_JSON
    db_file = Path(args.db) if args.db else DEFAULT_DB

    results: list[DiagnosticResult] = []

    cprint("Checking data integrity...", Color.BLUE, bold=True)
    print()

    # 1. Check JSON syntax and structure
    try:
        data = load_data(json_file)
        entries = data.get("entries", [])
        results.append(DiagnosticResult("OK", "JSON syntax valid"))
    except json.JSONDecodeError as e:
        results.append(DiagnosticResult("ERR", f"JSON syntax error: {e}"))
        entries = []
    except FileNotFoundError:
        results.append(DiagnosticResult("ERR", f"JSON file not found: {json_file}"))
        entries = []

    # 2. Check required fields
    missing_fields: list[str] = []
    for entry in entries:
        name = entry.get("name", "<unknown>")
        if not entry.get("name"):
            missing_fields.append(f"{name}: missing name")
        if not entry.get("category"):
            missing_fields.append(f"{name}: missing category")
        if not entry.get("url") and not entry.get("repo"):
            missing_fields.append(f"{name}: missing url or repo")

    if missing_fields:
        results.append(
            DiagnosticResult(
                "ERR",
                f"{len(missing_fields)} entries missing required fields",
                missing_fields[:10],  # Show first 10
            )
        )
    else:
        results.append(DiagnosticResult("OK", "All entries have required fields"))

    # 3. Check for missing descriptions
    missing_desc = [e["name"] for e in entries if not e.get("description")]
    if missing_desc:
        results.append(
            DiagnosticResult(
                "WARN",
                f"{len(missing_desc)} entries missing descriptions",
                missing_desc[:5],
            )
        )
    else:
        results.append(DiagnosticResult("OK", "All entries have descriptions"))

    # 4. Check for duplicate URLs
    url_counts: dict[str, list[str]] = defaultdict(list)
    for entry in entries:
        for url_field in ["url", "repo"]:
            url = entry.get(url_field)
            if url:
                url_counts[url].append(entry.get("name", "unknown"))

    duplicate_urls = [
        (url, names) for url, names in url_counts.items() if len(names) > 1
    ]
    if duplicate_urls:
        details = [f"{url}: {', '.join(names)}" for url, names in duplicate_urls[:5]]
        results.append(
            DiagnosticResult(
                "ERR", f"{len(duplicate_urls)} duplicate URLs detected", details
            )
        )
    else:
        results.append(DiagnosticResult("OK", "No duplicate URLs"))

    # 5. Check for duplicate names
    name_counts: dict[str, int] = defaultdict(int)
    for entry in entries:
        name_counts[entry.get("name", "")] += 1

    duplicate_names = [
        name for name, count in name_counts.items() if count > 1 and name
    ]
    if duplicate_names:
        results.append(
            DiagnosticResult(
                "ERR",
                f"{len(duplicate_names)} duplicate entry names",
                duplicate_names[:5],
            )
        )
    else:
        results.append(DiagnosticResult("OK", "No duplicate entry names"))

    # 6. Check database exists and schema is up to date
    if db_file.exists():
        try:
            with get_connection(db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(entry)")
                columns = {row[1] for row in cursor.fetchall()}

                # Check for migration columns
                expected_cols = {"tags", "aliases", "mirror_urls", "stars", "forks"}
                missing_cols = expected_cols - columns
                if missing_cols:
                    results.append(
                        DiagnosticResult(
                            "WARN",
                            f"Database missing columns: {', '.join(missing_cols)}",
                            ["Run 'linkdb import' to migrate"],
                        )
                    )
                else:
                    results.append(DiagnosticResult("OK", "Database schema up to date"))

                # Count DB entries
                cursor.execute("SELECT COUNT(*) FROM entry")
                db_count = cursor.fetchone()[0]

                # Compare with JSON
                if db_count != len(entries):
                    results.append(
                        DiagnosticResult(
                            "WARN",
                            f"Entry count mismatch: JSON={len(entries)}, DB={db_count}",
                            ["Consider running 'linkdb import --update'"],
                        )
                    )
        except sqlite3.Error as e:
            results.append(DiagnosticResult("ERR", f"Database error: {e}"))
    else:
        results.append(
            DiagnosticResult(
                "WARN",
                f"Database not found: {db_file}",
                ["Run 'linkdb import' to create"],
            )
        )

    # 7. Check for repositories not checked recently (30+ days)
    if db_file.exists():
        try:
            with get_connection(db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT name FROM entry
                    WHERE repo IS NOT NULL
                    AND (last_checked IS NULL
                         OR last_checked < datetime('now', '-30 days'))"""
                )
                old_checks = [row[0] for row in cursor.fetchall()]
                if old_checks:
                    results.append(
                        DiagnosticResult(
                            "WARN",
                            f"{len(old_checks)} repositories not checked in 30+ days",
                            old_checks[:5] + (["..."] if len(old_checks) > 5 else []),
                        )
                    )
                else:
                    results.append(
                        DiagnosticResult("OK", "All repositories checked recently")
                    )
        except sqlite3.Error:
            pass  # Skip if table doesn't exist yet

    # 8. Check category consistency
    categories = load_categories(json_file)
    used_categories = {e.get("category") for e in entries if e.get("category")}
    undefined_categories = used_categories - categories - {""}
    if undefined_categories and categories:  # Only warn if categories are defined
        results.append(
            DiagnosticResult(
                "WARN",
                f"{len(undefined_categories)} categories used but not defined",
                list(undefined_categories)[:5],
            )
        )

    # Display results
    errors = 0
    warnings = 0
    for result in results:
        if result.status == "OK":
            prefix = f"  {Color.GREEN}[OK]{Color.RESET}"
        elif result.status == "WARN":
            prefix = f"  {Color.YELLOW}[WARN]{Color.RESET}"
            warnings += 1
        else:
            prefix = f"  {Color.RED}[ERR]{Color.RESET}"
            errors += 1

        print(f"{prefix} {result.message}")
        for detail in result.details:
            print(f"        {detail}")

    print()
    if errors > 0:
        cprint(f"Found {errors} error(s) and {warnings} warning(s)", Color.RED)
        return 1
    elif warnings > 0:
        cprint(f"Found {warnings} warning(s)", Color.YELLOW)
        return 0
    else:
        cprint("All checks passed!", Color.GREEN)
        return 0


def cmd_stale(args: argparse.Namespace) -> int:
    """Find stale/unmaintained projects using GitHub data."""
    json_file = Path(args.json) if args.json else None
    entries = load_entries(json_file)

    github_entries = [
        e for e in entries if e.get("repo") and "github.com" in e.get("repo", "")
    ]

    if not github_entries:
        print("No GitHub repositories found.")
        return 0

    token = get_github_token()
    if not token:
        cprint(
            "Warning: No GITHUB_TOKEN set. Rate limits will be strict.", Color.YELLOW
        )
        print()

    print(f"Checking {len(github_entries)} GitHub repos for staleness...")

    def progress(current: int, total: int, name: str) -> None:
        print(f"  [{current}/{total}] {name}")

    results = run_fetch_stats(entries, args.concurrency, progress)

    stale_repos: list[RepoResult] = []
    archived_repos: list[RepoResult] = []
    active_repos: list[RepoResult] = []

    for r in results:
        if not r.success or r.stats is None:
            continue
        if r.stats.archived:
            archived_repos.append(r)
        elif r.stats.days_since_push and r.stats.days_since_push > args.days:
            stale_repos.append(r)
        else:
            active_repos.append(r)

    stale_repos.sort(
        key=lambda r: (r.stats.days_since_push or 0) if r.stats else 0, reverse=True
    )

    print()
    cprint("Results:", Color.BLUE, bold=True)
    print(f"  Active: {len(active_repos)}")
    print(f"  Stale (>{args.days} days): {len(stale_repos)}")
    print(f"  Archived: {len(archived_repos)}")

    if archived_repos:
        print()
        cprint("Archived repositories:", Color.RED, bold=True)
        for r in archived_repos:
            print(f"  {r.entry_name}")
            print(f"    {r.repo_url}")

    if stale_repos:
        print()
        cprint(
            f"Stale repositories (>{args.days} days since push):",
            Color.YELLOW,
            bold=True,
        )
        for r in stale_repos:
            if r.stats is None:
                continue
            print(f"  {r.entry_name}: {r.stats.days_since_push} days ago")
            print(f"    {r.repo_url}")

    total_checked = len(active_repos) + len(stale_repos) + len(archived_repos)
    if total_checked > 0:
        health_pct = len(active_repos) / total_checked * 100
        print()
        print(f"Repository health: {health_pct:.1f}% active")

    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    """Generate README.md from database."""
    db_file = Path(args.db) if args.db else DEFAULT_DB

    if not db_file.exists():
        cprint(f"Database not found: {db_file}", Color.RED)
        print("Run 'linkdb import' first to create the database.")
        return 1

    template = Path(args.template) if args.template else None
    output = Path(args.output) if args.output else None
    force = getattr(args, "force", False)

    content = generate_readme(db_file, template, output, force=force)

    if output:
        cprint(f"Generated README at {output}", Color.GREEN)
    else:
        print(content)

    return 0


def cmd_sort(args: argparse.Namespace) -> int:
    """Sort entries.json file."""
    json_file = Path(args.json) if args.json else None
    by_category = args.by_category

    num_categories, num_entries = sort_entries_file(json_file, by_category=by_category)

    sort_desc = "by category, then name" if by_category else "by name"
    cprint(
        f"Sorted {num_categories} categories and {num_entries} entries ({sort_desc})",
        Color.GREEN,
    )
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    """Add a new entry to the JSON file and sync to database."""
    json_file = Path(args.json) if args.json else None
    db_file = Path(args.db) if args.db else None

    # Batch mode: add from file
    if getattr(args, "file", None):
        return _cmd_add_from_file(args, json_file, db_file)

    # Interactive mode
    if getattr(args, "interactive", False):
        try:
            entry = interactive_add(json_path=json_file, db_path=db_file)
            if entry:
                cprint(f"Added '{entry['name']}'", Color.GREEN)
                return 0
            return 1
        except (ValueError, KeyError) as e:
            cprint(str(e), Color.RED)
            return 1

    # Category is required in non-interactive mode
    if not args.category:
        cprint("Error: --category is required (or use --interactive mode)", Color.RED)
        return 1

    # Check if repo is a GitHub URL and we're missing name/description
    is_github = args.repo and "github.com" in args.repo
    needs_github_fetch = is_github and (not args.name or not args.description)

    if needs_github_fetch:
        print(f"Fetching metadata from {args.repo}...")
        try:
            entry = add_entry_from_github(
                github_url=args.repo,
                category=args.category,
                name=args.name,
                desc=args.description,
                json_path=json_file,
                db_path=db_file,
                sync=True,
            )
            cprint(f"Added '{entry['name']}'", Color.GREEN)
            print(f"  Category: {entry['category']}")
            print(f"  Description: {entry['desc']}")
            if entry.get("url"):
                print(f"  URL: {entry['url']}")
            print(f"  Repo: {entry['repo']}")

            # Show GitHub metadata
            db_path = db_file or DEFAULT_DB
            if db_path.exists():
                with get_connection(db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT * FROM entry WHERE name = ?", (entry["name"],)
                    )
                    row = cursor.fetchone()
                    if row:
                        if row["stars"] is not None:
                            print(f"  Stars: {row['stars']}")
                        if row["forks"] is not None:
                            print(f"  Forks: {row['forks']}")
                        if row["language"]:
                            print(f"  Language: {row['language']}")
                        if row["license"]:
                            print(f"  License: {row['license']}")
                        if row["keywords"]:
                            print(f"  Keywords: {row['keywords']}")
            return 0
        except (ValueError, KeyError) as e:
            cprint(str(e), Color.RED)
            return 1

    # Standard add (non-GitHub or all fields provided)
    if not args.name:
        cprint(
            "Error: --name is required (or use a GitHub URL for -r to auto-detect)",
            Color.RED,
        )
        return 1
    if not args.description:
        cprint(
            "Error: --description is required (or use a GitHub URL for -r to auto-detect)",
            Color.RED,
        )
        return 1

    try:
        entry = add_entry(
            name=args.name,
            category=args.category,
            desc=args.description,
            url=args.url,
            repo=args.repo,
            json_path=json_file,
            db_path=db_file,
            sync=True,
        )
        cprint(f"Added '{entry['name']}'", Color.GREEN)
        return 0
    except (ValueError, KeyError) as e:
        cprint(str(e), Color.RED)
        return 1


def cmd_remove(args: argparse.Namespace) -> int:
    """Remove an entry from the JSON file and database."""
    json_file = Path(args.json) if args.json else None
    db_file = Path(args.db) if args.db else None
    dry_run = getattr(args, "dry_run", False)

    # Category removal mode
    if getattr(args, "category", None):
        return _cmd_remove_category(args, json_file, db_file, dry_run)

    # Single entry mode requires name
    if not args.name:
        cprint("Error: entry name required (or use --category)", Color.RED)
        return 1

    # Show entry info before removing
    entry = get_entry(args.name, json_file)
    if not entry:
        cprint(f"Entry '{args.name}' not found", Color.YELLOW)
        return 1

    if dry_run:
        cprint("[DRY RUN] Would remove:", Color.YELLOW, bold=True)
    else:
        print("Entry to remove:")

    print(f"  Name: {entry['name']}")
    print(f"  Category: {entry['category']}")
    print(f"  Description: {entry['desc']}")
    if entry.get("url"):
        print(f"  URL: {entry['url']}")
    if entry.get("repo"):
        print(f"  Repo: {entry['repo']}")

    if dry_run:
        cprint("[DRY RUN] No changes made", Color.YELLOW)
        return 0

    if not args.yes:
        confirm = input("Remove this entry? [y/N] ")
        if confirm.lower() != "y":
            print("Cancelled")
            return 0

    try:
        removed = remove_entry(
            name=args.name,
            json_path=json_file,
            db_path=db_file,
            sync=True,
        )
        cprint(f"Removed '{removed['name']}'", Color.GREEN)
        return 0
    except KeyError as e:
        cprint(str(e), Color.RED)
        return 1


def _cmd_add_from_file(
    args: argparse.Namespace, json_file: Optional[Path], db_file: Optional[Path]
) -> int:
    """Handle batch add from file (internal helper)."""
    dry_run = getattr(args, "dry_run", False)

    if not args.category:
        cprint("Error: --category is required when using --file", Color.RED)
        return 1

    file_path = Path(args.file)
    if not file_path.exists():
        cprint(f"File not found: {file_path}", Color.RED)
        return 1

    with open(file_path) as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not urls:
        print("No URLs found in file")
        return 0

    if dry_run:
        cprint(f"[DRY RUN] Would process {len(urls)} URLs", Color.YELLOW, bold=True)
    else:
        print(f"Processing {len(urls)} URLs...")

    result = add_many_entries(
        urls=urls,
        category=args.category,
        json_path=json_file,
        db_path=db_file,
        dry_run=dry_run,
    )

    # Report results
    if result.added:
        action = "Would add" if dry_run else "Added"
        cprint(f"{action} {len(result.added)} entries:", Color.GREEN)
        for name in result.added[:10]:
            print(f"  {name}")
        if len(result.added) > 10:
            print(f"  ... and {len(result.added) - 10} more")

    if result.skipped:
        cprint(f"Skipped {len(result.skipped)} entries:", Color.YELLOW)
        for url, reason in result.skipped[:5]:
            print(f"  {url}: {reason}")
        if len(result.skipped) > 5:
            print(f"  ... and {len(result.skipped) - 5} more")

    if result.errors:
        cprint(f"Errors ({len(result.errors)}):", Color.RED)
        for url, error in result.errors[:5]:
            print(f"  {url}: {error}")
        if len(result.errors) > 5:
            print(f"  ... and {len(result.errors) - 5} more")
        return 1

    if dry_run:
        cprint("[DRY RUN] No changes made", Color.YELLOW)
    return 0


def cmd_add_many(args: argparse.Namespace) -> int:
    """Add multiple entries from a file (deprecated, use 'add --file')."""
    json_file = Path(args.json) if args.json else None
    db_file = Path(args.db) if args.db else None
    dry_run = getattr(args, "dry_run", False)

    # Read URLs from file
    file_path = Path(args.file)
    if not file_path.exists():
        cprint(f"File not found: {file_path}", Color.RED)
        return 1

    with open(file_path) as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not urls:
        print("No URLs found in file")
        return 0

    if dry_run:
        cprint(f"[DRY RUN] Would process {len(urls)} URLs", Color.YELLOW, bold=True)
    else:
        print(f"Processing {len(urls)} URLs...")

    result = add_many_entries(
        urls=urls,
        category=args.category,
        json_path=json_file,
        db_path=db_file,
        dry_run=dry_run,
    )

    # Report results
    if result.added:
        action = "Would add" if dry_run else "Added"
        cprint(f"{action} {len(result.added)} entries:", Color.GREEN)
        for name in result.added[:10]:
            print(f"  {name}")
        if len(result.added) > 10:
            print(f"  ... and {len(result.added) - 10} more")

    if result.skipped:
        cprint(f"Skipped {len(result.skipped)} entries:", Color.YELLOW)
        for url, reason in result.skipped[:5]:
            print(f"  {url}: {reason}")
        if len(result.skipped) > 5:
            print(f"  ... and {len(result.skipped) - 5} more")

    if result.errors:
        cprint(f"Errors ({len(result.errors)}):", Color.RED)
        for url, error in result.errors[:5]:
            print(f"  {url}: {error}")
        if len(result.errors) > 5:
            print(f"  ... and {len(result.errors) - 5} more")
        return 1

    print()
    if dry_run:
        cprint("[DRY RUN] Complete - no changes made", Color.YELLOW)
    else:
        cprint(
            f"Batch add complete: {len(result.added)} added, "
            f"{len(result.skipped)} skipped",
            Color.GREEN,
        )
    return 0


def _cmd_remove_category(
    args: argparse.Namespace,
    json_file: Optional[Path],
    db_file: Optional[Path],
    dry_run: bool,
) -> int:
    """Handle category removal (internal helper)."""
    result = remove_entries_by_category(
        category=args.category,
        json_path=json_file,
        db_path=db_file,
        dry_run=True,  # Always preview first
    )

    if not result.entries_to_remove:
        print(f"No entries found in category '{args.category}'")
        return 0

    action = "Would remove" if dry_run else "Entries to remove"
    cprint(
        f"{action} {len(result.entries_to_remove)} entries:", Color.YELLOW, bold=True
    )
    for entry in result.entries_to_remove[:10]:
        print(f"  {entry['name']}")
    if len(result.entries_to_remove) > 10:
        print(f"  ... and {len(result.entries_to_remove) - 10} more")

    if dry_run:
        print()
        cprint("[DRY RUN] No changes made", Color.YELLOW)
        return 0

    if not args.yes:
        user_confirm = input(
            f"Remove all {len(result.entries_to_remove)} entries "
            f"in category '{args.category}'? [y/N] "
        )
        if user_confirm.lower() != "y":
            print("Cancelled")
            return 0

    # Actually remove
    result = remove_entries_by_category(
        category=args.category,
        json_path=json_file,
        db_path=db_file,
        dry_run=False,
    )

    cprint(f"Removed {len(result.removed)} entries", Color.GREEN)
    return 0


def cmd_dedupe(args: argparse.Namespace) -> int:
    """Find and optionally merge duplicate entries."""
    json_file = Path(args.json) if args.json else None
    db_file = Path(args.db) if args.db else None
    dry_run = getattr(args, "dry_run", False)
    auto_merge = getattr(args, "merge", False)

    result = find_duplicates(json_file)

    if not result.has_duplicates:
        cprint("No duplicates found!", Color.GREEN)
        return 0

    print(
        f"Found {len(result.duplicate_groups)} duplicate groups "
        f"({result.total_duplicates} duplicate entries):\n"
    )

    total_removed = 0

    for i, group in enumerate(result.duplicate_groups, 1):
        primary = group.primary
        duplicates = group.duplicates

        cprint(
            f"Group {i}: {group.key_type.upper()} duplicate", Color.YELLOW, bold=True
        )
        print(f"  {group.key}")
        print()
        cprint("  Keep (most complete):", Color.GREEN)
        print(f"    Name: {primary['name']}")
        print(f"    Category: {primary['category']}")
        print(f"    Description: {primary.get('desc', '')[:60]}...")
        if primary.get("url"):
            print(f"    URL: {primary['url']}")
        if primary.get("repo"):
            print(f"    Repo: {primary['repo']}")

        cprint(f"  Remove ({len(duplicates)}):", Color.RED)
        for dup in duplicates:
            print(f"    - {dup['name']} ({dup['category']})")
        print()

        if dry_run:
            total_removed += len(duplicates)
            continue

        if auto_merge:
            removed = merge_duplicates(group, json_file, db_file, dry_run=False)
            total_removed += len(removed)
            cprint(f"  Merged: removed {len(removed)} duplicates", Color.GREEN)
        else:
            # Interactive mode - ask for each group
            confirm = input("  Merge this group (remove duplicates)? [y/N]: ").strip()
            if confirm.lower() == "y":
                removed = merge_duplicates(group, json_file, db_file, dry_run=False)
                total_removed += len(removed)
                cprint(f"  Merged: removed {len(removed)} duplicates", Color.GREEN)
            else:
                print("  Skipped")
        print()

    if dry_run:
        print()
        cprint(
            f"[DRY RUN] Would remove {total_removed} duplicate entries", Color.YELLOW
        )
    elif total_removed > 0:
        print()
        cprint(f"Removed {total_removed} duplicate entries", Color.GREEN)
    else:
        print("No duplicates were removed")

    return 0


def cmd_backup_help(args: argparse.Namespace) -> int:
    """Show help for backup command."""
    print("Usage: linkdb backup <command>")
    print()
    print("Commands:")
    print("  create   Create a new backup")
    print("  restore  Restore from a backup")
    print("  list     List available backups")
    print()
    print("Run 'linkdb backup <command> --help' for more information.")
    return 0


def cmd_backup_list(args: argparse.Namespace) -> int:
    """List available backups."""
    backup_dir = (
        Path(args.backup_dir) if args.backup_dir else DEFAULT_JSON.parent / "backups"
    )

    if not backup_dir.exists():
        print(f"No backups found (directory doesn't exist: {backup_dir})")
        return 0

    backups = sorted(backup_dir.glob("linkdb-*.tar.gz"), reverse=True)
    if not backups:
        print(f"No backups found in {backup_dir}")
        return 0

    cprint("Available backups:", Color.BLUE, bold=True)
    for backup in backups:
        size_kb = backup.stat().st_size / 1024
        print(f"  {backup.name} ({size_kb:.1f} KB)")

    print()
    print("To restore: linkdb backup restore <filename>")
    return 0


def cmd_backup(args: argparse.Namespace) -> int:
    """Create a backup of JSON and database files."""
    json_file = Path(args.json) if args.json else None
    db_file = Path(args.db) if args.db else None
    backup_dir = Path(args.backup_dir) if args.backup_dir else None

    try:
        backup_path = create_backup(json_file, db_file, backup_dir)
        cprint(f"Backup created: {backup_path}", Color.GREEN)

        # Show backup contents
        with tarfile.open(backup_path, "r:gz") as tar:
            print("Contents:")
            for member in tar.getmembers():
                size_kb = member.size / 1024
                print(f"  {member.name} ({size_kb:.1f} KB)")

        return 0
    except Exception as e:
        cprint(f"Backup failed: {e}", Color.RED)
        return 1


def cmd_restore(args: argparse.Namespace) -> int:
    """Restore from a backup."""
    json_file = Path(args.json) if args.json else None
    db_file = Path(args.db) if args.db else None
    dry_run = getattr(args, "dry_run", False)

    # If no backup specified, list available backups
    if not args.backup:
        backup_dir = Path(args.backup_dir) if args.backup_dir else None
        backups = list_backups(backup_dir)

        if not backups:
            print("No backups found.")
            return 0

        cprint("Available backups:", Color.BLUE, bold=True)
        for i, b in enumerate(backups, 1):
            contents = []
            if b.has_json:
                contents.append("JSON")
            if b.has_db:
                contents.append("DB")
            date_str = b.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            print(f"  {i}. {b.name} ({date_str}) [{', '.join(contents)}]")

        print("\nTo restore, run: linkdb restore <backup_name>")
        return 0

    # Find the backup
    backup_path = Path(args.backup)
    if not backup_path.exists():
        # Try in default backup dir
        backup_dir = Path(args.backup_dir) if args.backup_dir else DEFAULT_BACKUP_DIR
        backup_path = backup_dir / args.backup
        if not backup_path.exists():
            cprint(f"Backup not found: {args.backup}", Color.RED)
            return 1

    if dry_run:
        cprint("[DRY RUN] Would restore from:", Color.YELLOW, bold=True)
    else:
        print("Restoring from:")
    print(f"  {backup_path}")

    # Show what's in the backup
    with tarfile.open(backup_path, "r:gz") as tar:
        print("  Contents:")
        for member in tar.getmembers():
            print(f"    {member.name}")

    if dry_run:
        cprint("[DRY RUN] No changes made", Color.YELLOW)
        return 0

    if not args.yes:
        cprint("Warning: This will overwrite existing data!", Color.YELLOW)
        confirm = input("Continue? [y/N]: ").strip()
        if confirm.lower() != "y":
            print("Cancelled")
            return 0

    json_restored, db_restored = restore_backup(backup_path, json_file, db_file)

    restored = []
    if json_restored:
        restored.append("JSON")
    if db_restored:
        restored.append("database")

    if restored:
        cprint(f"Restored: {', '.join(restored)}", Color.GREEN)
    else:
        print("Nothing to restore")

    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    """Show history of changes."""
    db_file = Path(args.db) if args.db else None

    # Parse since date if provided
    since = None
    if args.since:
        try:
            since = datetime.fromisoformat(args.since)
        except ValueError:
            # Try other formats
            for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y/%m/%d"]:
                try:
                    since = datetime.strptime(args.since, fmt)
                    break
                except ValueError:
                    continue
            if since is None:
                cprint(f"Invalid date format: {args.since}", Color.RED)
                print("Use ISO format (YYYY-MM-DD) or YYYY-MM-DD HH:MM")
                return 1

    # Get history
    entries = get_history(
        db_path=db_file,
        since=since,
        action=args.action,
        limit=args.limit,
    )

    if not entries:
        if since:
            print(f"No changes since {since.strftime('%Y-%m-%d %H:%M')}")
        else:
            print("No history recorded yet.")
        return 0

    # Group by date for display
    cprint("Change History:", Color.BLUE, bold=True)
    if since:
        print(f"Since: {since.strftime('%Y-%m-%d %H:%M')}")
    print()

    current_date = None
    for entry in entries:
        entry_date = entry.timestamp.strftime("%Y-%m-%d")
        if entry_date != current_date:
            current_date = entry_date
            cprint(f"  {entry_date}", Color.BLUE)

        time_str = entry.timestamp.strftime("%H:%M:%S")
        action_color = {
            "add": Color.GREEN,
            "remove": Color.RED,
            "update": Color.YELLOW,
        }.get(entry.action, "")

        action_str = f"[{entry.action.upper():^7}]"
        cprint(f"    {time_str} {action_str}", action_color, bold=False)
        print(f" {entry.entry_name}", end="")
        if entry.category:
            print(f" ({entry.category})", end="")
        print()
        if entry.details and args.verbose:
            print(f"             {entry.details}")

    print()
    print(f"Total: {len(entries)} changes")

    # Summary
    adds = sum(1 for e in entries if e.action == "add")
    removes = sum(1 for e in entries if e.action == "remove")
    updates = sum(1 for e in entries if e.action == "update")
    print(f"  Added: {adds}, Removed: {removes}, Updated: {updates}")

    return 0


def cmd_history_combined(args: argparse.Namespace) -> int:
    """Show change history (combined diff and per-entry history)."""
    db_file = Path(args.db) if args.db else None

    # If entry name provided, show history for that entry
    if getattr(args, "entry", None):
        return _cmd_history_entry(args, db_file)

    # Otherwise show general diff history
    return _cmd_history_diff(args, db_file)


def _cmd_history_entry(args: argparse.Namespace, db_file: Optional[Path]) -> int:
    """Show history for a specific entry (internal helper)."""
    entries = get_entry_history(args.entry, db_file)

    if not entries:
        print(f"No history found for '{args.entry}'")
        return 0

    cprint(f"History for '{args.entry}':", Color.BLUE, bold=True)
    print()

    for entry in entries:
        date_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        action_color = {
            "add": Color.GREEN,
            "remove": Color.RED,
            "update": Color.YELLOW,
        }.get(entry.action, "")

        cprint(f"  {date_str} [{entry.action.upper()}]", action_color)
        if entry.details:
            print(f"    {entry.details}")

    return 0


def _cmd_history_diff(args: argparse.Namespace, db_file: Optional[Path]) -> int:
    """Show general change history (internal helper)."""
    # Parse since date if provided
    since = None
    if getattr(args, "since", None):
        try:
            since = datetime.fromisoformat(args.since)
        except ValueError:
            for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y/%m/%d"]:
                try:
                    since = datetime.strptime(args.since, fmt)
                    break
                except ValueError:
                    continue
            if since is None:
                cprint(f"Invalid date format: {args.since}", Color.RED)
                print("Use ISO format (YYYY-MM-DD) or YYYY-MM-DD HH:MM")
                return 1

    action = getattr(args, "action", None)
    limit = getattr(args, "limit", 100)
    show_details = getattr(args, "details", False)

    entries = get_history(db_path=db_file, since=since, action=action, limit=limit)

    if not entries:
        if since:
            print(f"No changes since {since.strftime('%Y-%m-%d %H:%M')}")
        else:
            print("No history recorded yet.")
        return 0

    cprint("Change History:", Color.BLUE, bold=True)
    if since:
        print(f"Since: {since.strftime('%Y-%m-%d %H:%M')}")
    print()

    current_date = None
    for entry in entries:
        entry_date = entry.timestamp.strftime("%Y-%m-%d")
        if entry_date != current_date:
            current_date = entry_date
            cprint(f"  {entry_date}", Color.BLUE)

        time_str = entry.timestamp.strftime("%H:%M:%S")
        action_color = {
            "add": Color.GREEN,
            "remove": Color.RED,
            "update": Color.YELLOW,
        }.get(entry.action, "")

        cprint(
            f"    {time_str} [{entry.action.upper()}] {entry.entry_name}", action_color
        )
        if entry.category:
            print(f"      Category: {entry.category}")
        if show_details and entry.details:
            print(f"      Details: {entry.details}")

    print()
    print(f"Showing {len(entries)} of latest changes")
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    """Show history for a specific entry (deprecated, use 'history <entry>')."""
    db_file = Path(args.db) if args.db else None

    entries = get_entry_history(args.name, db_file)

    if not entries:
        print(f"No history found for '{args.name}'")
        return 0

    cprint(f"History for '{args.name}':", Color.BLUE, bold=True)
    print()

    for entry in entries:
        date_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        action_color = {
            "add": Color.GREEN,
            "remove": Color.RED,
            "update": Color.YELLOW,
        }.get(entry.action, "")

        cprint(f"  {date_str} [{entry.action.upper()}]", action_color)
        if entry.details:
            print(f"    {entry.details}")

    return 0


def cmd_update(args: argparse.Namespace) -> int:
    """Update an existing entry in the JSON file and sync to database."""
    json_file = Path(args.json) if args.json else None
    db_file = Path(args.db) if args.db else None

    # Show current entry info
    entry = get_entry(args.name, json_file)
    if not entry:
        cprint(f"Entry '{args.name}' not found", Color.YELLOW)
        return 1

    print("Current entry:")
    print(f"  Name: {entry['name']}")
    print(f"  Category: {entry['category']}")
    print(f"  Description: {entry['desc']}")
    if entry.get("url"):
        print(f"  URL: {entry['url']}")
    if entry.get("repo"):
        print(f"  Repo: {entry['repo']}")
    print()

    try:
        updated = update_entry(
            name=args.name,
            category=args.category,
            desc=args.description,
            url=args.url,
            repo=args.repo,
            json_path=json_file,
            db_path=db_file,
            sync=True,
        )
        cprint(f"Updated '{updated['name']}'", Color.GREEN)
        print("\nUpdated entry:")
        print(f"  Name: {updated['name']}")
        print(f"  Category: {updated['category']}")
        print(f"  Description: {updated['desc']}")
        if updated.get("url"):
            print(f"  URL: {updated['url']}")
        if updated.get("repo"):
            print(f"  Repo: {updated['repo']}")
        return 0
    except (ValueError, KeyError) as e:
        cprint(str(e), Color.RED)
        return 1


def cmd_scan_webloc(args: argparse.Namespace) -> int:
    """Scan a directory for .webloc files and optionally import them."""
    directory = Path(args.directory)
    json_file = Path(args.json) if args.json else None
    db_file = Path(args.db) if args.db else None

    print(f"Scanning {directory} for .webloc files...")
    result = scan_webloc_directory(directory, recursive=args.recursive)

    if result.error_count > 0:
        cprint(f"Encountered {result.error_count} errors:", Color.YELLOW)
        for path, error in result.errors:
            print(f"  {path}: {error}")
        print()

    if not result.entries:
        print("No .webloc files found.")
        return 0

    print(f"Found {result.success_count} .webloc files:")
    for entry in result.entries:
        github_marker = " [GitHub]" if entry.is_github else ""
        print(f"  {entry.name}{github_marker}")
        print(f"    {entry.url}")
    print()

    # If --import flag is set, import the entries
    if args.do_import:
        if not args.category:
            cprint("Error: --category is required when using --import", Color.RED)
            return 1

        print(
            f"Importing {result.success_count} entries to category '{args.category}'..."
        )

        imported, skipped, errors = import_webloc_entries(
            webloc_entries=result.entries,
            category=args.category,
            json_path=json_file,
            db_path=db_file,
            use_github_metadata=not args.no_github,
            default_description=args.description or "Imported from webloc bookmark",
        )

        print()
        cprint("Import Results:", Color.BLUE, bold=True)
        print(f"  Imported: {imported}")
        print(f"  Skipped (duplicates): {skipped}")

        if errors:
            cprint(f"  Errors: {len(errors)}", Color.RED)
            for err in errors:
                print(f"    {err}")
            return 1

        cprint("Import complete.", Color.GREEN)

    return 0


# =============================================================================
# Main Entry Point
# =============================================================================


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="linkdb",
        description="A CLI tool for managing curated project lists.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (use -vv for debug)",
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress non-error output"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # import
    p = subparsers.add_parser(
        "import", help="Import from JSON to SQLite, or from .webloc files"
    )
    p.add_argument("-j", "--json", help="Path to JSON file")
    p.add_argument("--db", help="Path to SQLite database")
    p.add_argument("--update", action="store_true", help="Update existing entries")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be imported without making changes",
    )
    p.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompts")
    # Webloc import options
    p.add_argument(
        "--webloc",
        metavar="DIR",
        help="Import from .webloc files in directory",
    )
    p.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Scan subdirectories (with --webloc)",
    )
    p.add_argument("-c", "--category", help="Category for webloc imports")
    p.add_argument(
        "-d", "--description", help="Default description for non-GitHub weblocs"
    )
    p.add_argument(
        "--no-github",
        action="store_true",
        help="Don't fetch GitHub metadata (with --webloc)",
    )
    p.set_defaults(func=cmd_import)

    # export
    p = subparsers.add_parser("export", help="Export entries from SQLite to JSON")
    p.add_argument("--db", help="Path to SQLite database")
    p.add_argument("-o", "--output", required=True, help="Output JSON file path")
    p.add_argument(
        "--source-json",
        dest="source_json",
        help="Preserve categories from this source JSON file",
    )
    p.add_argument(
        "--include-github",
        action="store_true",
        help="Include GitHub metadata (stars, forks, language, etc.)",
    )
    p.set_defaults(func=cmd_export)

    # list
    p = subparsers.add_parser("list", help="List all entries in the database")
    p.add_argument("--db", help="Path to SQLite database")
    p.add_argument("-c", "--category", help="Filter by category")
    p.add_argument(
        "-f",
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format",
    )
    p.add_argument(
        "--stars-min",
        type=int,
        metavar="N",
        help="Filter by minimum GitHub stars (requires 'github' command first)",
    )
    p.add_argument(
        "--language",
        metavar="LANG",
        help="Filter by programming language (e.g., python, rust, c++)",
    )
    p.add_argument(
        "--active-only",
        action="store_true",
        help="Filter out archived/stale repos (no push in 365+ days)",
    )
    p.set_defaults(func=cmd_list)

    # search
    p = subparsers.add_parser("search", help="Search entries by name or description")
    p.add_argument("query", help="Search query")
    p.add_argument("--db", help="Path to SQLite database")
    p.set_defaults(func=cmd_search)

    # stats
    p = subparsers.add_parser("stats", help="Show database statistics")
    p.add_argument("--db", help="Path to SQLite database")
    p.set_defaults(func=cmd_stats)

    # category (with subcommands)
    category_parser = subparsers.add_parser("category", help="Manage categories")
    category_sub = category_parser.add_subparsers(dest="category_command")

    # category list
    p = category_sub.add_parser("list", help="List all categories")
    p.add_argument("-j", "--json", help="Path to JSON file")
    p.set_defaults(func=cmd_category_list)

    # category add
    p = category_sub.add_parser("add", help="Add a new category")
    p.add_argument("name", help="Category name")
    p.add_argument("-j", "--json", help="Path to JSON file")
    p.set_defaults(func=cmd_category_add)

    # category rm
    p = category_sub.add_parser("rm", help="Remove a category")
    p.add_argument("name", help="Category name")
    p.add_argument("-j", "--json", help="Path to JSON file")
    p.add_argument(
        "-f", "--force", action="store_true", help="Force removal even if in use"
    )
    p.set_defaults(func=cmd_category_rm)

    # check
    p = subparsers.add_parser("check", help="Check all URLs for broken links")
    p.add_argument("-j", "--json", help="Path to JSON file")
    p.add_argument(
        "-c", "--concurrency", type=int, default=10, help="Concurrent requests"
    )
    p.add_argument(
        "-t", "--timeout", type=float, default=10.0, help="Timeout per request"
    )
    p.add_argument(
        "--insecure",
        action="store_true",
        help="Disable SSL certificate verification (not recommended)",
    )
    p.set_defaults(func=cmd_check)

    # github (with subcommands: fetch, stale, cache)
    github_parser = subparsers.add_parser(
        "github", help="GitHub operations (fetch stats, find stale, manage cache)"
    )
    github_sub = github_parser.add_subparsers(dest="github_command")

    # github fetch (default behavior)
    p = github_sub.add_parser("fetch", help="Fetch GitHub statistics")
    p.add_argument("-j", "--json", help="Path to JSON file")
    p.add_argument(
        "-c", "--concurrency", type=int, default=5, help="Concurrent requests"
    )
    p.add_argument(
        "-s",
        "--sort",
        choices=["stars", "name", "activity"],
        default="stars",
        help="Sort results by",
    )
    p.add_argument(
        "--show-topics", action="store_true", help="Display repository topics"
    )
    p.add_argument(
        "--update-db", action="store_true", help="Update database with topics"
    )
    p.add_argument("--db", help="Path to SQLite database")
    p.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass cache and fetch fresh data from GitHub API",
    )
    p.set_defaults(func=cmd_github)

    # github stale
    p = github_sub.add_parser("stale", help="Find stale/unmaintained projects")
    p.add_argument("-j", "--json", help="Path to JSON file")
    p.add_argument("--days", type=int, default=365, help="Days since last push")
    p.add_argument(
        "-c", "--concurrency", type=int, default=5, help="Concurrent requests"
    )
    p.set_defaults(func=cmd_stale)

    # github cache
    p = github_sub.add_parser("cache", help="Manage GitHub API response cache")
    p.add_argument(
        "cache_action",
        choices=["stats", "clear"],
        help="Action: 'stats' or 'clear'",
    )
    p.add_argument("--db", help="Path to SQLite database")
    p.add_argument(
        "--all",
        action="store_true",
        help="Clear all cache entries, not just expired",
    )
    p.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Skip confirmation prompt",
    )
    p.set_defaults(func=cmd_cache)

    # Set default subcommand for github
    github_parser.set_defaults(func=cmd_github_help)

    # doctor
    p = subparsers.add_parser("doctor", help="Check data integrity and health")
    p.add_argument("-j", "--json", help="Path to JSON file")
    p.add_argument("--db", help="Path to SQLite database")
    p.set_defaults(func=cmd_doctor)

    # generate
    p = subparsers.add_parser("generate", help="Generate README.md from database")
    p.add_argument("--db", help="Path to SQLite database")
    p.add_argument("-o", "--output", help="Output README path")
    p.add_argument("-t", "--template", help="Custom template file")
    p.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite output file without prompting",
    )
    p.set_defaults(func=cmd_generate)

    # sort
    p = subparsers.add_parser("sort", help="Sort entries.json file")
    p.add_argument("-j", "--json", help="Path to JSON file")
    p.add_argument(
        "-c",
        "--by-category",
        action="store_true",
        help="Sort entries by category first, then by name (default: sort by name only)",
    )
    p.set_defaults(func=cmd_sort)

    # add
    p = subparsers.add_parser("add", help="Add entry/entries to JSON and database")
    p.add_argument("-n", "--name", help="Project name (auto-detected from GitHub URL)")
    p.add_argument("-c", "--category", help="Category (required unless --interactive)")
    p.add_argument(
        "-d",
        "--description",
        help="Project description (auto-detected from GitHub URL)",
    )
    p.add_argument("-u", "--url", help="Project URL")
    p.add_argument(
        "-r", "--repo", help="Repository URL (GitHub URLs auto-populate fields)"
    )
    p.add_argument("-j", "--json", help="Path to JSON file")
    p.add_argument("--db", help="Path to SQLite database")
    p.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Interactive mode with prompts for all fields",
    )
    p.add_argument(
        "-f",
        "--file",
        metavar="PATH",
        help="Add multiple entries from file (one URL per line)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be added without making changes (with --file)",
    )
    p.set_defaults(func=cmd_add)

    # remove
    p = subparsers.add_parser(
        "remove", help="Remove entry by name, or all entries in a category"
    )
    p.add_argument("name", nargs="?", help="Entry name to remove")
    p.add_argument(
        "-c",
        "--category",
        metavar="NAME",
        help="Remove ALL entries in this category",
    )
    p.add_argument("-j", "--json", help="Path to JSON file")
    p.add_argument("--db", help="Path to SQLite database")
    p.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without making changes",
    )
    p.set_defaults(func=cmd_remove)

    # dedupe
    p = subparsers.add_parser(
        "dedupe", help="Find and merge duplicate entries (same URL or repo)"
    )
    p.add_argument("-j", "--json", help="Path to JSON file")
    p.add_argument("--db", help="Path to SQLite database")
    p.add_argument(
        "--merge",
        action="store_true",
        help="Automatically merge all duplicates without prompting",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show duplicates without merging",
    )
    p.set_defaults(func=cmd_dedupe)

    # update
    p = subparsers.add_parser("update", help="Update an existing entry")
    p.add_argument("name", help="Entry name to update")
    p.add_argument("-c", "--category", help="New category")
    p.add_argument("-d", "--description", help="New description")
    p.add_argument("-u", "--url", help="New URL (use '' to clear)")
    p.add_argument("-r", "--repo", help="New repo URL (use '' to clear)")
    p.add_argument("-j", "--json", help="Path to JSON file")
    p.add_argument("--db", help="Path to SQLite database")
    p.set_defaults(func=cmd_update)

    # backup (with subcommands: create, restore, list)
    backup_parser = subparsers.add_parser(
        "backup", help="Backup operations (create, restore, list)"
    )
    backup_sub = backup_parser.add_subparsers(dest="backup_command")

    # backup create
    p = backup_sub.add_parser("create", help="Create a new backup")
    p.add_argument("-j", "--json", help="Path to JSON file")
    p.add_argument("--db", help="Path to SQLite database")
    p.add_argument(
        "--backup-dir",
        help="Directory to store backups (default: data/backups)",
    )
    p.set_defaults(func=cmd_backup)

    # backup restore
    p = backup_sub.add_parser("restore", help="Restore from a backup")
    p.add_argument("backup", nargs="?", help="Backup file (omit to list available)")
    p.add_argument("-j", "--json", help="Path to restore JSON file to")
    p.add_argument("--db", help="Path to restore database to")
    p.add_argument(
        "--backup-dir",
        help="Directory containing backups (default: data/backups)",
    )
    p.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be restored without making changes",
    )
    p.set_defaults(func=cmd_restore)

    # backup list
    p = backup_sub.add_parser("list", help="List available backups")
    p.add_argument(
        "--backup-dir",
        help="Directory containing backups (default: data/backups)",
    )
    p.set_defaults(func=cmd_backup_list)

    # Set default subcommand for backup
    backup_parser.set_defaults(func=cmd_backup_help)

    # history (combines diff and per-entry history)
    p = subparsers.add_parser("history", help="Show change history")
    p.add_argument("entry", nargs="?", help="Entry name (omit for all changes)")
    p.add_argument("--db", help="Path to SQLite database")
    p.add_argument(
        "--since",
        metavar="DATE",
        help="Show changes since date (YYYY-MM-DD or ISO format)",
    )
    p.add_argument(
        "--action",
        choices=["add", "remove", "update"],
        help="Filter by action type",
    )
    p.add_argument(
        "-n",
        "--limit",
        type=int,
        default=100,
        help="Maximum entries to show (default: 100)",
    )
    p.add_argument(
        "--details",
        action="store_true",
        help="Show full details for each change",
    )
    p.set_defaults(func=cmd_history_combined)

    args = parser.parse_args()

    # Configure logging based on verbosity
    setup_logging(verbose=args.verbose, quiet=args.quiet)

    if not args.command:
        parser.print_help()
        return 0

    result: int = args.func(args)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
