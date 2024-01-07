from datetime import datetime
from typing import List, Tuple, Union
from src.data.bot_data import EUGENIY_ID, MIN_PERIOD_TO_GET_VOTE_BUTTONS, days_per_period
from src.data.config import *
from src.apis import get_connection_and_cursor, close_connection_and_cursor, commit_and_close_connection_and_cursor
from src.utils.client import Client
from telebot import TeleBot


def client_has_year_subscribe(client_id: int, category: int = None) -> bool:
    if client_id == EUGENIY_ID:
        return True
    if not client_id:
        return False
    subscribes = Client.get_clients_by_filter(
            id = client_id, payment_period_end = datetime.now(), greater = True, category = category, 
            payment_period = days_per_period[MIN_PERIOD_TO_GET_VOTE_BUTTONS], is_paid = True
        )
    if not subscribes:
        return False
    return True


def user_is_having_launched_bot(user_id: int) -> bool:
    conn, cursor = get_connection_and_cursor()
    cursor.execute(f'SELECT COUNT({ID_COL}) FROM {USERS_TABLE_NAME} WHERE {ID_COL} = {user_id}')
    result = cursor.fetchall()
    close_connection_and_cursor(conn, cursor)
    return result[0][0]


def get_user_launching_date(user_id: int) -> datetime:
    conn, cursor = get_connection_and_cursor()
    cursor.execute(F'SELECT {LAUNCHING_DATE} FROM {USERS_TABLE_NAME} WHERE {ID_COL} = {user_id}')
    result = cursor.fetchall()
    close_connection_and_cursor(conn, cursor)
    if not result:
        return None
    return result[0][0]


def set_user_as_having_launched(user_id: int):
    conn, cursor = get_connection_and_cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        f'INSERT INTO {USERS_TABLE_NAME} VALUES({user_id}, "{now}", 0, NULL, '
        'DEFAULT, DEFAULT, 0, DEFAULT, FALSE)'
    )
    commit_and_close_connection_and_cursor(conn, cursor)


def set_user_as_offered_trial(user_id: int):
    conn, cursor = get_connection_and_cursor()
    cursor.execute(f'UPDATE {USERS_TABLE_NAME} SET {IS_OFFERED_TRIAL} = 1 WHERE {ID_COL} = {user_id}')
    commit_and_close_connection_and_cursor(conn, cursor)


def user_is_offered_trial(user_id: int):
    conn, cursor = get_connection_and_cursor()
    cursor.execute(f'SELECT {IS_OFFERED_TRIAL} FROM {USERS_TABLE_NAME} WHERE {ID_COL}  ={user_id}')
    result = cursor.fetchall()
    close_connection_and_cursor(conn, cursor)
    if not result:
        return False
    return result[0][0]


def get_all_user_ids() -> List[int]:
    conn, cursor = get_connection_and_cursor()
    cursor.execute(f'SELECT {ID_COL} FROM {USERS_TABLE_NAME}')
    result = [i[0] for i in  cursor.fetchall()]
    close_connection_and_cursor(conn, cursor)
    return result


def get_all_users() -> List[Tuple[int, datetime, bool, Union[None, datetime], bool, Union[None, str]]]:
    conn, cursor = get_connection_and_cursor()
    cursor.execute(f'SELECT * FROM {USERS_TABLE_NAME}')
    result = cursor.fetchall()
    close_connection_and_cursor(conn, cursor)
    return result


def date_of_recieveing_latest_messages(user_id: int) -> datetime: # date when user recieved latest messages per those day
    conn, cursor = get_connection_and_cursor()
    cursor.execute(f'SELECT {DATE_OF_RECIEVEING_MESSAGES} FROM {USERS_TABLE_NAME} WHERE {ID_COL} = {user_id}')
    result = cursor.fetchall()
    close_connection_and_cursor(conn, cursor)
    if not result:
        return None
    return result[0][0]


def set_date_of_recieveing_messages(user_id: int, date: datetime):
    conn, cursor = get_connection_and_cursor()
    str_date = date.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(f'UPDATE {USERS_TABLE_NAME} SET {DATE_OF_RECIEVEING_MESSAGES} = '
        f'"{str_date}" WHERE {ID_COL} = {user_id}')
    commit_and_close_connection_and_cursor(conn, cursor)


