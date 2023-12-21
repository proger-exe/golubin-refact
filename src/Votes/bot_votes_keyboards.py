import datetime
import logging
from aiogram.utils.exceptions import *
from src.apis.db.accounts import get_admin_of_account
from src.utils.client import Client
import typing
from datetime import date
from typing import Union
from aiogram import Bot
from aiogram.types import *

from aiogram.dispatcher.filters.state import StatesGroup, State
from src.data.config import *
from src.data.config import SENDER_BOT_ID, msg_categories
from .config import *
from src.data.bot_data import *
from . import Vote
from src.apis.ClientsData import Accounts, StopWords
from src.apis.bot_get_nick import get_nick
from src.utils import message_deleting

class States(StatesGroup):
    get_period_for_votes_statistics = State()


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




def generate_vote_keyboard(relative_msg_id: Union[int, str]) -> InlineKeyboardMarkup:
    return __generate_vote_keyboard(False, relative_msg_id)

def __generate_vote_keyboard(message_is_forwarded: bool, relative_msg_id: Union[int, str]) -> InlineKeyboardMarkup:
    message_is_forwarded = 1 if message_is_forwarded else 0
    relative_msg_id = str(relative_msg_id)
    msg_id_offset = str(-message_is_forwarded)
    vote_keyboard = InlineKeyboardMarkup()
    vote_keyboard.row(
        InlineKeyboardButton('Целевой', callback_data = CALLBACK_SEP.join(
            [MESSAGE_VOTE, str(TARGET), msg_id_offset, relative_msg_id])),
        InlineKeyboardButton('Не целевой', 
            callback_data = CALLBACK_SEP.join(
                [MESSAGE_VOTE, str(NOT_TARGET), msg_id_offset, relative_msg_id]))
    )
    vote_keyboard.row(
        InlineKeyboardButton('Спам', 
            callback_data = CALLBACK_SEP.join(
                [MESSAGE_VOTE, str(SPAM), msg_id_offset, relative_msg_id])),
        InlineKeyboardButton('ЧC',
            callback_data = CALLBACK_SEP.join(
                [MESSAGE_VOTE, str(SPAM_ONLY_FOR_CLIENT), msg_id_offset, relative_msg_id])
        )
    )
    return vote_keyboard

def generate_vote_keyboard_for_forwarded_message(relative_msg_id: Union[int, str]) -> InlineKeyboardMarkup:
    return __generate_vote_keyboard(True, relative_msg_id)

def get_spam_button_for_forwarded_message(relative_msg_id: Union[int, str]) -> InlineKeyboardButton:
    return __get_spam_button(True, relative_msg_id)

def __get_spam_button(message_is_forwarded: bool, relative_msg_id: Union[int, str]) -> InlineKeyboardButton:
    message_is_forwarded = 1 if message_is_forwarded else 0
    msg_id_offset = str(-message_is_forwarded)
    return InlineKeyboardButton('Спам', 
        callback_data = CALLBACK_SEP.join([MESSAGE_VOTE, str(SPAM), msg_id_offset, str(relative_msg_id)]))

def get_spam_button(relative_msg_id: Union[int, str]) -> InlineKeyboardButton:
    return __get_spam_button(False, relative_msg_id)

