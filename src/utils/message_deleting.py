from shutil import rmtree
from typing import Tuple, Union
import logging
import aiogram
from src.data.bot_data import CALLBACK_SEP, USERS_THAT_ALLOWED_TO_DELETE_MESSAGES, bot_tokens
from src.apis import *
from src.data.config import *
from aiogram import Bot, Dispatcher
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.exceptions import *
from telebot.types import InlineKeyboardMarkup as OldKbMarkup

DELETE_MESSAGE = 'DELETE_MSG'

def delete_message_kb(
    relative_msg_id: int,
    kb_type: type = InlineKeyboardMarkup,
    bt_type: type = InlineKeyboardButton
) -> Union[InlineKeyboardMarkup, OldKbMarkup]:
    kb =  kb_type()
    kb.add(bt_type('Удалить', callback_data = DELETE_MESSAGE + CALLBACK_SEP + str(relative_msg_id)))
    return kb

def get_index_for_new_message() -> int:
    conn, cursor = get_connection_and_cursor()
    # get the last message index
    cursor.execute(
        f'SELECT distinct({RELATIVE_MSG_ID}) FROM {SENDED_MESSAGES} ORDER BY {RELATIVE_MSG_ID} DESC LIMIT 1')
    result = cursor.fetchall()
    index = 0
    if result:
        index = result[0][0] + 1
    # make a gag to make sure that this index won't be used by any other bots or message senders
    cursor.execute(F'INSERT INTO {SENDED_MESSAGES} VALUES ({index}, -1, 0, 0, -1)')
    # delete the last gag
    cursor.execute(F'DELETE FROM {SENDED_MESSAGES} WHERE {RELATIVE_MSG_ID} = {index-1} AND {BOT_ID} = -1')
    commit_and_close_connection_and_cursor(conn, cursor)
    return index

def save_sended_message_data(
    relative_message_id: int, client_id: int, sended_message_id: int, bot_id: int, inside_bot_msg_id: int = -1
):
    conn, cursor = get_connection_and_cursor()
    cursor.execute(f'INSERT INTO {SENDED_MESSAGES} VALUES ({relative_message_id}, {inside_bot_msg_id}, {client_id}, '
        f'{sended_message_id}, {bot_id})')
    commit_and_close_connection_and_cursor(conn, cursor)

def get_sended_message_data(relative_message_id: int, bot_id: int, user_id: int = None) -> tuple:
    conn, cursor = get_connection_and_cursor()
    cursor.execute(f'SELECT {RECIEVER_ID}, {SENDED_MSG_ID} FROM {SENDED_MESSAGES} WHERE '
        f'{RELATIVE_MSG_ID} = {relative_message_id} AND {BOT_ID} = {bot_id}' + (
            '' if user_id == None else f' AND {RECIEVER_ID} = {user_id}')
    )
    result = cursor.fetchall()
    close_connection_and_cursor(conn, cursor)
    return result
 
def get_relative_message_id_by_inside_bot_msg_id(inside_bot_msg_id: int, bot_id: int) -> int:
    conn, cursor = get_connection_and_cursor()
    cursor.execute(f'SELECT DISTINCT({RELATIVE_MSG_ID}) FROM {SENDED_MESSAGES} WHERE '
        f'{INSIDE_BOT_MSG_ID} = {inside_bot_msg_id} AND {BOT_ID} = {bot_id}')
    result = cursor.fetchall()
    close_connection_and_cursor(conn, cursor)
    if not result:
        return -1
    return result[0][0]

def get_sended_message_data_by_inside_bot_msg_id(inside_bot_msg_id: int, bot_id: int) -> tuple:
    conn, cursor = get_connection_and_cursor()
    cursor.execute(f'SELECT {RECIEVER_ID}, {SENDED_MSG_ID} FROM {SENDED_MESSAGES} WHERE '
        f'{INSIDE_BOT_MSG_ID} = {inside_bot_msg_id} AND {BOT_ID} = {bot_id}')
    result = cursor.fetchall()
    close_connection_and_cursor(conn, cursor)
    return result

def delete_saved_message_data(relative_msg_id: int, bot_id: int):
    conn, cursor = get_connection_and_cursor()
    cursor.execute(
        f'DELETE FROM {SENDED_MESSAGES} WHERE {RELATIVE_MSG_ID} = {relative_msg_id} AND {BOT_ID} IN ({bot_id}, -1)'
    )
    commit_and_close_connection_and_cursor(conn, cursor)

async def delete_sended_msg(bot: Bot, sended_msg_data: tuple, except_for: Tuple[int, int]= ()) -> tuple:
    succesfully = unsuccesfully = total = 0
    for client_id, msg_id in sended_msg_data:
        if (client_id, msg_id) == except_for or client_id in USERS_THAT_ALLOWED_TO_DELETE_MESSAGES:
            continue
        total += 1
        try:
            await bot.delete_message(client_id, msg_id)
        except (ChatNotFound, BotBlocked, MessageToDeleteNotFound, MessageCantBeDeleted):
            unsuccesfully += 1
        except Exception as e:
            unsuccesfully += 1
            logging.error(f'Failed to delete message ({client_id}, {msg_id}): '+str(e), exc_info = True)
            continue
        else: 
            succesfully += 1
    return succesfully, unsuccesfully, total

