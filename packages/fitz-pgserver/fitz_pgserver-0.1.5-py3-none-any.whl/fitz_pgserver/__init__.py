# fitz_pgserver/__init__.py
"""
fitz-pgserver: Fork of pgserver with Windows crash recovery fix.

This is a fork of pgserver (https://github.com/orm011/pgserver) that fixes
a Windows-specific issue where crash recovery fails due to log file locking.

The fix: Use unique log file names per session to avoid sharing violations.

Original pgserver by Oscar Moll, licensed under Apache 2.0.
"""
from ._commands import POSTGRES_BIN_PATH, initdb, pg_ctl
from .postgres_server import PostgresServer, get_server

__all__ = ["PostgresServer", "get_server", "POSTGRES_BIN_PATH", "initdb", "pg_ctl"]
__version__ = "0.1.5"  # Based on pgserver 0.1.4 + Windows fix
