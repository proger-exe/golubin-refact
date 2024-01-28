import logging
import typing
from datetime import date
from typing import Optional, Union
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from src.apis.bot_get_nick import get_nick
from src.data.bot_data import CALLBACK_SEP, DEVELOPER_ID, EUGENIY_ID, PAYING_BOT_TOKEN, USERS_THAT_ALLOWED_TO_DELETE_MESSAGES
from src.data.config import *
from src.apis.db.accounts import get_all_accounts_of, get_admin_of_account
from src.apis.ClientsData import StopWords
from src.utils import message_deleting
from db import check_if_client_is_allowed_to_get_vote_buttons
from src.utils.Votes.config import CONFIRM_SPAM, DISCARD_SPAM, JUST_DEL_MSG, NOT_TARGET, SPAM, SPAM_ONLY_FOR_CLIENT, TARGET, THROW_MSG_TO_SPAM, vote_type_names
from db.users_votes import Vote

# ...

def generate_vote_keyboard(relative_msg_id: Union[int, str]) -> InlineKeyboardMarkup:
    """
    Generates an inline keyboard for voting on a message.

    Parameters:
        relative_msg_id (Union[int, str]): The relative message ID to associate the vote with.

    Returns:
        InlineKeyboardMarkup: The generated inline keyboard.
    """
    
    
    return __generate_vote_keyboard(False, relative_msg_id)

def __generate_vote_keyboard(message_is_forwarded: bool, relative_msg_id: Union[int, str]) -> InlineKeyboardMarkup:
    """
    Generates an inline keyboard for voting on a forwarded message.

    Parameters:
        relative_msg_id (Union[int, str]): The relative message ID to associate the vote with.

    Returns:
        InlineKeyboardMarkup: The generated inline keyboard.
    """    

    vote_keyboard = InlineKeyboardMarkup()

    message_is_forwarded = int(message_is_forwarded)
    relative_msg_id = str(relative_msg_id)
    msg_id_offset = str(-message_is_forwarded)

    vote_keyboard.row(
        InlineKeyboardButton('Целевой', callback_data=CALLBACK_SEP.join([MESSAGE_VOTE, str(TARGET), msg_id_offset, relative_msg_id])),
        InlineKeyboardButton('Не целевой', callback_data=CALLBACK_SEP.join([MESSAGE_VOTE, str(NOT_TARGET), msg_id_offset, relative_msg_id]))
    )
    vote_keyboard.row(
        InlineKeyboardButton('Спам', callback_data=CALLBACK_SEP.join([MESSAGE_VOTE, str(SPAM), msg_id_offset, relative_msg_id])),
        InlineKeyboardButton('ЧC', callback_data=CALLBACK_SEP.join([MESSAGE_VOTE, str(SPAM_ONLY_FOR_CLIENT), msg_id_offset, relative_msg_id]))
    )
    return vote_keyboard

def generate_vote_keyboard_for_forwarded_message(relative_msg_id: Union[int, str]) -> InlineKeyboardMarkup:
    """
    Generates an inline keyboard for voting on a forwarded message.

    Parameters:
        relative_msg_id (Union[int, str]): The relative message ID to associate the vote with.

    Returns:
        InlineKeyboardMarkup: The generated inline keyboard.
    """    
    
    return __generate_vote_keyboard(True, relative_msg_id)

def get_spam_button_for_forwarded_message(relative_msg_id: Union[int, str]) -> InlineKeyboardButton:
    """
    Retrieves the spam button for voting on a forwarded message.

    Parameters:
        relative_msg_id (Union[int, str]): The relative message ID to associate the vote with.

    Returns:
        InlineKeyboardButton: The spam button.
    """    
    
    return __get_spam_button(True, relative_msg_id)

def __get_spam_button(message_is_forwarded: bool, relative_msg_id: Union[int, str]) -> InlineKeyboardButton:
    """
    Retrieves the spam button for voting on a forwarded message.

    Parameters:
        relative_msg_id (Union[int, str]): The relative message ID to associate the vote with.

    Returns:
        InlineKeyboardButton: The spam button.
    """    
    
    message_is_forwarded = int(message_is_forwarded) 
    msg_id_offset = str(-message_is_forwarded)
    return InlineKeyboardButton('Спам', callback_data=CALLBACK_SEP.join([MESSAGE_VOTE, str(SPAM), msg_id_offset, str(relative_msg_id)]))

