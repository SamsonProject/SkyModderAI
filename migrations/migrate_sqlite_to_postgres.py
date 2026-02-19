"""
SQLite to PostgreSQL Data Migration Script

This script migrates data from a SQLite database to PostgreSQL.
It handles type conversions and ensures data integrity during the transfer.

Usage:
    python migrations/migrate_sqlite_to_postgres.py

Environment Variables:
    SQLITE_DB_PATH: Path to SQLite database (default: instance/app.db)
    DATABASE_URL: PostgreSQL connection URL (required)

IMPORTANT: 
    - Backup both databases before running this script
    - Run during low-traffic period
    - Test thoroughly in staging before production
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.pool import NullPool

# Configuration
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "instance/app.db")
POSTGRES_URL = os.getenv("DATABASE_URL")

if not POSTGRES_URL:
    print("ERROR: DATABASE_URL environment variable is required")
    print("Example: postgresql://user:password@localhost:5432/skymodderai")
    sys.exit(1)

# Tables to migrate (in order to respect foreign keys)
TABLES_TO_MIGRATE = [
    "users",
    "user_sessions",
    "password_reset_tokens",
    "api_keys",
    "user_saved_lists",
    "community_posts",
    "community_replies",
    "community_votes",
    "community_reports",
    "openclaw_grants",
    "openclaw_events",
    "openclaw_permissions",
    "openclaw_plan_runs",
    "openclaw_feedback",
    "user_feedback",
    "user_activity",
    "satisfaction_surveys",
    "conflict_stats",
    "businesses",
    "business_trust_scores",
    "business_votes",
    "business_flags",
    "business_connections",
    "hub_resources",
    "sponsors",
    "sponsor_creatives",
    "sponsor_clicks",
    "sponsor_votes",
    "source_credibility",
    "knowledge_sources",
    "trash_bin",
    "mod_database",
    "conflicts",
    "mod_conflicts",
    "conflict_rules",
    "game_versions",
    "mod_tags",
    "mod_platform_links",
]


def get_sqlite_connection():
    """Get SQLite connection."""
    if not os.path.exists(SQLITE_DB_PATH):
        raise FileNotFoundError(f"SQLite database not found at: {SQLITE_DB_PATH}")
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_postgres_engine():
    """Get PostgreSQL engine."""
    # Convert postgres:// to postgresql:// if needed
    url = POSTGRES_URL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    
    return create_engine(url, poolclass=NullPool, echo=True)


def convert_sqlite_value(value, col_type):
    """Convert SQLite value to PostgreSQL-compatible format."""
    if value is None:
        return None
    
    col_type_upper = col_type.upper() if col_type else ""
    
    # Handle boolean conversion
    if "BOOL" in col_type_upper:
        return bool(value)
    
    # Handle integer conversion
    if "INT" in col_type_upper or "SERIAL" in col_type_upper:
        try:
            return int(value) if value != "" else None
        except (ValueError, TypeError):
            return None
    
    # Handle float/real conversion
    if "REAL" in col_type_upper or "FLOAT" in col_type_upper or "DOUBLE" in col_type_upper:
        try:
            return float(value) if value != "" else None
        except (ValueError, TypeError):
            return None
    
    # Handle JSON/text that might be JSON
    if "JSON" in col_type_upper:
        return value
    
    # Default: return as string
    return value


def migrate_table(sqlite_conn, pg_engine, table_name):
    """Migrate a single table from SQLite to PostgreSQL."""
    print(f"\nMigrating table: {table_name}")
    
    sqlite_cursor = sqlite_conn.cursor()
    
    # Get table info from SQLite
    try:
        sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = sqlite_cursor.fetchall()
    except sqlite3.OperationalError:
        print(f"  ⚠️  Table {table_name} does not exist in SQLite, skipping")
        return 0
    
    if not columns_info:
        print(f"  ⚠️  No columns found for table {table_name}, skipping")
        return 0
    
    column_names = [col["name"] for col in columns_info]
    column_types = {col["name"]: col["type"] for col in columns_info}
    
    # Get all rows from SQLite
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"  ℹ️  No data in table {table_name}")
        return 0
    
    print(f"  Found {len(rows)} rows to migrate")
    
    # Prepare INSERT statement for PostgreSQL
    placeholders = ", ".join(["%s"] * len(column_names))
    columns_quoted = ", ".join(column_names)
    
    # Disable foreign key checks temporarily
    with pg_engine.connect() as conn:
        conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))
        
        inserted = 0
        skipped = 0
        
        for row in rows:
            try:
                # Convert values
                values = []
                for i, col_name in enumerate(column_names):
                    value = row[i]
                    col_type = column_types.get(col_name, "TEXT")
                    converted = convert_sqlite_value(value, col_type)
                    values.append(converted)
                
                # Insert into PostgreSQL
                insert_sql = f"""
                    INSERT INTO {table_name} ({columns_quoted})
                    VALUES ({placeholders})
                    ON CONFLICT DO NOTHING
                """
                conn.execute(text(insert_sql), tuple(values))
                inserted += 1
                
            except Exception as e:
                print(f"  ⚠️  Error inserting row: {e}")
                skipped += 1
                continue
        
        # Commit the transaction
        conn.commit()
        
        print(f"  ✅ Migrated {inserted} rows, skipped {skipped} rows")
        return inserted


def verify_migration(pg_engine):
    """Verify the migration by counting rows in PostgreSQL."""
    print("\n" + "=" * 60)
    print("Verifying migration...")
    print("=" * 60)
    
    with pg_engine.connect() as conn:
        for table_name in TABLES_TO_MIGRATE:
            try:
                result = conn.execute(
                    text(f"SELECT COUNT(*) FROM {table_name}")
                ).fetchone()
                count = result[0] if result else 0
                print(f"  {table_name}: {count} rows")
            except Exception as e:
                print(f"  {table_name}: Error - {e}")


def main():
    """Run the migration."""
    print("=" * 60)
    print("SQLite to PostgreSQL Migration")
    print("=" * 60)
    print(f"SQLite database: {SQLITE_DB_PATH}")
    print(f"PostgreSQL URL: {POSTGRES_URL[:50]}...")
    print(f"Started at: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Validate SQLite database exists
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"\n❌ ERROR: SQLite database not found at {SQLITE_DB_PATH}")
        print("Please ensure the database exists or set SQLITE_DB_PATH environment variable")
        sys.exit(1)
    
    # Connect to databases
    print("\nConnecting to databases...")
    try:
        sqlite_conn = get_sqlite_connection()
        print(f"  ✅ Connected to SQLite: {SQLITE_DB_PATH}")
    except Exception as e:
        print(f"  ❌ Failed to connect to SQLite: {e}")
        sys.exit(1)
    
    try:
        pg_engine = get_postgres_engine()
        print(f"  ✅ Connected to PostgreSQL")
        
        # Test connection
        with pg_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"  ✅ PostgreSQL connection verified")
    except Exception as e:
        print(f"  ❌ Failed to connect to PostgreSQL: {e}")
        sys.exit(1)
    
    # Run migration
    total_rows = 0
    migrated_tables = 0
    
    for table_name in TABLES_TO_MIGRATE:
        try:
            rows = migrate_table(sqlite_conn, pg_engine, table_name)
            total_rows += rows
            if rows > 0:
                migrated_tables += 1
        except Exception as e:
            print(f"\n❌ Error migrating {table_name}: {e}")
            continue
    
    # Close connections
    sqlite_conn.close()
    
    # Summary
    print("\n" + "=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"Tables migrated: {migrated_tables}")
    print(f"Total rows migrated: {total_rows}")
    print(f"Completed at: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Verify
    verify_migration(pg_engine)
    
    print("\n" + "=" * 60)
    print("⚠️  IMPORTANT NEXT STEPS:")
    print("=" * 60)
    print("1. Verify data integrity in PostgreSQL")
    print("2. Update application configuration to use PostgreSQL")
    print("3. Test all features thoroughly")
    print("4. Keep SQLite backup until confident in migration")
    print("=" * 60)


if __name__ == "__main__":
    main()
