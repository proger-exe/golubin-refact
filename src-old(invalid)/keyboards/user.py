from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.callbacks import accounts_manage
from src.apis.ClientsData.GoogleSheets.config import DEL_GOOGLE_SHEET, ADD_GOOGLE_SHEET

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


# def choose_cat_to_add(year_subscribes):
#     markup = InlineKeyboardMarkup()
    
#     for sub in year_subscribes:
#         if len()

def google_sheets_panel(spread_sheet: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    if not spread_sheet:
        kb.add(InlineKeyboardButton('Подключить', call_data = ADD_GOOGLE_SHEET))
        
    else:
        kb.add(InlineKeyboardButton('Отключить', call_data = DEL_GOOGLE_SHEET))

    return kb