async def __edit_pressed_vote_keyboard(callback: CallbackQuery, bot: Bot, msg_id_offset: Union[int, str], 
relative_msg_id: Union[int, str], is_target: bool, category: int) -> InlineKeyboardMarkup:
    '''set an emoji on the  pressed button '''
    if '✅' in callback.message.reply_markup.inline_keyboard[0][0].text or \
       '⛔️' in callback.message.reply_markup.inline_keyboard[0][1].text:
       return
    vote_keyboard = InlineKeyboardMarkup()
    msg_id_offset = str(msg_id_offset)
    relative_msg_id = str(relative_msg_id)
    vote_keyboard.row(
        InlineKeyboardButton('Целевой ' + ('✅' if is_target else ''), callback_data = CALLBACK_SEP.join(
            [MESSAGE_VOTE, str(TARGET), msg_id_offset, relative_msg_id])),
        InlineKeyboardButton('Не целевой ' + ('' if is_target else '⛔️'), 
            callback_data = CALLBACK_SEP.join(
                [MESSAGE_VOTE, str(NOT_TARGET), msg_id_offset, relative_msg_id]))
    )
    vote_keyboard.row(
        InlineKeyboardButton('Спам', 
            callback_data = CALLBACK_SEP.join(
                [MESSAGE_VOTE, str(SPAM), msg_id_offset, relative_msg_id])),
        InlineKeyboardButton('ЧC',
            callback_data = CALLBACK_SEP.join(
                [MESSAGE_VOTE, str(SPAM_ONLY_FOR_CLIENT), msg_id_offset, relative_msg_id])
        )
    )
    if callback.from_user.id in USERS_THAT_ALLOWED_TO_DELETE_MESSAGES:
        vote_keyboard.add(message_deleting.delete_message_kb(int(relative_msg_id)).inline_keyboard[0][0])
    admin_id = callback.from_user.id
    accounts = Accounts.get_all_accounts_of(admin_id, category)
    if not accounts:
        admin_id = get_admin_of_account(admin_id, category)
        if admin_id:
            accounts = Accounts.get_all_accounts_of(admin_id, category)
            accounts.pop(accounts.index(callback.from_user.id))
            accounts.append(admin_id)
    try:
        
        await callback.message.edit_reply_markup(vote_keyboard)
    except:
        logging.error('Failed to edit vote keyboard after pressing a button: ', exc_info=True)
    for i in accounts:
        info = message_deleting.get_sended_message_data(int(relative_msg_id), SENDER_BOT_ID + category, i)
        if not info or not info[0]:
            continue
        msg_id = info[0][1]
        await bot.edit_message_reply_markup(i, msg_id, reply_markup = vote_keyboard)

async def message_vote_callback(bot: Bot, callback: CallbackQuery, category: int):
    Bot.set_current(bot)
    _, vote_type, msg_id_offset, relative_msg_id = callback.data.split(CALLBACK_SEP)
    vote_type, msg_id_offset, relative_msg_id = int(vote_type), int(msg_id_offset), int(relative_msg_id)
    if vote_type == SPAM:
        orig_msg = await bot.forward_message(DEVELOPER_ID, callback.from_user.id, 
            callback.message.message_id + msg_id_offset)
        kb = InlineKeyboardMarkup()
        msg_id_str = str(callback.message.message_id)
        kb.row(
            InlineKeyboardButton(
                'Спам', 
                callback_data = CALLBACK_SEP.join(
                    [CONFIRM_SPAM, THROW_MSG_TO_SPAM, str(callback.from_user.id), 
                        str(relative_msg_id), str(category), msg_id_str]
                )
            ),
            InlineKeyboardButton(
                'Удалить', 
                callback_data = CALLBACK_SEP.join(
                    [CONFIRM_SPAM, JUST_DEL_MSG, str(callback.from_user.id), 
                        str(relative_msg_id), str(category), msg_id_str]
                )
            )
        )
        kb.add(
            InlineKeyboardButton(
                'Отказ', 
                callback_data = CALLBACK_SEP.join(
                    [DISCARD_SPAM, str(callback.from_user.id), msg_id_str, str(category)])
            )
        )
        await callback.message.edit_text(callback.message.text + '\n\nАдминистраторы проверят сообщение '
            'и заблокируют пользователя, если это спам.')
        paying_bot = Bot(PAYING_BOT_TOKEN)
        # trying to get text of considered message ( if it is forwarded, so keyboard is clicked from the additional 
        # message)
        text = f'Пользователь {await get_nick(callback.from_user)} считает, '\
            f'что это сообщение ({message_category_names[category]}) спам:\n\n{orig_msg.text}\n'\
            '\nПодвердить блокировку пользователя?'
        try:
            await orig_msg.delete()
        except:
            pass
        try:
            await paying_bot.send_message(
                EUGENIY_ID if not TESTING else callback.from_user.id, 
                text, 
                reply_markup = kb, parse_mode = 'HTML'
            )
        except:
            logging.critical(f'Failed to send spam-suggested-message to admin:\n"{text}"', exc_info=True)
        await (await paying_bot.get_session()).close()
    client_is_allowed_to_set_votes = check_if_client_is_allowed_to_get_vote_buttons(callback.from_user.id, category) 
    if vote_type != SPAM and not client_is_allowed_to_set_votes:
        await callback.answer('У вас больше нет доступа к кнопкам для отметки сообщений')
        return
    if not client_is_allowed_to_set_votes:
        return
    message_id = callback.message.message_id + msg_id_offset
    votes = Vote.findByFilter(message_id = message_id, user_id = callback.from_user.id, category = category)
    if votes:
        await callback.answer(f'Вы уже отметили это сообщение как {vote_type_names[votes[0].vote_type]} ранее')
        return
    try:
        # there can not be SPAM_ONLY_FOR_CLIENT-vote-type (-2) in db, only SPAM(-1)
        vote = Vote(date.today(), callback.from_user.id, category, message_id, max(vote_type, SPAM))
        vote.save()
    except Exception as e:
        logging.error(f'Failed to save vote {vote.user_id, vote.vote_type, vote.category}: ', exc_info=True)
        await callback.answer('Произошла ошибка')
    else:
        if vote_type == SPAM_ONLY_FOR_CLIENT:
            if callback.message.entities:
                nick = ''
                for entity in callback.message.entities[::-1]:
                    if entity.type in ('mention', 'url', 'email', 'phone_number', 'text_mention'):
                        nick = entity.get_text(callback.message.text)
                        break
                client = Client(callback.from_user.id, None, None, category)
                if nick and not nick in StopWords.get_stop_words(client): 
                    StopWords.add_stop_words(client, [nick.lower()])
                    await callback.answer(f'Пользователь {nick} заблокирован для вас')
                else:
                     callback.answer('Не удалось определить пользователя, чтобы его заблокировать')
            try:
                await callback.message.delete()
                if message_id != 0:
                    await callback.bot.delete_message(callback.from_user.id, message_id)
            except:
                logging.error(
                    f'Failed to delete spam message ({message_id}, {msg_categories[category]}) '\
                    f'(requested from {callback.from_user.id}):',
                    exc_info = True
                )
                await callback.answer('Произошла ошибка при попытке удалить сообщение')
                return
            return
        await callback.answer(f'Сообщение отмечено как {vote_type_names[vote_type]}')
    if vote_type == TARGET or vote_type == NOT_TARGET:
        await __edit_pressed_vote_keyboard(callback, bot, msg_id_offset, relative_msg_id, vote_type, category)

