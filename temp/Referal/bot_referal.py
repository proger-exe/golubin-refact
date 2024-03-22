import os
from typing import Union
from aiogram import Bot
from aiogram.types import Message
from src.apis.db import get_connection_and_cursor
from src.apis.db.modules.referal_links import get_referal_url
from src.apis.db.modules import statistics, user
from .ReferalClient import ReferalClient as RefClient
from decimal import Decimal 
from src.data.bot_config import *
from client import Client
from decimal import Decimal
from src.data.modules.refs import *
import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.utils.bot_get_nick import get_nick
from datetime import datetime
 
from src.apis.db.modules.promocodes import get_all_active_promocodes_of_refer

# ага, шелби, улучшил импорты, шедевроооо

async def _show_referal_system(bot: Bot, client_id: int, message: Message, edit_only = True):
	referal = RefClient.get_client_by_id(client_id)
	if not referal:
		referal = RefClient(client_id, HAS_REFS, Decimal('0.00'), NOT_INVITED)
		con, cur = get_connection_and_cursor()
		referal.add_to_db(con, cur)
		statistics.save_to_statistics(new_refererals=1)
	kb = None
	kb = _get_referal_markup(referal)
	ref_stats = statistics.get_referal_statistics(f't.me/{PAING_BOT_NAME}?start=ref{client_id}')
	text = REFERAL_INFO_TEXT.format(
		referal.id, 
		'{0:.2f}'.format(referal.balance).replace('.', ','), 
		referal.refers_num, 
		str(int(referal.percent1*100)).replace('.', ','), 
		ref_stats[0],
		ref_stats[2],
		ref_stats[3],
		'{0:.2f}'.format(ref_stats[4]).replace('.', ','),
		str(int(referal.percent2*100)).replace('.', ','),
		referal.required_referal_number
	)
	if edit_only:
		await bot.edit_message_text(
			text = text,
			chat_id = message.chat.id,
            message_id = message.message_id,
			reply_markup =  kb, disable_web_page_preview = True
		)
	else:
		await bot.send_message(
			client_id, text, reply_markup =  kb)

def _get_referal_markup(referal: RefClient) -> InlineKeyboardMarkup:
	kb = InlineKeyboardMarkup()
	if referal.balance:
		kb.add(
			InlineKeyboardButton(
				'Вывести деньги',
				callback_data = REQUIRE_WITHDRAWAL_OF_REFERAL_BALANCE
			)
		)
	if get_all_active_promocodes_of_refer(referal.id):
		kb.add(InlineKeyboardButton('Мои промокоды', callback_data = MY_PROMOCODES))
	if referal.show_notifications:
		kb.add(InlineKeyboardButton('Отключить уведомления 🔕', callback_data = TURN_NOTIFICATIONS_OFF))
	else:
		kb.add(InlineKeyboardButton('Включить уведомления 🔔', callback_data = TURN_NOTIFICATIONS_ON))
	return kb

async def handle_start_with_referal_info(bot: Bot, message: Message) -> Union[int, None]:
	'''
	Saves info about new user that was invited using the referal system.
	
	if the link is valid will return the id of a refer that has invited new user else None 
	'''
	ref_info = message.text.split()[1]
	str_id = ref_info[len(REF_START):]
	available_link = True
	id = None
	if not str_id.isdigit() or str_id[0] == '-':
		available_link = False
	else:
		id = int(str_id)
		if not RefClient.has_client_id(id):
			available_link = False
		else:
			referal = RefClient.get_client_by_id(id)
			if referal.referal_status == HASNT_REFS:
				available_link = False
	if not available_link:
		await handle_referal_link_to_another_origin_site(message, str_id)
		return None
	else:
		await add_client_into_referal_system(message.from_user.id, id, bot)
		return id

async def handle_referal_link_to_another_origin_site(message: Message, link_name: str):
	ref_url = get_referal_url(link_name)
	if not ref_url:
		return
	if user.user_is_having_launched_bot(message.from_user.id):
		return
	user.set_user_as_having_launched(message.from_user.id)
	user.set_origin(message.from_user.id, ref_url)

