"""Database migration management for brawny (SQLite-only)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from brawny.model.errors import DatabaseError
from brawny.logging import get_logger, log_unexpected

if TYPE_CHECKING:
    from brawny.db.base import Database


MIGRATIONS_DIR = Path(__file__).parent / "migrations"
logger = get_logger(__name__)


@dataclass
class Migration:
    """Represents a database migration."""

    version: str
    filename: str
    sql: str
    applied_at: datetime | None = None

    @property
    def is_applied(self) -> bool:
        return self.applied_at is not None


def discover_migrations() -> list[Migration]:
    """Discover all migration files in the migrations directory.

    Returns:
        List of Migration objects sorted by version

    Raises:
        DatabaseError: If duplicate migration versions are found
    """
    migrations: list[Migration] = []
    seen_versions: dict[str, str] = {}

    if not MIGRATIONS_DIR.exists():
        return migrations

    for file_path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        # Extract version from filename (e.g., "001_init.sql" -> "001")
        match = re.match(r"^(\d+)_.*\.sql$", file_path.name)
        if match:
            version = match.group(1)

            # Check for duplicate version numbers
            if version in seen_versions:
                raise DatabaseError(
                    f"Duplicate migration version {version}: "
                    f"{seen_versions[version]} and {file_path.name}"
                )
            seen_versions[version] = file_path.name

            sql = file_path.read_text()
            migrations.append(
                Migration(
                    version=version,
                    filename=file_path.name,
                    sql=sql,
                )
            )

    return sorted(migrations, key=lambda m: m.version)


def get_applied_migrations(db: Database) -> set[str]:
    """Get set of applied migration versions.

    Args:
        db: Database connection

    Returns:
        Set of version strings that have been applied
    """
    try:
        result = db.execute_returning(
            """
            SELECT version, applied_at
            FROM schema_migrations
            ORDER BY version
            """
        )
        return {row["version"] for row in result}
    except Exception as e:
        db_info = _db_context(db)
        if _is_missing_schema_migrations(e):
            # RECOVERABLE schema_migrations missing on fresh DBs.
            log_unexpected(
                logger,
                "migrations.schema_missing",
                db=db_info,
                error=str(e)[:200],
            )
            return set()
        # BUG re-raise on unexpected schema read failures.
        log_unexpected(
            logger,
            "migrations.schema_read_failed",
            db=db_info,
            error=str(e)[:200],
        )
        raise DatabaseError("Failed to read schema_migrations table") from e


def get_pending_migrations(db: Database) -> list[Migration]:
    """Get list of migrations that haven't been applied.

    Args:
        db: Database connection

    Returns:
        List of pending Migration objects
    """
    applied = get_applied_migrations(db)
    all_migrations = discover_migrations()
    return [m for m in all_migrations if m.version not in applied]


def get_migration_status(db: Database) -> list[Migration]:
    """Get status of all migrations.

    Args:
        db: Database connection

    Returns:
        List of all migrations with applied_at set if applied
    """
    applied: dict[str, datetime] = {}

    try:
        result = db.execute_returning(
            """
            SELECT version, applied_at
            FROM schema_migrations
            ORDER BY version
            """
        )
        for row in result:
            applied[row["version"]] = row["applied_at"]
    except Exception as e:
        db_info = _db_context(db)
        if _is_missing_schema_migrations(e):
            # RECOVERABLE schema_migrations missing on fresh DBs.
            log_unexpected(
                logger,
                "migrations.schema_missing",
                db=db_info,
                error=str(e)[:200],
            )
        else:
            # BUG re-raise on unexpected schema read failures.
            log_unexpected(
                logger,
                "migrations.schema_read_failed",
                db=db_info,
                error=str(e)[:200],
            )
            raise DatabaseError("Failed to read schema_migrations table") from e

    all_migrations = discover_migrations()
    for migration in all_migrations:
        if migration.version in applied:
            migration.applied_at = applied[migration.version]

    return all_migrations


def run_migration(db: Database, migration: Migration) -> None:
    """Run a single migration.

    Args:
        db: Database connection
        migration: Migration to run

    Raises:
        DatabaseError: If migration fails
    """
    try:
        if migration.version == "012":
            with db.transaction():
                existing = {
                    r["name"].lower()
                    for r in db.execute_returning("PRAGMA table_info(tx_intents)")
                }
                if "claimed_by" in existing:
                    db.execute(
                        "INSERT OR IGNORE INTO schema_migrations (version) VALUES (?)",
                        (migration.version,),
                    )
                    return
                try:
                    db.execute(
                        "ALTER TABLE tx_intents ADD COLUMN claimed_by VARCHAR(200)"
                    )
                except Exception as exc:
                    if "duplicate column name" not in str(exc).lower():
                        # BUG re-raise unexpected migration failure.
                        log_unexpected(
                            logger,
                            "migrations.duplicate_column_unexpected",
                            version=migration.version,
                            table="tx_intents",
                            error=str(exc)[:200],
                        )
                        raise
                    # RECOVERABLE duplicate column means migration already applied.
                    log_unexpected(
                        logger,
                        "migrations.duplicate_column_ignored",
                        version=migration.version,
                        table="tx_intents",
                        error=str(exc)[:200],
                    )
                db.execute(
                    "INSERT OR IGNORE INTO schema_migrations (version) VALUES (?)",
                    (migration.version,),
                )
            return
        if migration.version == "014":
            with db.transaction():
                existing = {
                    r["name"].lower()
                    for r in db.execute_returning("PRAGMA table_info(tx_intents)")
                }
                if "lease_expires_at" in existing:
                    db.execute(
                        "INSERT OR IGNORE INTO schema_migrations (version) VALUES (?)",
                        (migration.version,),
                    )
                    return
                try:
                    db.execute(
                        "ALTER TABLE tx_intents ADD COLUMN lease_expires_at TIMESTAMP"
                    )
                except Exception as exc:
                    if "duplicate column name" not in str(exc).lower():
                        # BUG re-raise unexpected migration failure.
                        log_unexpected(
                            logger,
                            "migrations.duplicate_column_unexpected",
                            version=migration.version,
                            table="tx_intents",
                            error=str(exc)[:200],
                        )
                        raise
                    # RECOVERABLE duplicate column means migration already applied.
                    log_unexpected(
                        logger,
                        "migrations.duplicate_column_ignored",
                        version=migration.version,
                        table="tx_intents",
                        error=str(exc)[:200],
                    )
                db.execute(
                    "INSERT OR IGNORE INTO schema_migrations (version) VALUES (?)",
                    (migration.version,),
                )
            return
        if migration.version == "022":
            statements = _split_sql_statements(migration.sql)
            db.execute("PRAGMA foreign_keys = OFF")
            try:
                with db.transaction():
                    for stmt in statements:
                        stmt = stmt.strip()
                        if not stmt:
                            continue
                        try:
                            db.execute(stmt)
                        except DatabaseError as e:
                            if _is_duplicate_column_error(e, stmt):
                                # Idempotent safety for already-applied schema changes.
                                continue
                            raise
            finally:
                db.execute("PRAGMA foreign_keys = ON")
            return

        with db.transaction():
            # Split SQL into individual statements for SQLite compatibility
            # SQLite can only execute one statement at a time
            statements = _split_sql_statements(migration.sql)
            for stmt in statements:
                stmt = stmt.strip()
                if not stmt:
                    continue
                try:
                    db.execute(stmt)
                except DatabaseError as e:
                    if _is_duplicate_column_error(e, stmt):
                        # Idempotent safety for already-applied schema changes.
                        continue
                    raise
    except Exception as e:
        # BUG re-raise on migration failure.
        log_unexpected(
            logger,
            "migrations.run_failed",
            version=migration.version,
            filename=migration.filename,
            error=str(e)[:200],
        )
        raise DatabaseError(
            f"Migration {migration.version} ({migration.filename}) failed: {e}"
        )


def _is_duplicate_column_error(error: Exception, stmt: str) -> bool:
    """Return True if the error indicates an already-existing column."""
    message = str(error).lower()
    if "duplicate column name" in message or "already exists" in message:
        if "add column" in stmt.lower():
            return True
    return False


def _split_sql_statements(sql: str) -> list[str]:
    """Split SQL into individual statements.

    Handles semicolons, comments, and multi-line statements.

    Args:
        sql: SQL text with multiple statements

    Returns:
        List of individual statements
    """
    # Remove SQL comments
    lines = []
    for line in sql.split('\n'):
        # Remove -- comments
        if '--' in line:
            line = line[:line.index('--')]
        lines.append(line)
    sql = '\n'.join(lines)

    # Split on semicolons, but be careful about strings
    # This is a simple split - for production, use a proper SQL parser
    statements = []
    current = []
    in_string = False
    string_char = None

    for char in sql:
        if char in ('"', "'") and not in_string:
            in_string = True
            string_char = char
            current.append(char)
        elif char == string_char and in_string:
            in_string = False
            string_char = None
            current.append(char)
        elif char == ';' and not in_string:
            stmt = ''.join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
        else:
            current.append(char)

    # Don't forget the last statement if no trailing semicolon
    stmt = ''.join(current).strip()
    if stmt:
        statements.append(stmt)

    return statements


def _is_missing_schema_migrations(error: Exception) -> bool:
    message = str(error).lower()
    return "no such table" in message and "schema_migrations" in message


def _db_context(db: Database) -> dict[str, str]:
    info: dict[str, str] = {"dialect": getattr(db, "dialect", "unknown")}
    db_path = getattr(db, "_database_path", None)
    if isinstance(db_path, str):
        info["path"] = db_path
    return info


def run_pending_migrations(db: Database) -> list[Migration]:
    """Run all pending migrations.

    Args:
        db: Database connection

    Returns:
        List of migrations that were applied

    Raises:
        DatabaseError: If any migration fails
    """
    pending = get_pending_migrations(db)

    for migration in pending:
        run_migration(db, migration)
        migration.applied_at = datetime.utcnow()

    return pending


def verify_critical_schema(db: Database) -> None:
    """Hard-fail if critical columns missing. Runs for daemon + CLI."""
    # Keep the list short and hot-path only.
    required_by_table: dict[str, set[str]] = {
        "tx_intents": {
            "intent_id",
            "status",
            "claim_token",
            "claimed_at",
            "claimed_by",
            "lease_expires_at",
        },
        "tx_attempts": {
            "attempt_id",
            "intent_id",
            "status",
            "created_at",
        },
        "nonce_reservations": {
            "id",
            "chain_id",
            "signer_address",
            "nonce",
            "status",
            "intent_id",
            "created_at",
            "updated_at",
        },
    }

    missing_by_table: dict[str, set[str]] = {}
    for table_name, required in required_by_table.items():
        rows = db.execute_returning(f"PRAGMA table_info({table_name})")
        existing = {r["name"].lower() for r in rows}
        missing = {col for col in required if col.lower() not in existing}
        if missing:
            missing_by_table[table_name] = missing

    if not missing_by_table:
        return

    expected_version = _latest_migration_version()
    current_version, current_version_note = _read_schema_version(db)
    remediation = _schema_remediation(expected_version, current_version, current_version_note)

    missing_details = "; ".join(
        f"{table}: {', '.join(sorted(cols))}"
        for table, cols in sorted(missing_by_table.items())
    )
    message_parts = [
        f"Missing critical columns: {missing_details}.",
    ]
    if expected_version:
        message_parts.append(f"Expected schema version: {expected_version}.")
    if current_version:
        message_parts.append(f"Current schema version: {current_version}.")
    elif current_version_note:
        message_parts.append(f"Current schema version: unknown ({current_version_note}).")
    message_parts.append(f"Remediation: {remediation}.")
    raise RuntimeError(" ".join(message_parts))


def _latest_migration_version() -> str | None:
    migrations = discover_migrations()
    if not migrations:
        return None
    return max(migrations, key=lambda m: int(m.version)).version


def _read_schema_version(db: Database) -> tuple[str | None, str | None]:
    try:
        rows = db.execute_returning(
            "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1"
        )
    except Exception as exc:
        if _is_missing_schema_migrations(exc):
            return None, "schema_migrations missing"
        # RECOVERABLE used for diagnostics when schema version is unreadable.
        log_unexpected(
            logger,
            "migrations.schema_read_failed",
            db=_db_context(db),
            error=str(exc)[:200],
        )
        return None, "schema_migrations unreadable"

    if not rows:
        return None, "schema_migrations empty"
    return str(rows[0]["version"]), None


def _schema_remediation(
    expected_version: str | None,
    current_version: str | None,
    current_version_note: str | None,
) -> str:
    if current_version_note is not None:
        return "DB appears out-of-band; delete/re-init or run a repair script if available"
    if expected_version and current_version:
        expected_int = _parse_version_int(expected_version)
        current_int = _parse_version_int(current_version)
        if expected_int is not None and current_int is not None:
            if current_int < expected_int:
                return "run `brawny db migrate`"
    return "DB appears out-of-band; delete/re-init or run a repair script if available"


def _parse_version_int(version: str) -> int | None:
    try:
        return int(version)
    except ValueError:
        return None


class Migrator:
    """High-level migration management interface."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def status(self) -> list[dict[str, str | bool]]:
        """Get migration status as a list of dicts.

        Returns:
            List of dicts with version, filename, applied, and applied_at
        """
        migrations = get_migration_status(self.db)
        return [
            {
                "version": m.version,
                "filename": m.filename,
                "applied": m.is_applied,
                "applied_at": m.applied_at.isoformat() if m.applied_at else None,
            }
            for m in migrations
        ]

    def pending(self) -> list[Migration]:
        """Get pending migrations."""
        return get_pending_migrations(self.db)

    def migrate(self) -> list[Migration]:
        """Run all pending migrations.

        Returns:
            List of applied migrations
        """
        return run_pending_migrations(self.db)

    def has_pending(self) -> bool:
        """Check if there are pending migrations."""
        return len(self.pending()) > 0
