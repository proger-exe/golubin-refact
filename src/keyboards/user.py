from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.callbacks import accounts_manage

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


def choose_cat_to_add(year_subscribes):
    markup = InlineKeyboardMarkup()
    
    for sub in year_subscribes:
        if len()
    