from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from config import message_category_names, message_categories
from .admin_bot_config import *

CALLBACK_SEP = ';'
main_menu_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu_kb.row(
	KeyboardButton(EDIT_STOP_WORDS),
	KeyboardButton(INCREASE_PERIOD)
)
main_menu_kb.row(
	KeyboardButton(SEND_MESSAGE_AWAY),
	KeyboardButton(PROMOCODES)
)
main_menu_kb.add(
	KeyboardButton(CHANGE_REFERAL_CONDITIONS),
	KeyboardButton(CHANGE_CHANNEL_OF_TRIAL_PERIOD)
)
category_choose_kb = ReplyKeyboardMarkup()
for k in message_category_names:
	category_choose_kb.add(KeyboardButton(message_category_names[k]))
choose_promocode_cat = InlineKeyboardMarkup()
for i in range(0, len(message_categories), 2):
	c = message_categories[i]
	if i + 1 < len(message_categories):
		c2 = message_categories[i+1]
		choose_promocode_cat.row(
			InlineKeyboardButton(
				message_category_names[c], callback_data = PROMOCODE_CATEGORY+CALLBACK_SEP+str(c)),
			InlineKeyboardButton(
				message_category_names[c2], callback_data = PROMOCODE_CATEGORY+CALLBACK_SEP+str(c2))
		)
	else:
		choose_promocode_cat.row(
			InlineKeyboardButton(
				message_category_names[c], callback_data = PROMOCODE_CATEGORY+CALLBACK_SEP+str(c)),
			InlineKeyboardButton(
				'Все', callback_data = PROMOCODE_CATEGORY+CALLBACK_SEP+'*')
		)
if len(message_categories) % 2 == 0:
	choose_promocode_cat.add(
		InlineKeyboardButton(
			'Все', callback_data = PROMOCODE_CATEGORY+CALLBACK_SEP+'*')
	)
def get_choose_promocode_act(category: int):
	choose_promocode_act = InlineKeyboardMarkup()
	choose_promocode_act.add(
		InlineKeyboardButton(
			'Дни пробного периода', callback_data = CALLBACK_SEP.join([TRIAL_EXTRA_DAYS, str(category)]))
	)
	choose_promocode_act.add(
		InlineKeyboardButton(
			'Скидка при оплате', callback_data = CALLBACK_SEP.join([PAYMENT_SALE, str(category)]))
	)
	return choose_promocode_act

keyboard_to_find_out_if_client_has_paid = ReplyKeyboardMarkup(resize_keyboard = True)
keyboard_to_find_out_if_client_has_paid.row(
	KeyboardButton(CLIENT_PAID),
	KeyboardButton(CLIENT_DID_NOT_PAY)
)

keyboard_to_find_out_if_promocode_belongs_refer = InlineKeyboardMarkup()
keyboard_to_find_out_if_promocode_belongs_refer.row(
	InlineKeyboardButton('да', callback_data = PROMOCODE_BELONGS_REFER),
	InlineKeyboardButton('нет', callback_data = PROMOCODE_DOESNT_BELONG_REFER)
)

def get_keyboard_to_customize_referal_conditions(client_id: int) -> InlineKeyboardMarkup:
	keyboard_to_customize_referal_conditions = InlineKeyboardMarkup()
	keyboard_to_customize_referal_conditions.row(
		InlineKeyboardButton(CHANGE_PERCENT1[0], callback_data=f'{CHANGE_PERCENT1[1]};{client_id}'),
		InlineKeyboardButton(CHANGE_PERCENT2[0], callback_data=f'{CHANGE_PERCENT2[1]};{client_id}')
	)
	keyboard_to_customize_referal_conditions.add(
		InlineKeyboardButton(CHANGE_REQUIRED_MIN_NUM_OF_REFERALS_TO_GET_BIGGER_PERCENT[0], 
			callback_data = f'{CHANGE_REQUIRED_MIN_NUM_OF_REFERALS_TO_GET_BIGGER_PERCENT[1]};{client_id}')
	)
	return keyboard_to_customize_referal_conditions