def set_unactive_users_and_get_active_number(bot: TeleBot, silent_message: str) -> int:
    conn, cursor = get_connection_and_cursor()
    cursor.execute(f'SELECT {ID_COL}, {IS_ACTIVE} FROM {USERS_TABLE_NAME}')
    u_ids = cursor.fetchall()
    active_n = 0
    for id, is_active in u_ids:
        message = None
        try:
            message = bot.send_message(id, silent_message)
        except:
            if is_active:
                cursor.execute(f'UPDATE {USERS_TABLE_NAME} SET {IS_ACTIVE} = 0 WHERE {ID_COL} = {id}')
                conn.commit()
        else:
            active_n += 1
            if not is_active:
                cursor.execute(f'UPDATE {USERS_TABLE_NAME} SET {IS_ACTIVE} = 1 WHERE {ID_COL} = {id}')
                conn.commit()
        finally:
            if message != None:
                try:
                    bot.delete_message(message.chat.id, message.message_id)
                except:
                    pass    
    commit_and_close_connection_and_cursor(conn, cursor)
    return active_n


def set_origin(user_id: int, link: str):
    conn, cursor = get_connection_and_cursor()
    cursor.execute(
        f'UPDATE {USERS_TABLE_NAME} SET {ORIGIN} = "{link}" WHERE {ID_COL} = {user_id}')
    commit_and_close_connection_and_cursor(conn, cursor)


def get_origin_of(user_id: int) -> Union[str, None]:
    conn, cursor = get_connection_and_cursor()
    cursor.execute(f'SELECT {ORIGIN} FROM {USERS_TABLE_NAME} WHERE {ID_COL} = {user_id}')
    result = cursor.fetchall()
    close_connection_and_cursor(conn, cursor)
    if not result:
        return None
    return result[0][0]


def get_index_of_written_review(user_id: int) -> Union[int, None]:
    conn, cursor = get_connection_and_cursor()
    cursor.execute(f'SELECT {INDEX_OF_WRITTEN_REVIEW} FROM {USERS_TABLE_NAME} WHERE {ID_COL} = {user_id}')
    result = cursor.fetchall()
    close_connection_and_cursor(conn, cursor)
    if not result:
        return 0
    return result[0][0]


def set_index_of_written_review(user_id: int, index: int):
    conn, cursor = get_connection_and_cursor()
    cursor.execute(
        f'UPDATE {USERS_TABLE_NAME} SET {INDEX_OF_WRITTEN_REVIEW} = {index} WHERE {ID_COL} = {user_id}')
    commit_and_close_connection_and_cursor(conn, cursor)


def set_date_of_trying_to_buy(user_id: int, date: datetime):
    conn, cursor = get_connection_and_cursor()
    str_date = date.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(f'UPDATE {USERS_TABLE_NAME} SET {DATE_OF_PAYMENT_TRYING} = '
        f'"{str_date}" WHERE {ID_COL} = {user_id}')
    commit_and_close_connection_and_cursor(conn, cursor)


def date_of_trying_to_buy(user_id: int) -> Union[datetime, None]:
    conn, cursor = get_connection_and_cursor()
    cursor.execute(f'SELECT {DATE_OF_PAYMENT_TRYING} FROM {USERS_TABLE_NAME} WHERE {ID_COL} = {user_id}')
    result = cursor.fetchall()
    close_connection_and_cursor(conn, cursor)
    if not result:
        return None
    return result[0][0]


def set_as_asked_to_continue_payment(user_id: int):
    conn, cursor = get_connection_and_cursor()
    cursor.execute(f'UPDATE {USERS_TABLE_NAME} SET {IS_ASKED_TO_CONTINUE_PAYMENT} = 1 WHERE {ID_COL} = {user_id}')
    commit_and_close_connection_and_cursor(conn, cursor)


def is_asked_to_continue_payment(user_id: int) -> bool:
    conn, cursor = get_connection_and_cursor()
    cursor.execute(f'SELECT {IS_ASKED_TO_CONTINUE_PAYMENT} FROM {USERS_TABLE_NAME} WHERE {ID_COL} = {user_id}')
    result = cursor.fetchall()
    close_connection_and_cursor(conn, cursor)
    if not result:
        return False
    return result[0][0]