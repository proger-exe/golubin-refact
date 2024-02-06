import logging
from typing import Callable
from datetime import datetime, timedelta
import signal
from typing import Union
from Statistics.config import TIMESTAMP_FORMAT
from database import *
from threading import Thread

DB_TABLE = 'timed_sendings'
DUE_TIME = 'due_time'
TEXT = 'text'
BUTTON = 'button'
PHOTO_ID = 'photo_id'
BOT_ID = 'bot_id'
VIDEO_ID = 'video_id'
# prototype of the handler which will send scheudled messages. 
# Arguments: message(str), button(str|None), photo_id(str|None), bot_id(int), video_id(str|None)
__message_timer_handler: Callable[[str, Union[str, None], int, Union[str, None]], None] = None  
MAX_DUE_TIME_DIFFERENCE = 3 #seconds

def set_alarm_for_last_timed_messages(): 
    ''' bot calls it at start (because of restartings) '''
    connection, cursor = get_connection_and_cursor()
    cursor.execute(f'SELECT {DUE_TIME} FROM {DB_TABLE} ORDER BY {DUE_TIME}')
    result = cursor.fetchall()
    close_connection_and_cursor(connection, cursor)
    if not len(result) or not result[0]:
        return
    now = datetime.now()
    time: datetime = result[0][0]
    if time <= now:
        signal.alarm(1)
    else:
        signal.alarm((time - now).seconds)

def set_timer_for_message(
        due_time: datetime, text: str, button: Union[str, None], photo_id: Union[str, None], bot_id: int, video_id: Union[str, None]):
    connection, cursor = get_connection_and_cursor()

    str_time = due_time.strftime(TIMESTAMP_FORMAT)
    text = text.replace('"', '\\"')
    
    cursor.execute(f'SELECT COUNT({DUE_TIME}) FROM {DB_TABLE}')
    there_is_timers = cursor.fetchall()[0][0]
    

    if button:
        button = button.replace('"', '\\"')

    cursor.execute(
        f'INSERT INTO {DB_TABLE} VALUES("{str_time}", "{text}", ' + (f'"{button}", ' if button else 'NULL, ') + \
        (f'"{photo_id}"' if photo_id else 'NULL') + \
        f', {bot_id}, ' + (f'"{video_id}")' if video_id else 'NULL)')
    )
    commit_and_close_connection_and_cursor(connection, cursor)
    
    if not there_is_timers:
        t_now = datetime.now()
        delay = (due_time - t_now).seconds
        signal.alarm(delay)

def delete_message_timer(text: str):
    connection, cursor = get_connection_and_cursor()
    text.replace('"', '\\"')
    cursor.execute(F'DELETE FROM {DB_TABLE} WHERE {TEXT} = "{text}"')
    commit_and_close_connection_and_cursor(connection, cursor)

def set_message_timer_handler(handler: Callable[[str, Union[str, None], Union[str, None], int, Union[str, None]], int]):
    global __message_timer_handler
    __message_timer_handler = handler
    signal.signal(signal.SIGALRM, __overall_message_timer_handler)

def set_handler_of_message_sending_fails(handler: Callable[[str], None]):
    global __fail_to_send_message_handler
    __fail_to_send_message_handler = handler

def __overall_message_timer_handler(signum, stack):
    now = datetime.now()
    connection, cursor = get_connection_and_cursor()

    cursor.execute(f'SELECT COUNT({DUE_TIME}) FROM {DB_TABLE}')
    if cursor.fetchall()[0][0] == 1:
        cursor.execute(f'SELECT {TEXT}, {BUTTON}, {PHOTO_ID}, {BOT_ID}, {VIDEO_ID} FROM {DB_TABLE}')
        result = cursor.fetchall()[0]

        Thread(target = _try_to_call_message_handler, args = result).start()
        _delete_message_from_db(result[0], connection, cursor)
        set_next_timer(cursor)
        close_connection_and_cursor(connection, cursor)

        return
    
    time_period = (
        (now - timedelta(seconds = MAX_DUE_TIME_DIFFERENCE)).strftime(TIMESTAMP_FORMAT),
        (now + timedelta(seconds = MAX_DUE_TIME_DIFFERENCE)).strftime(TIMESTAMP_FORMAT)
    )
    cursor.execute(F'SELECT {TEXT}, {BUTTON}, {PHOTO_ID}, {BOT_ID}, {VIDEO_ID} FROM {DB_TABLE} '
        f'WHERE {DUE_TIME} BETWEEN "{time_period[0]}" AND "{time_period[1]}" OR {DUE_TIME} <= NOW()')
    result = cursor.fetchall()

    for message in result:
        Thread(target = _try_to_call_message_handler, args = message).start()
        _delete_message_from_db(message[0], connection, cursor)

    set_next_timer(cursor)
    close_connection_and_cursor(connection, cursor)

def set_next_timer(cursor: Cursor):
    cursor.execute(f'SELECT {DUE_TIME} FROM {DB_TABLE} ORDER BY {DUE_TIME} LIMIT 1')
    result = cursor.fetchall()
    
    if not len(result) or not result[0]:
        return
    
    time = result[0][0]
    signal.alarm((time - datetime.now()).seconds)

def _try_to_call_message_handler(message: str, button: Union[str, None], 
photo_id: Union[str, None], bot_id: int, video_id: Union[str, None]):
    try:
        __message_timer_handler(message, button, photo_id, bot_id, video_id)
    except:
        now = datetime.now()
        logging.critical(f'ERROR OCCURED WHILE SENDING SCHEDULED MESSAGE ({now}):', exc_info=True)

def _delete_message_from_db(text: str, 
connection: Connection, cursor: Cursor):
    text_for_check = text.replace('"', '\\"')
    cursor.execute(f'DELETE FROM {DB_TABLE} WHERE {TEXT} = "{text_for_check}"')
    del text_for_check
    connection.commit()