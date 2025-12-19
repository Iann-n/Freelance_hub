"""Database utilities"""
import sqlite3
from contextlib import contextmanager

def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect("freelancehub.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db():
    """Context manager for automatic connection cleanup - USE THIS!"""
    conn = None
    try:
        conn = get_db_connection()
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()