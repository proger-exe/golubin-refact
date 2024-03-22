from datetime import datetime
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.apis.ClientsData.GoogleSheets.config import ADD_GOOGLE_SHEET, DEL_GOOGLE_SHEET
from src.apis.db.accounts import get_all_accounts_of
from src.data import config
from src.data.bot_config import *
from src.utils.client import Client
from src.data.modules import accounts_manage

add_chat_kb = InlineKeyboardMarkup()
add_chat_kb.row(
    InlineKeyboardButton(
        "Пригласить аккаунт", callback_data=INVITE_ACCOUNT_TO_EXTERNAL_CHAT
    ),
    InlineKeyboardButton("Отправить ссылку", callback_data=SEND_LINK_TO_EXTERNAL_CHAT),
)
back_button = InlineKeyboardMarkup()
back_button.add(
    InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data=ADD_EXTERNAL_CHAT_CALLBACK)
)

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


def google_sheets_panel(spread_sheet: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    if not spread_sheet:
        kb.add(InlineKeyboardButton('Подключить', callback_data = ADD_GOOGLE_SHEET))
        
    else:
        kb.add(InlineKeyboardButton('Отключить', callback_data = DEL_GOOGLE_SHEET))

    return kb

def manage_account_keyboard(account_ids, has_year_sub):
    markup = InlineKeyboardMarkup()
    
    
    if has_year_sub:
        text = 'Добавить первый аккаунт' if not account_ids else 'Добавить новый'
        markup.add(
            InlineKeyboardButton(text, callback_data = accounts_manage.ADD_ACCOUNT) 
        )
        
    if account_ids:
        markup.add(
            InlineKeyboardButton('Удалить существующий', callback_data = accounts_manage.DEL_ACCOUNT)
        )
    
    return markup

def accounts(year_subscribes, user_id):
    choose_cat_to_add = InlineKeyboardMarkup()
    for sub in year_subscribes:
        if len(get_all_accounts_of(user_id, sub.sending_mode)) < accounts_manage.MAX_NUMBER_OF_ACCOUNTS:
            choose_cat_to_add.add(
                InlineKeyboardButton(
                    config.message_category_names[sub.sending_mode], 
                    callback_data = accounts_manage.CHOOSE_CATEGORY_FOR_ACC+CALLBACK_SEP+str(sub.sending_mode)
                )
            )
    return choose_cat_to_add