def get_spam_button(relative_msg_id: Union[int, str]) -> InlineKeyboardButton:
    return __get_spam_button(False, relative_msg_id)

async def __edit_pressed_vote_keyboard(callback: CallbackQuery, bot: Bot, msg_id_offset: Union[int, str], relative_msg_id: Union[int, str], is_target: bool, category: int):
    """
    Edits the inline keyboard after a vote button is pressed.

    Parameters:
        callback (CallbackQuery): The callback query containing vote information.
        bot (Bot): The bot instance.
        msg_id_offset (Union[int, str]): The message ID offset.
        relative_msg_id (Union[int, str]): The relative message ID.
        is_target (bool): Indicates if the vote is for a target.
        category (int): The message category.

    Returns:
        InlineKeyboardMarkup: The edited inline keyboard.
    """    
    
    '''set an emoji on the  pressed button '''
    if '✅' in callback.message.reply_markup.inline_keyboard[0][0].text or '⛔️' in callback.message.reply_markup.inline_keyboard[0][1].text:
        return
    vote_keyboard = InlineKeyboardMarkup()
    msg_id_offset = str(msg_id_offset)
    relative_msg_id = str(relative_msg_id)
    vote_keyboard.row(
        InlineKeyboardButton('Целевой ' + ('✅' if is_target else ''), callback_data=CALLBACK_SEP.join([MESSAGE_VOTE, str(TARGET), msg_id_offset, relative_msg_id])),
        InlineKeyboardButton('Не целевой ' + ('' if is_target else '⛔️'), callback_data=CALLBACK_SEP.join([MESSAGE_VOTE, str(NOT_TARGET), msg_id_offset, relative_msg_id]))
    )
    vote_keyboard.row(
        InlineKeyboardButton('Спам', callback_data=CALLBACK_SEP.join([MESSAGE_VOTE, str(SPAM), msg_id_offset, relative_msg_id])),
        InlineKeyboardButton('ЧC', callback_data=CALLBACK_SEP.join([MESSAGE_VOTE, str(SPAM_ONLY_FOR_CLIENT), msg_id_offset, relative_msg_id])
        )
    )
    if callback.from_user.id in USERS_THAT_ALLOWED_TO_DELETE_MESSAGES:
        vote_keyboard.add(message_deleting.delete_message_kb(int(relative_msg_id)).inline_keyboard[0][0])
    admin_id = callback.from_user.id
    accounts = get_all_accounts_of(admin_id, category)
    if not accounts:
        admin_id = get_admin_of_account(admin_id, category)
        if admin_id:
            accounts = get_all_accounts_of(admin_id, category)
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
        await bot.edit_message_reply_markup(i, msg_id, reply_markup=vote_keyboard)

