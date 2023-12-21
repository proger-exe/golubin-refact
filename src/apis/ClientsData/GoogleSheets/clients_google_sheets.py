from typing import List, Tuple
from .config import *
from src.apis import *
from mysql.connector.errors import IntegrityError

class RepeatedGoogleSpreadSheet(Exception):
    def __init__(self, client_id: int, spreadsheet_id: str):
        super(RepeatedGoogleSpreadSheet, self).__init__(
            f'Duplicate google spread sheet id ("{spreadsheet_id}") for client {client_id}')

def save_google_sheet_to_client(client_id: int, spread_sheet_id: str, sheet_id: int):
    connection, cursor = get_connection_and_cursor()
    try:
        cursor.execute(
            f'INSERT INTO {CLIENTS_SPREAD_SHEETS} VALUES ({client_id}, "{spread_sheet_id}", {sheet_id})')
    except IntegrityError as e:
        if e.code == DUPLICATE_MYSQL_ENTRY_CODE:
            raise(RepeatedGoogleSpreadSheet(client_id, spread_sheet_id))
        else:
            raise(e)
    finally:
        commit_and_close_connection_and_cursor(connection, cursor)

def get_google_sheet_of_client(client_id: int) -> Tuple[str, int]:
    connection, cursor = get_connection_and_cursor()
    cursor.execute(
        f'SELECT {SPREAD_SHEET_ID}, {SHEET_ID} FROM {CLIENTS_SPREAD_SHEETS} WHERE {CLIENT_ID} = {client_id}')
    result = cursor.fetchall()
    close_connection_and_cursor(connection, cursor)
    if not result:
        return ('', -1)
    return result[0]

def delete_spread_sheet_of_client(client_id: int):
    connection, cursor = get_connection_and_cursor()
    cursor.execute(f'DELETE FROM {CLIENTS_SPREAD_SHEETS} WHERE {CLIENT_ID} = {client_id}')
    commit_and_close_connection_and_cursor(connection, cursor)

def get_all_clients_with_google_sheets() -> List[int]:
    connection, cursor = get_connection_and_cursor()
    cursor.execute(f'SELECT {CLIENT_ID} FROM {CLIENTS_SPREAD_SHEETS}')
    result = cursor.fetchall()
    close_connection_and_cursor(connection, cursor)
    if not result:
        return []
    return [i[0] for i in result]