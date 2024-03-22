from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from src.apis.db import get_connection_and_cursor, commit_and_close_connection_and_cursor
from src.data.bot_config import ADD_EXTERNAL_CHAT, ADD_EXTERNAL_CHAT_CALLBACK, INVITE_ACCOUNT_TO_EXTERNAL_CHAT, SEND_LINK_TO_EXTERNAL_CHAT
from src.data.config import EXTERNAL_CHATS, CHAT_URL
from src.markups.users import add_chat_kb, back_button
from AdminBot.google_sheets import upload_new_chats

SPECIAL_ACCOUNT_FOR_CHATS = '@digital_agency365'

def save_chat(url: str = 'NULL') -> bool:
    conn, cursor = get_connection_and_cursor()
    url_is_in_db = False
    if url != 'NULL':
        chat_url_base = url.split('/')[-1]
        url = f'"{url}"'
        cursor.execute(f'SELECT COUNT({CHAT_URL}) FROM {EXTERNAL_CHATS} WHERE {CHAT_URL} LIKE "%{chat_url_base}"')
        url_is_in_db = cursor.fetchall()[0][0]
    if not url_is_in_db:
        cursor.execute(f'INSERT INTO {EXTERNAL_CHATS} VALUES(NULL, NULL, {url})')
    commit_and_close_connection_and_cursor(conn, cursor)
    return not url_is_in_db


# @dp.message_handler(lambda message: message.text == ADD_EXTERNAL_CHAT, state = '*')
handle_add_external_chat = lambda dp: dp.register_message_handler(add_external_chat, text=ADD_EXTERNAL_CHAT, state="*")
async def add_external_chat(message: Message, state: FSMContext):
    await state.finish()
    await message.answer(
        'Чтобы добавить чат, из которого, возможно, в будущем мы будем пересылать заявки, '
        'вы можете либо пригласить в него наш специальный аккаунт, '
        'либо отправить нам ссылку на чат.\nВыберите действие:',
        reply_markup = add_chat_kb
    )

# @dp.callback_query_handler(lambda callback: callback.data == ADD_EXTERNAL_CHAT_CALLBACK, state = '*')
handle_add_external_chat_callback = lambda dp: dp.register_callback_query_handler(add_external_chat_callback, text=ADD_EXTERNAL_CHAT_CALLBACK, state="*")
async def add_external_chat_callback(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    try:
        await callback.message.edit_text(
            'Чтобы добавить чат, из которого, возможно, в будущем мы будем пересылать заявки, '
            'вы можете либо пригласить в него наш специальный аккаунт, '
            'либо отправить нам ссылку на чат.\nВыберите действие:',
            reply_markup = add_chat_kb
        )
    except:
        pass

# @dp.callback_query_handler(lambda callback: callback.data == INVITE_ACCOUNT_TO_EXTERNAL_CHAT, state = '*')
handle_send_instruction_about_inviting_account = lambda dp: dp.register_callback_query_handler(send_instruction_about_inviting_account, text=INVITE_ACCOUNT_TO_EXTERNAL_CHAT, state="*")
async def send_instruction_about_inviting_account(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    try:
        await callback.message.edit_text(f'Пригласите {SPECIAL_ACCOUNT_FOR_CHATS} в чат.', reply_markup = back_button)
    except: 
        pass

# @dp.callback_query_handler(lambda callback: callback.data == SEND_LINK_TO_EXTERNAL_CHAT, state = '*')
handle_get_url_to_external_chat = lambda dp: dp.register_callback_query_handler(get_url_to_external_chat, text=SEND_LINK_TO_EXTERNAL_CHAT, state="*")
async def get_url_to_external_chat(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    try:
        await callback.message.edit_text('Отправьте ссылку на чат (можно несколько через пробел).', reply_markup = back_button)
    except:
        pass
    await state.set_state("get_url_to_new_chat")

# @dp.message_handler(state = "get_url_to_new_chat"")
handle_save_chat_by_url = lambda dp: dp.register_message_handler(save_chat_by_url, state="get_url_to_new_chat")
async def save_chat_by_url(message: Message, state: FSMContext):
    saved_links = []
    for link in message.text.split():
        if not link.startswith('t.me/') and not link.startswith('@') and not link.startswith('http://t.me/') \
        and not link.startswith('https://t.me/'):
            await message.answer(f'Не удаётся распознать ссылку {link}. (Отправьте другую либо /cancel)')
            continue
        link = link.replace('@', 'https://t.me/')
        if save_chat(url = link):
            saved_links.append(link)
        else:
            await message.answer(f'{link} уже сохранён.')
    if saved_links:
        await state.finish()
        await message.answer('Чат сохранён в базе.' if len(saved_links) == 1 else \
                                f'{len(saved_links)} ссылок сохранены в базу.')
        upload_new_chats(saved_links)


def register_handlers(dp):
    handle_get_url_to_external_chat(dp)
    handle_add_external_chat(dp)
    handle_add_external_chat_callback(dp)
    handle_send_instruction_about_inviting_account(dp)
    handle_save_chat_by_url(dp)