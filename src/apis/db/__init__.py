import typing
from src.data.config import *
from mysql.connector.connection import MySQLConnection as Connection
from mysql.connector.cursor import MySQLCursor as Cursor

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_connection_and_cursor(
    database=CLIENTS_DATABASE_NAME,
) -> typing.Tuple[Connection, Cursor]:
    conn = Connection(host=HOST, user=USER, password=PASSWORD, database=database)
    cursor = conn.cursor()
    return conn, cursor


def close_connection_and_cursor(connection: Connection, cursor: Cursor):
    cursor.close()
    connection.close()


def commit_and_close_connection_and_cursor(connection: Connection, cursor: Cursor):
    connection.commit()
    cursor.close()
    connection.close()


def get_right_str(string: str) -> str:
    """put escape characters into string (converts "50%_promocode" to "50\%\_promocode")"""
    string = string.replace("\\", "\\\\")
    string = string.replace("%", "\%")
    string = string.replace("_", "\_")
    string = string.replace('"', '\\"')
    return string
