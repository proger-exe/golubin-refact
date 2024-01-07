from datetime import date
import typing

from aiogram import Bot
from src.apis.bot_get_nick import get_nick
from db.accounts import get_admin_of_account, get_all_accounts_of
from db.user import client_has_year_subscribe
from src.data.bot_data import EUGENIY_ID
from . import config
from src.data.config import message_categories, message_category_names
from .config import TARGET, NOT_TARGET, SPAM, MESSAGE_VOTE, GET_VOTE_STATISTICS, JUST_DEL_MSG, THROW_MSG_TO_SPAM
from .users_votes import Vote


def check_if_client_is_allowed_to_get_vote_buttons(client_id: int, category: typing.Optional[int] = None) -> bool:
    if client_id == EUGENIY_ID:
        return True
    admin = get_admin_of_account(client_id)
    if admin and client_has_year_subscribe(admin, category):
        return True
    return client_has_year_subscribe(client_id, category)


async def generate_statistics_texts_for_message(
    bot: Bot, client_id: int, period: typing.Tuple[date, date]
) -> typing.List[str]:
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


'''This package controlls users messages-votes'''