async def add_client_into_referal_system(client_id: int, referal_id: int, bot: Bot):
	if client_id == referal_id:
		await bot.send_message(client_id, 'Нельзя переходить по своей же реферальной ссылке')
		return
	if user.user_is_having_launched_bot(client_id):
		await bot.send_message(
			client_id, 
			'Реферальная ссылка работает только для пользователей, ни разу не запускавших этого бота ранее'
		)
		return
	refer  = RefClient(client_id, HASNT_REFS, Decimal('0.0'), referal_id)
	try:
		con, cur = get_connection_and_cursor()
		refer.add_to_db(con, cur)
	except Exception as e:
		logging.error(f'Failed to add  referal: {str(e)}. User-id: {client_id}, refer-id: {referal_id}', e)

async def _require_withdrawal_of_referal_balance(bot: Bot, client_id: int, message: Message, edit_only = True):
	client = RefClient.get_client_by_id(client_id)
	if not client.balance:
		await bot.send_message(client_id, 'На вашем балансе нет денег')
		return
	kb = InlineKeyboardMarkup()
	kb.row(
		InlineKeyboardButton('Qiwi', callback_data = WITHDRAW_TO+CALLBACK_SEP+QIWI),
		InlineKeyboardButton('ЮМани', callback_data = WITHDRAW_TO+CALLBACK_SEP+YOOMONEY),
		InlineKeyboardButton('Банковская карта', callback_data = WITHDRAW_TO+CALLBACK_SEP+CARD)
	)
	kb.add(InlineKeyboardButton('назад', callback_data=BACK_TO_REFERAL_MENU))
	text = 'Выберите, куда вывести деньги: '
	if edit_only:
		await bot.edit_message_text(
			text = text,
			chat_id = message.chat.id,
            message_id = message.message_id,
			reply_markup =  kb
		)
	else:
		await bot.send_message(client_id, text, reply_markup=kb)

async def process_referal(client_id: int, cost: Decimal, bot: Bot) -> Decimal: 
	''' checks if client is invited by a referal and do commisions to the referal
		returns commision size
	'''
	refer = RefClient.get_client_by_id(client_id)
	commision = Decimal('0')
	if not refer:
		return commision
	if refer.referal_id == NOT_INVITED:
		return commision
	referal = RefClient.get_client_by_id(refer.referal_id)
	refers_num = referal.refers_num
	if refers_num < referal.required_referal_number:
		commision = cost * referal.percent1
	else:
		con, cur = get_connection_and_cursor()
		clients = referal.get_refer_ids(con, cur)
		active_n = 0
		now = datetime.now()
		for id in clients:
			c = Client.get_clients_by_filter(id = id, payment_period_end = now, greater = True, is_paid = True)
			if not c:
				continue
			active_n += 1
			if active_n >= referal.required_referal_number:
				break
		if active_n >= referal.required_referal_number:
			commision = cost * referal.percent2
		else:
			commision = cost * referal.percent1  
	referal.balance += commision
	con, cur = get_connection_and_cursor()
	referal.add_to_db(con, cur)
	statistics.save_to_statistics(total_referal_commisions = commision, 
		new_referal_buyers = 1, total_referal_income = cost, ref_link = f't.me/{PAING_BOT_NAME}?start=ref{referal.id}')
	if referal.show_notifications:
		await notify_referal_about_new_order(referal, client_id, commision, cost, bot)
	return commision

async def notify_referal_about_new_order(referal: RefClient, client_id: int, commision: Decimal, cost: Decimal, bot: Bot):
	kb = InlineKeyboardMarkup()
	kb.add(InlineKeyboardButton('Отключить уведомления 🔕', callback_data = TURN_NOTIFICATIONS_OFF))
	try:
		user = await bot.get_chat_member(client_id, client_id)
		nick = await get_nick(user.user)
	except:
		nick = f'<a href="tg://user?id={client_id}">Unknown</a>'
	await bot.send_message(
		referal.id,
		f'Поступила оплата от {nick}\n'
		'Сумма {0:.2f} руб'.format(cost).replace('.', ',')+'.\n' + \
		'<b>Вознаграждение {0:.2f} руб'.format(commision).replace('.', ',')+'.\n' + \
		'Баланс {0:.2f}</b> руб'.format(referal.balance).replace('.', ',')+'.',
		reply_markup = kb,
		parse_mode='HTML'
	)
