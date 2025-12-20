"""Database utilities"""
import psycopg2
import psycopg2.extras
import os
from contextlib import contextmanager

def get_db_connection():
    """Get PostgreSQL database connection"""
    conn = psycopg2.connect(
        os.environ.get('DATABASE_URL'),
        cursor_factory=psycopg2.extras.RealDictCursor
    )
    return conn

@contextmanager
def get_db():
    """Context manager for automatic connection cleanup"""
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