async def del_sended_message_by_callback_query(call: CallbackQuery, bot: Bot, bot_id: int):
    message_info = call.data.split(CALLBACK_SEP)[1]
    relative_message_index = int(message_info)
    sended_msg_data = get_sended_message_data(relative_message_index, bot_id)
    if not sended_msg_data:
        try:
            await bot.edit_message_text('Сообщение уже было удалено ранее', call.from_user.id, call.message.message_id)
        except:
            await bot.send_message(call.from_user.id, 'Сообщение уже было удалено ранее')
        return
    try:
        await bot.edit_message_text('Сообщение удаляется, ждите...', call.from_user.id, call.message.message_id)
    except:
        await bot.send_message(call.from_user.id, 'Сообщение удаляется, ждите...')
    await delete_message_and_ge
    t_info_about_it_to_admin(bot, bot_id, sended_msg_data, relative_message_index, call)
    delete_sended_message_from_temp(bot_id, relative_message_index)

async def delete_message_and_get_info_about_it_to_admin(
    bot: Bot, 
    bot_id: int,
    sended_msg_data: tuple, 
    relative_message_id: int, 
    call: CallbackQuery
):
    try:
        succesfully, unsuccesfully, total = (
            await delete_sended_msg(bot, sended_msg_data, (call.from_user.id, call.message.message_id)))
    except Exception as e:
        logging.error(
            f'Failed to delete messages for original message id = {relative_message_id} from {call.from_user.id}: ',
            exc_info = True
        )
        try:
            await bot.edit_message_text(
                f'Не удалось удалить сообщение (id = {relative_message_id})',
                call.from_user.id, call.message.message_id
            )
        except:
            await bot.send_message(
                call.from_user.id,
                f'Не удалось удалить сообщение (id = {relative_message_id})',
            )
    else:
        text = f'Всего разослано: <b>{total}</b>\nУдалено: <b>{succesfully}</b>'\
            f'\nНе удалось удалить: <b>{unsuccesfully}</b>'
        try:
            await bot.edit_message_text(
                text,
                call.from_user.id, call.message.message_id, 
                parse_mode = 'HTML'
            )
        except:
            await bot.send_message(call.from_user.id, text, parse_mode = 'HTML')
            try:
                await call.message.delete()
            except: 
                pass
        delete_saved_message_data(relative_message_id, bot_id)

def delete_sended_message_from_temp(bot_id: int, relative_message_index: int):
    if bot_id != PAYING_BOT_ID:
        try:
            if not TESTING:
                try:
                    rmtree(
                        NEW_MESSAGES_PATH+SENDED_DIR+msg_categories[bot_id-SENDER_BOT_ID]+f'/{relative_message_index}')
                except FileNotFoundError:
                    pass
            else:
                try:
                    rmtree(
                        TEMP_MESSAGES_PATH+SENDED_DIR+msg_categories[bot_id-SENDER_BOT_ID]+f'/{relative_message_index}')
                except FileNotFoundError:
                    pass
        except Exception as e:
            logging.error(
                f'Failed to delete message`s directory for ({relative_message_index}): '+str(e), exc_info = True)

def get_relative_message_id(bot_id: int, sent_msg_id: int, user_id: int) -> Union[int, None]:
    conn, cursor = get_connection_and_cursor()
    cursor.execute(f'SELECT {RELATIVE_MSG_ID} FROM {SENDED_MESSAGES} WHERE {RECIEVER_ID} = {user_id} AND '
        f'{SENDED_MSG_ID} = {sent_msg_id} AND {BOT_ID} = {bot_id}')
    result = cursor.fetchall()
    close_connection_and_cursor(conn, cursor)
    if not result:
        return None
    else:
        return result[0][0]

async def delete_message_from_inside_bot(inside_bot_message_id: int, category: int, bot: aiogram.Bot):
    bot_id = SENDER_BOT_ID + category
    msg_data = get_sended_message_data_by_inside_bot_msg_id(inside_bot_message_id, bot_id)
    succesfully, _, total =  await delete_sended_msg(bot, msg_data)
    if not succesfully and total > 0:
        logging.error(
            f'Failed to delete message from inside {msg_categories[category]} channel: {inside_bot_message_id}')
    else:
        relative_message_id = get_relative_message_id_by_inside_bot_msg_id(inside_bot_message_id, bot_id)
        delete_saved_message_data(relative_message_id, bot_id)
        delete_sended_message_from_temp(bot_id, relative_message_id)

def init_callbacks(dp: Dispatcher, bot_id: int): # bot_id can be either PAYING_BOT_ID or SENDER_BOT_ID (+category id)
    bot = dp.bot

    @dp.callback_query_handler(lambda c: c.data.startswith(DELETE_MESSAGE))
    async def message_deleting_query_handler(call: CallbackQuery):
        await del_sended_message_by_callback_query(call, bot, bot_id)
        

async def del_spam_message(relative_msg_id: int, category: int, not_delete: typing.Tuple[int, int])\
-> typing.Tuple[int, int, int]:
    b = Bot(bot_tokens[category])
    try:
        data = get_sended_message_data(relative_msg_id, SENDER_BOT_ID + category)
        succesfully, unsuccesfully, total = await delete_sended_msg(b, data, not_delete)
        await (await b.get_session()).close()
        del data
    except:
        logging.critical(f'Failed to delete spam message by relative message id:', exc_info = True)
        return (0, 0, 0)

    delete_saved_message_data(relative_msg_id, SENDER_BOT_ID + category)
    return succesfully, unsuccesfully, total