async def message_vote_callback(bot: Bot, callback: CallbackQuery, category: int):
    """
    Handles callback queries for voting on messages.

    Parameters:
        bot (Bot): The bot instance.
        callback (CallbackQuery): The callback query containing vote information.
        category (int): The message category.
    """    
    

    Bot.set_current(bot)
    _, vote_type, msg_id_offset, relative_msg_id = callback.data.split(CALLBACK_SEP)
    vote_type, msg_id_offset, relative_msg_id = int(vote_type), int(msg_id_offset), int(relative_msg_id)
    if vote_type == SPAM:
        orig_msg = await bot.forward_message(DEVELOPER_ID, callback.from_user.id, callback.message.message_id + msg_id_offset)
        kb = InlineKeyboardMarkup()
        msg_id_str = str(callback.message.message_id)
        kb.row(
            InlineKeyboardButton(
                'Спам', callback_data=CALLBACK_SEP.join([CONFIRM_SPAM, THROW_MSG_TO_SPAM, str(callback.from_user.id),
                str(relative_msg_id), str(category), msg_id_str])
            ),
            InlineKeyboardButton(
                'Удалить', callback_data=CALLBACK_SEP.join([CONFIRM_SPAM, JUST_DEL_MSG, str(callback.from_user.id),
                str(relative_msg_id), str(category), msg_id_str])
            )
        )
        kb.add(
            InlineKeyboardButton(
                'Отказ', callback_data=CALLBACK_SEP.join([DISCARD_SPAM, str(callback.from_user.id), msg_id_str, str(category)])
            )
        )
        await callback.message.edit_text(callback.message.text + '\n\nАдминистраторы проверят сообщение '
        'и заблокируют пользователя, если это спам.')
        paying_bot = Bot(PAYING_BOT_TOKEN)
        text = f'Пользователь {await get_nick(callback.from_user)} считает, ' \
               f'что это сообщение ({message_category_names[category]}) спам:\n\n{orig_msg.text}\n' \
               '\nПодвердить блокировку пользователя?'
        try:
            await orig_msg.delete()
        except:
            pass
        try:
            await paying_bot.send_message(
                EUGENIY_ID if not TESTING else callback.from_user.id,
                text,
                reply_markup=kb, parse_mode='HTML'
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
    votes = Vote.findByFilter(message_id=message_id, user_id=callback.from_user.id, category=category)
    if votes:
        await callback.answer(f'Вы уже отметили это сообщение как {vote_type_names[votes[0].vote_type]} ранее')
        return
    try:
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
                    exc_info=True
                )
                await callback.answer('Произошла ошибка при попытке удалить сообщение')
                return
            return
        await callback.answer(f'Сообщение отмечено как {vote_type_names[vote_type]}')
    if vote_type == TARGET or vote_type == NOT_TARGET:
        await __edit_pressed_vote_keyboard(callback, bot, msg_id_offset, relative_msg_id, vote_type, category)

async def generate_statistics_texts_for_message(
    bot: Bot, client_id: int, period: typing.Tuple[date, date]
) -> typing.List[str]:
    """
    Generates statistics texts for a client's messages.

    Parameters:
        bot (Bot): The bot instance.
        client_id (int): The client ID.
        period (typing.Tuple[date, date]): The period for generating statistics.

    Returns:
        typing.List[str]: The list of statistics texts.
    """
    
    statistics_texts = []
    for category in message_categories:
        current_text = ''
        accounts = [client_id] + get_all_accounts_of(client_id)
        current_statistics = {TARGET: 0, NOT_TARGET: 0, SPAM: 0}
        for i, account in enumerate(accounts):
            try:
                nickname = await get_nick((await bot.get_chat_member(account, account)).user)
            except:
                nickname = f'{account}'
            votes = Vote.findByFilter(period=period, user_id=account, category=category)
            if not votes:
                continue
            account_statistics = {TARGET: 0, NOT_TARGET: 0, SPAM: 0}
            for vote in votes:
                account_statistics[vote.vote_type] += 1
                current_statistics[vote.vote_type] += 1
            current_text += f'<i><b>{nickname}</b></i>: отмечено целевых : <b>{account_statistics[TARGET]}</b> '\
                            f'не целевых : <b>{account_statistics[NOT_TARGET]}</b> '\
                            f'спам : <b>{account_statistics[SPAM]}</b>'
            current_text += '\n---------------------------\n' if i < len(accounts) - 1 else '\n'
        if not current_text:
            continue
        current_text = f'<b>{message_category_names[category]}</b>\n' + current_text
        if len(accounts) > 1:
            current_text += f'\nВсего:\nЦелевых - <b>{current_statistics[TARGET]}</b>\nНе целевых - <b>{current_statistics[NOT_TARGET]}</b>'
        target_percent = '{0:.1f}'.format(
            current_statistics[TARGET] / max(1, current_statistics[TARGET] + current_statistics[NOT_TARGET] + current_statistics[SPAM]) * 100
        )
        current_text += f'\n% целевых - <b>{target_percent}%</b>'
        statistics_texts.append(current_text)
    return statistics_texts
