import os
from aiogram import Dispatcher
from aiogram.types import Message
from src.apis.db import get_connection_and_cursor
from src.apis.db.modules import statistics, accounts
from temp.Referal.bot_referal import _require_withdrawal_of_referal_balance, _show_referal_system
from .ReferalClient import ReferalClient as RefClient
from decimal import Decimal 
from src.data.bot_config import *
from decimal import Decimal
from src.data.modules.refs import *
import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.dispatcher.storage import FSMContext
from src.utils.bot_get_nick import get_nick
from src.data.config import TESTING

from src.apis.db.modules.referal_payments_history import ReferalPaymentsHistory, ReferalPayment
from src.apis.db.modules.payments_history import PaymentHistory
from AdminBot.google_sheets import upload_new_referal_withdrawal
from src.apis.db.modules.promocodes import get_all_active_promocodes_of_refer, get_promocode_action
import pandas as pd
from aiogram.types import InputFile



# @dp.message_handler(lambda message: message.text.endswith(REFERAL_SYSTEM_BUTTON_FOR_NEWBIE), 
#     state = '*'
# )

handle_show_ref_system = lambda dp: dp.register_message_handler(show_ref_system, text_endswith=REFERAL_SYSTEM_BUTTON_FOR_NEWBIE) 
async def show_ref_system(message: Message, state: FSMContext):
    await state.finish()
    admin = accounts.get_admin_of_account(message.from_user.id)
    if admin:
        await message.answer('Вы не можете использовать реферальную систему, '
            f'так как ваш аккаунт подключен к {await get_nick((await message.bot.get_chat_member(admin, admin)).user)}')
        return
    await _show_referal_system(message.bot, message.from_user.id, message, edit_only = False)


# @dp.callback_query_handler(lambda s : s.data == REQUIRE_WITHDRAWAL_OF_REFERAL_BALANCE)
handle_require_withdrawal_of_referal_balance = lambda dp: dp.register_callback_query_handler(require_withdrawal_of_referal_balance, text=REQUIRE_WITHDRAWAL_OF_REFERAL_BALANCE)
async def require_withdrawal_of_referal_balance(callback: CallbackQuery):
    await _require_withdrawal_of_referal_balance(callback.bot, callback.from_user.id, callback.message)

# @dp.callback_query_handler(lambda s : s.data == BACK_TO_REFERAL_MENU)
handle_get_back_to_ref_menu = lambda dp: dp.register_callback_query_handler(get_back_to_ref_menu, text=BACK_TO_REFERAL_MENU)
async def get_back_to_ref_menu(callback: CallbackQuery):
    await _show_referal_system(callback.bot, callback.from_user.id, callback.message)

# @dp.callback_query_handler(lambda s : s.data.startswith(WITHDRAW_TO))
handle_get_requisites_to_withdraw = lambda dp: dp.register_callback_query_handler(get_requisites_to_withdraw, text=WITHDRAW_TO)
async def get_requisites_to_withdraw(callback: CallbackQuery, state: FSMContext):
    withdraw_to = callback.data.split(CALLBACK_SEP)[1]
    await state.set_state("get_requisits_to_withdraw")
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
    await callback.bot.edit_message_text(
        text = text, 
        chat_id = callback.message.chat.id,
        message_id = callback.message.message_id,
        reply_markup = kb
    )

