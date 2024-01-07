from datetime import datetime
from random import randint
from typing import Optional
import typing
from aiogram.dispatcher import FSMContext
from src.apis.db.user import client_has_year_subscribe
from src.keyboards.user import manage_account_keyboard
from src.utils.client import Client
from aiogram.types import Message, CallbackQuery
from src.apis.db.accounts import *
from src.data.bot_data import *
from src.apis.bot_get_nick import get_nick
from src.callbacks import accounts_manage
from src.utils.errors import MessageInvalid


# dp.register_message_handler(text = ACCOUNTS_BUTTON, state = '*')
async def manage_accounts_message_handler(message: Message, state: FSMContext):
    admin = get_admin_of_account(message.from_user.id)
    
    if admin:
        await message.answer('Вы не можете подключать аккаунты, '
            f'так как ваш аккаунт уже подключен к {await get_nick((await message.bot.get_chat_member(admin, admin)).user)}')
        return
    
    await manage_accounts(message.from_user.id, state, message = message)


async def manage_accounts_callback_handler(callback: CallbackQuery, state: FSMContext):
    await manage_accounts(callback.from_user.id, state, callback = callback)


async def manage_accounts(client_id: int, state: FSMContext, call: Optional[CallbackQuery] = None, message: Optional[Message] = None 
):
    if not message and not call:
        raise ValueError('There is no whether message or callback setted in arguments')

    if message:
        answer = message.answer
        bot = message.bot 
    else:
        answer = call.message.answer
        bot = call.message.bot 
    
    await state.finish()
    text = ''
    has_year_sub = client_has_year_subscribe(client_id)
    
    if not has_year_sub:
        text = 'Для подключения дополнительных аккаунтов у вас должна быть оплачена годовая подписка'
        try:
            await answer(text)
        except MessageInvalid:
            return
    
    account_ids = {}
    current_max_number_of_accounts = 0
    num_of_accounts = 0

    for category in config.message_categories:
        accs = get_all_accounts_of(client_id, category)
        if accs:
            num_of_accounts += len(accs)
            account_ids[category] = accs
        if client_has_year_subscribe(client_id, category):
            current_max_number_of_accounts += accounts_manage.MAX_NUMBER_OF_ACCOUNTS
    
    if not account_ids:
        text += f'\nУ вас нет аккаунтов. Максимально допустимое количество аккаунтов: {accounts_manage.MAX_NUMBER_OF_ACCOUNTS} ' \
        'для каждой категории, по которой у вас оплачена годовая подписка'
            
    else:
        accounts = await get_clients_account_nick_text(account_ids, bot=bot)
        
        yet_allowed_number_of_accounts = str(current_max_number_of_accounts - num_of_accounts)
        
        ending = 'аккаунт'
        ending += 'а' if yet_allowed_number_of_accounts[-1] in ('2', '3', '4') else 'ов'
        # я знаю что это не сделало его читабельнее. Он хотябы выглядит как код.
        
        ending = f'{yet_allowed_number_of_accounts} {ending}'
        text += (
            f'\nВаши текущие аккаунты:{accounts}'
            '\nМаксимально допустимое количество аккаунтов для каждой '
            f'категории: {accounts_manage.MAX_NUMBER_OF_ACCOUNTS}. Вы можете подключить ещё {ending}'
        )
            
    try:
        await answer(text, reply_markup = manage_account_keyboard(account_ids, has_year_sub), parse_mode = 'HTML')   
    except MessageInvalid:
        return

