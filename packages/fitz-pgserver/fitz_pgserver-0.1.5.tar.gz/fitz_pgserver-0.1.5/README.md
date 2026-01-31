# fitz-pgserver

Fork of [pgserver](https://github.com/orm011/pgserver) with Windows crash recovery fix.

## Why this fork?

On Windows, when PostgreSQL crashes or is killed (e.g., via Ctrl+C), the recovery process can fail with a "sharing violation" error on the log file. This happens because:

1. `pg_ctl -l logfile start` opens the log file for writing
2. postgres subprocess starts and does crash recovery
3. During recovery, postgres tries to **fsync the entire pgdata directory**
4. This includes the log file that pg_ctl still has open → sharing violation
5. postgres retries for 30 seconds before proceeding

## The Fix

Put the log file in the system temp directory (outside pgdata):

```python
# Before (pgserver):
self.log = self.pgdata / 'log'

# After (fitz-pgserver):
temp_dir = Path(tempfile.gettempdir())
self.log = temp_dir / f'pgserver_log.{uuid.uuid4().hex[:8]}'
```

By putting the log file outside pgdata, postgres doesn't try to fsync it during recovery, avoiding the sharing violation entirely.

## Installation

```bash
pip install fitz-pgserver
```

## Usage

Drop-in replacement for pgserver:

```python
# Instead of: import pgserver
import fitz_pgserver as pgserver

db = pgserver.get_server("./my_pgdata")
uri = db.get_uri()
# Use uri with psycopg, SQLAlchemy, etc.
```

## Performance

| Scenario | pgserver | fitz-pgserver |
|----------|----------|---------------|
| Normal startup | ~2s | ~2s |
| First-time init | ~10-13s | ~10-13s |
| **Crash recovery** | **~33s** (data preserved but slow) | **~1-2s** (28x faster) |

The massive improvement in crash recovery is because we avoid the 30-second sharing violation retry loop.

## License

Apache 2.0 (same as original pgserver)

## Credits

Original pgserver by [Oscar Moll](https://github.com/orm011/pgserver).
