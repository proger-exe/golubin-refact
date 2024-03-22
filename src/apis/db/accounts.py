from typing import List, Union
from src.apis.db import get_connection_and_cursor, close_connection_and_cursor, commit_and_close_connection_and_cursor

_ACCOUNTS_TABLE = 'accounts'
_OWNER_ID = 'owner_id'
_ACCOUNT_ID = 'id'
_CATEGORY = 'category'
_ACCOUNTS_ARCHIVE = 'accounts_archive'


def add_account_to_client(client_id: int, account_id: int, for_category: int):
    connection, cursor = get_connection_and_cursor()
    cursor.execute(f'INSERT INTO {_ACCOUNTS_TABLE} VALUES {client_id, account_id, for_category}')
    commit_and_close_connection_and_cursor(connection, cursor)


def get_all_accounts_of(client_id: int, for_category = None) -> List[int]:
    connection, cursor = get_connection_and_cursor()
    cursor.execute(
        f'SELECT DISTINCT({_ACCOUNT_ID}) FROM {_ACCOUNTS_TABLE} WHERE {_OWNER_ID} = {client_id}' + 
        ('' if for_category == None else f' AND {_CATEGORY} = {for_category}')
    )
    result = cursor.fetchall()
    close_connection_and_cursor(connection, cursor)
    if not result:
        return []
    return [i[0] for i in result]


def delete_account(owner_id: int, account_id: int, category: int = None):
    connection, cursor = get_connection_and_cursor()
    cursor.execute(f'DELETE FROM {_ACCOUNTS_TABLE} WHERE {_OWNER_ID} = {owner_id} AND '
        f'{_ACCOUNT_ID} = {account_id}' + ('' if category == None else f' AND {_CATEGORY} = {category}'))
    commit_and_close_connection_and_cursor(connection, cursor)


def get_admin_of_account(account_id: int, category: int = None) -> Union[int, None]:
    connection, cursor = get_connection_and_cursor()
    cursor.execute(f'SELECT {_OWNER_ID} FROM {_ACCOUNTS_TABLE} WHERE {_ACCOUNT_ID} = {account_id}' + \
        ('' if category == None else f' AND {_CATEGORY} = {category}'))
    result = cursor.fetchall()
    close_connection_and_cursor(connection, cursor)
    if not result:
        return None
    return result[0][0]


def get_all_categories_which_account_is_pludged_to(account_id: int) -> List[int]:
    connection, cursor = get_connection_and_cursor()
    cursor.execute(f'SELECT {_CATEGORY} FROM {_ACCOUNTS_TABLE} WHERE {_ACCOUNT_ID} = {account_id}')
    result = cursor.fetchall()
    close_connection_and_cursor(connection, cursor)
    if not result:
        return []
    return [i[0] for i in result]


def transfer_accounts(old_admin_id: int, new_id: int):
    connection, cursor = get_connection_and_cursor()
    try:
        cursor.execute(f'INSERT INTO {_ACCOUNTS_ARCHIVE} SELECT * FROM {_ACCOUNTS_TABLE} WHERE {_OWNER_ID} = {old_admin_id}')
    except:
        pass
    cursor.execute(f'DELETE FROM {_ACCOUNTS_TABLE} WHERE {_OWNER_ID} = {new_id}')
    cursor.execute(f'UPDATE {_ACCOUNTS_TABLE} SET {_OWNER_ID} = {new_id} WHERE {_OWNER_ID} = {old_admin_id}')
    commit_and_close_connection_and_cursor(connection, cursor)