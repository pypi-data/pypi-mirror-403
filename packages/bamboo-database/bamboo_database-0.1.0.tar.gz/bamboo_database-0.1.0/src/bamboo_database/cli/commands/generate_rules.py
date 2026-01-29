"""Generate rules command for bamboo_database CLI."""

import argparse
from pathlib import Path


RULES_TEMPLATE = '''# Bamboo Database Migration Rules

Guidelines for creating database migrations with bamboo_database.

## Migration File Naming

### Format
```
{version}_{type}_{description}.sql
```

### Components
- **version**: 4-digit zero-padded number (0001, 0002, 0003...)
- **type**: One of `migrate`, `seed`, or `index`
- **description**: Snake_case description of the change

### Examples
```
0001_migrate_create_users.sql
0002_seed_insert_admin_user.sql
0003_index_users_email_idx.sql
0004_migrate_add_posts_table.sql
0005_seed_insert_sample_posts.sql
```

## Migration Types

| Type | Purpose | Example |
|------|---------|---------|
| `migrate` | Schema changes (CREATE, ALTER, DROP TABLE) | `0001_migrate_create_users.sql` |
| `seed` | Initial/reference data (INSERT statements) | `0002_seed_insert_admin_user.sql` |
| `index` | Index creation (CREATE INDEX) | `0003_index_users_email_idx.sql` |

## Migration File Structure

Every migration file should be wrapped in a transaction:

```sql
BEGIN;

-- Your SQL statements here

COMMIT;
```

## Combined Migration-Seed Files

You can include both schema changes AND seed data in a single migration file:

```sql
-- 0001_migrate_create_users.sql
BEGIN;

-- Schema
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed Data
INSERT INTO users (id, email, name) VALUES
    (1, 'admin@example.com', 'Admin User')
ON CONFLICT (id) DO NOTHING;

COMMIT;
```

## Idempotent Seed Data

Always use database-specific idempotent insert syntax:

### PostgreSQL
```sql
INSERT INTO users (id, email, name) VALUES (1, 'admin@example.com', 'Admin')
ON CONFLICT (id) DO NOTHING;
```

### MySQL
```sql
INSERT IGNORE INTO users (id, email, name) VALUES (1, 'admin@example.com', 'Admin');
```

### SQLite
```sql
INSERT OR IGNORE INTO users (id, email, name) VALUES (1, 'admin@example.com', 'Admin');
```

## Execution Order

1. Files are sorted by version number (0001, 0002, 0003...)
2. Within the same version: `migrate` → `seed` → `index`
3. Each file executes atomically (all or nothing)

## Best Practices

1. **One logical change per migration** - Keep migrations focused
2. **Use transactions** - Wrap all statements in BEGIN/COMMIT
3. **Make seeds idempotent** - Use ON CONFLICT / INSERT IGNORE
4. **Include comments** - Document complex changes
5. **Test locally first** - Verify migrations before deploying
6. **Never modify applied migrations** - Create new migrations instead

## Example: Complete Migration Sequence

```sql
-- 0001_migrate_create_users.sql
BEGIN;
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMIT;

-- 0002_seed_insert_default_admin.sql
BEGIN;
INSERT INTO users (id, email, password_hash, name)
VALUES (1, 'admin@example.com', '$2b$12$hash...', 'Administrator')
ON CONFLICT (id) DO NOTHING;
COMMIT;

-- 0003_index_users_email.sql
BEGIN;
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
COMMIT;

-- 0004_migrate_add_roles_table.sql
BEGIN;
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE user_roles (
    user_id INTEGER REFERENCES users(id),
    role_id INTEGER REFERENCES roles(id),
    PRIMARY KEY (user_id, role_id)
);
COMMIT;
```

## CLI Commands

```bash
# Run pending migrations
bamboodb migrate

# Run for specific database
bamboodb migrate --database default

# Check migration status
bamboodb status

# List configured databases
bamboodb list-databases
```
'''


def run(args: argparse.Namespace) -> int:
    """Run the generate-rules command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    output_path = Path(args.output)

    # Write the rules file
    output_path.write_text(RULES_TEMPLATE)

    print(f"Generated migration rules: {output_path}")
    print("\nYou can provide this file to AI assistants when generating migrations.")

    return 0
