"""Database utilities"""
import psycopg
from psycopg.rows import dict_row
import os
from contextlib import contextmanager

def get_db_connection():
    conn = psycopg.connect(
        os.environ.get('DATABASE_URL'),
        row_factory=dict_row
    )
    return conn

@contextmanager
def get_db():
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