import os
from typing import Union
from aiogram import Dispatcher, Bot
from aiogram.types import Message
from Referal.referal_links import get_referal_url
from Statistics import statistics
from .ReferalClient import ReferalClient as RefClient
from decimal import Decimal 
from bot_config import *
from client import Client
from decimal import Decimal
from .config import *
import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.dispatcher.storage import FSMContext
from bot_get_nick import get_nick
from .ref_states import RefBotStates
from config import TESTING
from datetime import datetime
import user
import Statistics
from History import ReferalPaymentsHistory, ReferalPayment
from ClientsData import Accounts
from AdminBot.google_sheets import upload_new_referal_withdrawal
from Promocodes import get_all_active_promocodes_of_refer, get_promocode_action
import pandas as pd
from History import PaymentHistory
from aiogram.types import InputFile

async def _show_referal_system(bot: Bot, client_id: int, message: Message, edit_only = True):
	referal = RefClient.get_client_by_id(client_id)
	if not referal:
		referal = RefClient(client_id, HAS_REFS, Decimal('0.00'), NOT_INVITED)
		referal.add_to_db()
		Statistics.save_to_statistics(new_refererals=1)
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
		refer.add_to_db()
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
		clients = referal.get_refer_ids()
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
	referal.add_to_db()
	Statistics.save_to_statistics(total_referal_commisions = commision, 
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

def init_referal_m_handlers(dp: Dispatcher):

	@dp.message_handler(lambda message: message.text.endswith(REFERAL_SYSTEM_BUTTON_FOR_NEWBIE), 
		state = '*'
	)
	async def show_ref_system(message: Message, state: FSMContext):
		await state.finish()
		admin = Accounts.get_admin_of_account(message.from_user.id)
		if admin:
			await message.answer('Вы не можете использовать реферальную систему, '
                f'так как ваш аккаунт подключен к {await get_nick((await dp.bot.get_chat_member(admin, admin)).user)}')
			return
		await _show_referal_system(dp.bot, message.from_user.id, message, edit_only = False)

	@dp.callback_query_handler(lambda s : s.data == REQUIRE_WITHDRAWAL_OF_REFERAL_BALANCE)
	async def require_withdrawal_of_referal_balance(callback: CallbackQuery):
		await _require_withdrawal_of_referal_balance(dp.bot, callback.from_user.id, callback.message)
	
	@dp.callback_query_handler(lambda s : s.data == BACK_TO_REFERAL_MENU)
	async def get_back_to_ref_menu(callback: CallbackQuery):
		await _show_referal_system(dp.bot, callback.from_user.id, callback.message)

	@dp.callback_query_handler(lambda s : s.data.startswith(WITHDRAW_TO))
	async def get_requisites_to_withdraw(callback: CallbackQuery):
		withdraw_to = callback.data.split(CALLBACK_SEP)[1]
		await RefBotStates.get_requisits_to_withdraw.set()
		state = dp.current_state(chat = callback.message.chat.id,
            user = callback.from_user.id)
		await state.update_data(withdraw_to = withdraw_to, message_to_delete = callback.message.message_id)
		text = ''
		if withdraw_to == QIWI:
			text = 'Отправьте номер киви кошелька: '
		elif withdraw_to == YOOMONEY:
			text = 'Отправьте номер ЮМани кошелька: '
		elif withdraw_to == CARD:
			text = 'Отправьте номер карты: '
		kb = InlineKeyboardMarkup()
		kb.add(InlineKeyboardButton('назад', callback_data = BACK_TO_WALLET_CHOOSING))
		await dp.bot.edit_message_text(
			text = text, 
			chat_id = callback.message.chat.id,
			message_id = callback.message.message_id,
			reply_markup = kb
		)

	@dp.callback_query_handler(
		lambda s : s.data == BACK_TO_WALLET_CHOOSING, state = RefBotStates.get_requisits_to_withdraw)
	async def get_back_to_wallet_choosing(callback: CallbackQuery, state: FSMContext):
		await state.finish()
		await _require_withdrawal_of_referal_balance(dp.bot, callback.from_user.id, callback.message)

	@dp.message_handler(state = RefBotStates.get_requisits_to_withdraw)
	async def send_withdrawl_requirement(message: Message, state: FSMContext):
		state_data = await state.get_data()
		withdraw_to = state_data['withdraw_to']
		await state.finish()
		to_id = EUGENIY_ID if not TESTING else message.from_user.id
		referal = RefClient.get_client_by_id(message.from_user.id)
		kb = InlineKeyboardMarkup()
		kb.add(
			InlineKeyboardButton(
				'Отменить перевод', 
				callback_data = CALLBACK_SEP.join([RESTORE_BALANCE, str(referal.id), str(referal.balance)])
			),
			InlineKeyboardButton(
				'Подтвердить перевод', 
				callback_data = CALLBACK_SEP.join([CONFIRM_WITHDRAWAL, str(referal.id), str(referal.balance)])
			)
		)
		nick = await get_nick(message.from_user)
		await dp.bot.send_message(
			to_id,
			f'<b>{nick}</b> запросил вывод средств с реферального счёта на \n'
			f'<b>{message.text}</b> ({WALLET_NAMES[withdraw_to]}).\n'
			f'Размер вывода: <b>{referal.balance}</b> руб.\n',
			reply_markup = kb, parse_mode = 'HTML'
		)
		referal.balance = Decimal('0.0')
		referal.add_to_db()
		await dp.bot.delete_message(chat_id = message.chat.id, message_id = state_data['message_to_delete'])
		await dp.bot.send_message(referal.id, 'Ваша заявка на снятие средств в очереди обработки. Пожалуйста, ждите.')

	@dp.callback_query_handler(lambda s : s.data.startswith(RESTORE_BALANCE))
	async def restore_ref_client_balance(callback: CallbackQuery):
		args = callback.data.split(CALLBACK_SEP)
		client_id = int(args[1])
		balance = Decimal(args[2])
		client = RefClient.get_client_by_id(client_id)
		client.balance = balance
		client.add_to_db()
		await dp.bot.send_message(client_id, 'Не удалось вывести средства с вашего реферального счета')
		await dp.bot.delete_message(chat_id = callback.message.chat.id, message_id = callback.message.message_id)
		await dp.bot.send_message(callback.from_user.id, 'Отмена перевода')

	@dp.callback_query_handler(lambda s : s.data.startswith(CONFIRM_WITHDRAWAL))
	async def notify_referal_about_withdrawal(callback: CallbackQuery):
		args = callback.data.split(CALLBACK_SEP)
		client_id = int(args[1])
		balance = Decimal(args[2])
		try:
			ReferalPaymentsHistory.save(ReferalPayment(date.today(), client_id, balance))
			statistics.save_to_statistics(total_referal_commisions = balance)
		except Exception as e:
			logging.error(f'Failed to save referal withdrawal (from {client_id}, {balance}) to history and statistics:',
				exc_info = True)
		upload_new_referal_withdrawal(date.today(), balance)
		await dp.bot.send_message(client_id, f'{balance} руб. переведены вам с реферального счета')
		await dp.bot.delete_message(chat_id = callback.message.chat.id, message_id = callback.message.message_id)
		await dp.bot.send_message(callback.from_user.id, 'Клиент оповещён о совершенной опперации')

	@dp.callback_query_handler(lambda c: c.data == TURN_NOTIFICATIONS_OFF, state = '*')
	async def turn_notifications_off(callback: CallbackQuery, state: FSMContext):
		await state.finish()
		referal = RefClient.get_client_by_id(callback.from_user.id)
		if not referal:
			await callback.answer('Не удалось найти ваш реферальный счёт.', True)
			return
		referal.show_notifications = False
		referal.add_to_db()
		await callback.answer('Вы не будете получать уведомления об оплатах через вашу реферальную ссылку', True)
		kb = InlineKeyboardMarkup()
		for row in callback.message.reply_markup.inline_keyboard:
			for i in range(len(row)):
				if row[i].callback_data == TURN_NOTIFICATIONS_OFF:
					row[i] = InlineKeyboardButton('Включить уведомления 🔔', callback_data = TURN_NOTIFICATIONS_ON)
					break
			kb.row(*row)
		if not len(kb.inline_keyboard):
			kb.add(InlineKeyboardButton('Включить уведомления 🔔', callback_data = TURN_NOTIFICATIONS_ON)) 
		await callback.message.edit_reply_markup(kb)


	@dp.callback_query_handler(lambda c: c.data == TURN_NOTIFICATIONS_ON, state = '*')
	async def turn_notifications_on(callback: CallbackQuery, state: FSMContext):
		await state.finish()
		referal = RefClient.get_client_by_id(callback.from_user.id)
		if not referal:
			await callback.answer('Не удалось найти ваш реферальный счёт.', True)
			return
		referal.show_notifications = True
		referal.add_to_db()
		await callback.answer('Вы будете получать уведомления об оплатах через вашу реферальную ссылку', True)
		kb = InlineKeyboardMarkup()
		for row in callback.message.reply_markup.inline_keyboard:
			for i in range(len(row)):
				if row[i].callback_data == TURN_NOTIFICATIONS_ON:
					row[i] = InlineKeyboardButton('Отключить уведомления 🔕', callback_data = TURN_NOTIFICATIONS_OFF)
					break
			kb.row(*row)
		if not len(kb.inline_keyboard):
			kb.add(InlineKeyboardButton('Отключить уведомления 🔕', callback_data = TURN_NOTIFICATIONS_OFF))
		await callback.message.edit_reply_markup(kb)

	@dp.callback_query_handler(lambda callback: callback.data == MY_PROMOCODES, state = '*')
	async def show_promocodes(callback: CallbackQuery, state: FSMContext):
		await state.finish()
		kb = InlineKeyboardMarkup()
		promocodes = get_all_active_promocodes_of_refer(callback.from_user.id)
		if not promocodes:
			kb.add(InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data = BACK_TO_REFERAL_MENU))
			await callback.message.edit_text('У вас нет активных промокодов', reply_markup = kb)
			return
		text = 'Ваши промокоды:\n\n'
		for p in promocodes:
			category, trial_days, sale, period, due_time = get_promocode_action(p)
			text += f'<code>{p}</code>:'
			if category:
				text += f'\n\t- <i>{message_category_names[category]}</i>'
			else:
				text += '\n\t- Все категории'
			if sale:
				sale = '{0:.2f}'.format(sale * 100).replace('.', ',')
				if not period:
					text += f'\n\t- <b>{sale}</b>% на все тарифы. '
				else:
					text += f'\n\t- <b>{sale}</b>% для {period} дн. '
			elif trial_days:
				text += f'\n\t- <b>{trial_days}</b> бонусных дней'
			if due_time:
				due_time = due_time.strftime('%d.%m.%Y')
				text += f'\n\t- До <u>{due_time}</u>'
			text += '\n-----------------------------------\n'
		kb.add(InlineKeyboardButton('Показать статистику', callback_data = SHOW_REFERAL_STATISTS))
		kb.add(InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data = BACK_TO_REFERAL_MENU))
		try:
			await callback.message.edit_text(text, 'HTML', reply_markup=kb)
		except:
			pass

	@dp.callback_query_handler(lambda callback: callback.data == SHOW_REFERAL_STATISTS, state = '*')
	async def send_referal_statistics(callback: CallbackQuery, state: FSMContext):
		await callback.answer('Собираем статистику...')
		ref_links = get_all_active_promocodes_of_refer(callback.from_user.id)
		ref_links.append(f't.me/{PAING_BOT_NAME}?start=ref{callback.from_user.id}')
		filename = f'temp_excel_tables/{callback.from_user.id}_referal_statistics.xlsx'
		if os.path.exists(filename):
			return
		sheets = {}
		for ref_link in ref_links:
			payments = PaymentHistory.findPaymentsBy(REFERAL_LINK = ref_link)
			if payments:
				df = pd.DataFrame(columns=['Клиент', 'Сумма оплаты', 'Дата', 'Вознаграждение'])
				for payment in payments:
					nick = ''
					try:
						user = (await dp.bot.get_chat_member(payment.client_id, payment.client_id)).user
					except:
						nick = f'TG-ID:{payment.client_id}'
					else:
						nick = user.username if user.username else user.full_name
					df.loc[len(df)] = [
						nick, 
						f'{payment.amount} руб.'.replace('.', ','), 
						payment.time.strftime('%d.%m.%Y %H:%M:%S'),
						f'{payment.referal_commission} руб.'.replace('.', ',')
					]
				df.loc[len(df)] = ['Итог:', f'=SUM(B2:B{len(df)})', '', f'=SUM(D2:D{len(df)})']
				if ref_link.startswith('t.me'):
					ref_link = 'Реф. ссылка'
				sheets[ref_link] = df
		if not sheets:
			await callback.answer(
				'Не удалось собрать статистику об оплатах через вашу реф. систему.', show_alert = True)
			return
		try:
			if not os.path.exists('temp_excel_tables'):
				os.mkdir('temp_excel_tables')
			with pd.ExcelWriter(filename) as writer:
				for ref_link in sheets:
					sheets[ref_link].to_excel(writer, ref_link, header=True, index=False)
		except:
			logging.error('Failed to send statistics about promocodes and ref system:', exc_info=True)
		else:
			try:
				await dp.bot.send_document(callback.from_user.id, 
			       InputFile(filename, 'Реферальная статистика golubin_bot.xlsx'))
			except:
				logging.critical('FAILED TO SEND REFERAL STATISTICS TO A CLIENT:', exc_info=True)
		finally:
			if os.path.exists(filename):
				os.remove(filename)