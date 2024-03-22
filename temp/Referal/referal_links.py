from typing import Union
from .config import *
from database import *

def add_new_referal_link(name: str, url: str):
    conn, cursor = get_connection_and_cursor()
    cursor.execute(F'INSERT INTO {REFERAL_LINKS} VALUES ("{name}", "{url}")')
    commit_and_close_connection_and_cursor(conn, cursor)

def get_referal_url(name: str) -> Union[str, None]:
    conn, cursor = get_connection_and_cursor()
    name = get_right_str(name)
    cursor.execute(f'SELECT {REF_URL} FROM {REFERAL_LINKS} WHERE {REF_LINK_NAME} = "{name}"')
    result = cursor.fetchall()
    close_connection_and_cursor(conn, cursor)
    if not result:
        return None
    return result[0][0]