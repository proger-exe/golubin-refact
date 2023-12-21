import typing
from src.data import HOST, USER, PASSWORD, CLIENTS_DATABASE_NAME
from mysql.connector.connection import MySQLConnection as Connection
from mysql.connector.cursor import MySQLCursor as Cursor


def get_connection_and_cursor() -> typing.Tuple[Connection, Cursor]:
	conn = Connection(
        host = HOST, user = USER, password = PASSWORD, 
		database = CLIENTS_DATABASE_NAME
    )
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
	'''put escape characters into string (converts "50%_promocode" to "50\%\_promocode")'''
	string = string.replace('\\', '\\\\')
	string = string.replace('%', '\%')
	string = string.replace('_', '\_')
	string = string.replace('"', '\\"')
	return string


# To easyble
from .user import *