def check_if_client_is_allowed_to_get_vote_buttons(client_id: int, category: int = None) -> bool:
    if client_id == EUGENIY_ID:
        return True
    admin = get_admin_of_account(client_id)
    if admin and client_has_year_subscribe(admin, category):
        return True
    return client_has_year_subscribe(client_id, category)

async def __generate_statistics_texts_for_message(
    bot: Bot, client_id: int, period: typing.Tuple[date, date]
) -> typing.List[str]:
    statistics_texts = []
    for category in message_categories:
        current_text = ''
        accounts = [client_id] + Accounts.get_all_accounts_of(client_id)
        current_statistics = {TARGET: 0, NOT_TARGET: 0, SPAM: 0}
        for i, account in enumerate(accounts):
            try:
                nickname = await get_nick((await bot.get_chat_member(account, account)).user)
            except:
                nickname = f'{account}'
            votes = Vote.findByFilter(period = period, user_id = account, category = category)
            if not votes:
                continue
            account_statistics = {TARGET: 0, NOT_TARGET: 0, SPAM: 0}
            for vote in votes:
                account_statistics[vote.vote_type] += 1
                current_statistics[vote.vote_type] += 1
            current_text += \
                f'<i><b>{nickname}</b></i>: отмечено целевых : <b>{account_statistics[TARGET]}</b> '\
                f'не целевых : <b>{account_statistics[NOT_TARGET]}</b> '\
                f'спам : <b>{account_statistics[SPAM]}</b>'
            current_text += '\n---------------------------\n' if i < len(accounts) - 1 else '\n'
        if not current_text:
            continue
        current_text = f'<b>{message_category_names[category]}</b>\n' + current_text
        if len(accounts) > 1:
            current_text += f'\nВсего:\nЦелевых - <b>{current_statistics[TARGET]}</b>\nНе целевых - <b>{current_statistics[NOT_TARGET]}</b>'
        target_percent = '{0:.1f}'.format(
            current_statistics[TARGET] / \
            max(1, current_statistics[TARGET] + current_statistics[NOT_TARGET] + current_statistics[SPAM]) * 100
        )
        current_text += f'\n% целевых - <b>{target_percent}%</b>'
        statistics_texts.append(current_text)
    return statistics_texts