# @dp.callback_query_handler(
#     lambda s : s.data == BACK_TO_WALLET_CHOOSING, state = RefBotStates.get_requisits_to_withdraw)
handle_get_back_to_wallet_choosing = lambda dp: dp.register_callback_query_handler(get_back_to_wallet_choosing, state="get_requisits_to_withdraw")
async def get_back_to_wallet_choosing(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    await _require_withdrawal_of_referal_balance(callback.bot, callback.from_user.id, callback.message)

# @dp.message_handler(state = RefBotStates.get_requisits_to_withdraw)
handle_send_withdrawal_requirement = lambda dp: dp.register_message_handler(send_withdrawl_requirement, state="get_requisits_to_withdraw")
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
    await message.bot.send_message(
        to_id,
        f'<b>{nick}</b> запросил вывод средств с реферального счёта на \n'
        f'<b>{message.text}</b> ({WALLET_NAMES[withdraw_to]}).\n'
        f'Размер вывода: <b>{referal.balance}</b> руб.\n',
        reply_markup = kb, parse_mode = 'HTML'
    )
    referal.balance = Decimal('0.0')
    con, cur = get_connection_and_cursor()
    referal.add_to_db(con, cur)
    await message.bot.delete_message(chat_id = message.chat.id, message_id = state_data['message_to_delete'])
    await message.bot.send_message(referal.id, 'Ваша заявка на снятие средств в очереди обработки. Пожалуйста, ждите.')

# @dp.callback_query_handler(lambda s : s.data.startswith(RESTORE_BALANCE))
handle_restore_ref_client_balance = lambda dp: dp.register_callback_query_handler(restore_ref_client_balance, text_startswith=RESTORE_BALANCE)
async def restore_ref_client_balance(callback: CallbackQuery):
    args = callback.data.split(CALLBACK_SEP)
    client_id = int(args[1])
    balance = Decimal(args[2])
    client = RefClient.get_client_by_id(client_id)
    client.balance = balance
    client.add_to_db()
    await callback.bot.send_message(client_id, 'Не удалось вывести средства с вашего реферального счета')
    await callback.bot.delete_message(chat_id = callback.message.chat.id, message_id = callback.message.message_id)
    await callback.bot.send_message(callback.from_user.id, 'Отмена перевода')

# @dp.callback_query_handler(lambda s : s.data.startswith(CONFIRM_WITHDRAWAL))
handle_notify_referal_about_withdrawal = lambda dp: dp.register_callback_query_handler(notify_referal_about_withdrawal, text_startswith=CONFIRM_WITHDRAWAL)
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
    await callback.bot.send_message(client_id, f'{balance} руб. переведены вам с реферального счета')
    await callback.bot.delete_message(chat_id = callback.message.chat.id, message_id = callback.message.message_id)
    await callback.bot.send_message(callback.from_user.id, 'Клиент оповещён о совершенной опперации')

# @dp.callback_query_handler(lambda c: c.data == TURN_NOTIFICATIONS_OFF, state = '*')
handle_turn_notifications_off = lambda dp: dp.register_callback_handler(turn_notifications_off, text=TURN_NOTIFICATIONS_OFF, state='*') 
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


# @dp.callback_query_handler(lambda c: c.data == TURN_NOTIFICATIONS_ON, state = '*')
handle_turn_notifications_on = lambda dp: dp.register_callback_handler(turn_notifications_on, text=TURN_NOTIFICATIONS_ON, state='*') 
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

# @dp.callback_query_handler(lambda callback: callback.data == MY_PROMOCODES, state = '*')
handle_show_promocodes = lambda dp: dp.register_callback_handler(show_promocodes, text=MY_PROMOCODES, state='*') 
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

# @dp.callback_query_handler(lambda callback: callback.data == SHOW_REFERAL_STATISTS, state = '*')
handle_send_referal_statistics = lambda dp: dp.register_callback_handler(send_referal_statistics, text=SHOW_REFERAL_STATISTS, state='*') 
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
                    user = (await callback.bot.get_chat_member(payment.client_id, payment.client_id)).user
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
            await callback.bot.send_document(callback.from_user.id, 
                InputFile(filename, 'Реферальная статистика golubin_bot.xlsx'))
        except:
            logging.critical('FAILED TO SEND REFERAL STATISTICS TO A CLIENT:', exc_info=True)
    finally:
        if os.path.exists(filename):
            os.remove(filename)


def register_handlers(dp: Dispatcher):
    handle_show_ref_system(dp)
    handle_require_withdrawal_of_referal_balance(dp)
    handle_get_back_to_ref_menu(dp)
    handle_get_requisites_to_withdraw(dp)
    handle_get_back_to_wallet_choosing(dp)
    handle_send_withdrawal_requirement(dp)
    handle_restore_ref_client_balance(dp)
    handle_notify_referal_about_withdrawal(dp)
    handle_turn_notifications_off(dp)
    handle_turn_notifications_on(dp)
    handle_show_promocodes(dp)
    handle_send_referal_statistics(dp)
