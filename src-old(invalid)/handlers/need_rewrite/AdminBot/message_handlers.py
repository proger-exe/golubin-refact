from decimal import InvalidOperation
import json
import logging
from os import remove
from typing import Tuple
from aiogram import Dispatcher
from aiogram.utils.exceptions import *
from aiogram.dispatcher.storage import FSMContext
from aiogram.types import Message, CallbackQuery
from db.promocodes import get_all_promocodes
from Referal.config import HAS_REFS, NOT_INVITED
from bot_get_nick import get_nick
from src.data.bot_data import BACK_BUTTON_TEXT, GET_PROMOCODE_SALE_PERIOD
from .keyboards import *
from .admin_bot_config import *
from .states import BotStates
from client import Client
from datetime import datetime, timedelta
from config import *
from bot_config import *
from Statistics import *
from aiogram_calendar import SimpleCalendar, simple_cal_callback
from aiogram.types import *
from Promocodes import *
from threading import Thread
from bot_keyboards import try_to_send_latest_messages, main_kb
import message_deleting
from src.apis.db import user 
from .google_sheets import *
from ClientsData.StopWords import edit_bot_filter
from .timed_sendings import *
from telebot import TeleBot
from threading import Thread
from . import timed_sendings
from telebot.types import InlineKeyboardMarkup as OldKb
from telebot.types import InlineKeyboardButton as OldButton
from telebot.types import InputMediaPhoto as OldMediaPh
from telebot.types import InputMediaVideo as OldMediaVd
from Referal import RefClient
from bs4 import BeautifulSoup as bs

def user_is_admin(id: int) -> bool:
    return id in admin_id_list

def init_message_handlers(dp: Dispatcher):
    bot = dp.bot
    message_deleting.init_callbacks(dp, PAYING_BOT_ID)
    
    def shceduled_messages_handler(message: str, photo_id: Union[str, None], button: Union[str, None], bot_id: int, video_id: Union[str, None]):
        if bot_id == PAYING_BOT_IS_CHOSEN:
            bot = TeleBot(PAYING_BOT_TOKEN)
        else:
            bot = TeleBot(bot_tokens[bot_id])

        users = user.get_all_user_ids()
        message_index = message_deleting.get_index_for_new_message()
        msgs = []
        kb = message_deleting.delete_message_kb(message_index, OldKb, OldButton)
        if button:
            button = OldButton(*button.split('\n'))
            kb.add(button)
            kb_ = OldKb()
            kb_.add(button)
            button = kb_
        media = []

        if photo_id or video_id:
            if photo_id:
                media.append(OldMediaPh(photo_id))
            if video_id:
                media.append(OldMediaVd(video_id))

        if media and len(bs(message).text) <= 1024:
            media[0].caption = message
            media[0].parse_mode = 'HTML'

        for i in USERS_THAT_ALLOWED_TO_DELETE_MESSAGES if not TESTING else (DEVELOPER_ID,):
            if media and media[0].caption:
                try:
                    _msgs = bot.send_media_group(i, media)

                    bot.send_message(
                        i, '_', reply_markup = kb)
                    
                    for m in _msgs: msgs.append((i, m.message_id))
                except Exception as e:
                    if str(e) not in (CHAT_NOT_FOUND_DESCRIPTION, FORBIDDEN_BY_USER, USER_IS_DEACTIVATED):
                        logging.error('FAILED TO SEND TIMED MESSAGE TO AN USER:', exc_info=True)
            else:
                try:
                    m = bot.send_message(i, message, reply_markup = kb if not media else None, parse_mode = 'HTML')
                    msgs.append((i, m.message_id))
                except Exception as e:
                    if str(e) not in (CHAT_NOT_FOUND_DESCRIPTION, FORBIDDEN_BY_USER, USER_IS_DEACTIVATED):
                        logging.error('FAILED TO SEND TIMED MESSAGE TO AN USER:', exc_info=True)
                else:
                    if media:
                        try:
                            _msgs = bot.send_media_group(i, media)
                        except Exception as e:
                            if str(e) not in (CHAT_NOT_FOUND_DESCRIPTION, FORBIDDEN_BY_USER, USER_IS_DEACTIVATED):
                                logging.error('FAILED TO SEND TIMED MESSAGE`S MEDIA TO AN USER:', exc_info=True)

                        for m in _msgs: msgs.append((i, m.message_id))

                        bot.send_message(i, '_', reply_markup = kb)

        try:
            for u in users:
                if u in USERS_THAT_ALLOWED_TO_DELETE_MESSAGES:
                    continue

                if media and media[0].caption:
                    try:
                        _msgs = bot.send_media_group(u, media)
                        if button:
                            _msgs.append(
                                bot.send_message(
                                    u, '_', reply_markup=button, reply_to_message_id=_msgs[-1].message_id)
                            )
                    except:
                        pass
                    else:
                        for m in _msgs: msgs.append((u, m.message_id))
                else:
                    try:
                        msgs.append(
                            (u, bot.send_message(u, message, parse_mode = 'HTML', reply_markup = button).message_id))

                        if media:
                            _msgs = bot.send_media_group(u, media)

                            for m in msgs: msgs.append((u, m.message_id)) 
                    except:
                        pass

            _bot_id = bot_id if bot_id != PAYING_BOT_IS_CHOSEN else PAYING_BOT_ID

            for u_id, m_id in msgs:
                message_deleting.save_sended_message_data(message_index, u_id, m_id, _bot_id)
        except Exception as e:
            logging.error('Something went wrong during message mailing: '+str(e), exc_info=True)

    timed_sendings.set_message_timer_handler(shceduled_messages_handler)
    timed_sendings.set_alarm_for_last_timed_messages()

    @dp.message_handler(lambda message: message.text == INCREASE_PERIOD, state = '*')
    async def increase_period(message: Message, state: FSMContext):
        await state.finish()
        if not user_is_admin(message.from_user.id):
            return
        await bot.send_message(message.from_user.id, 'Отправьте ник или id клиента, которому нужно увеличить период')
        await BotStates.get_client_nick.set()
    
    @dp.message_handler(state = BotStates.get_client_nick)
    async def get_client_nick(message: Message, state: FSMContext):
        if not user_is_admin(message.from_user.id):
            return 
        await state.finish()
        await BotStates.get_category.set()
        state = dp.current_state(chat = message.chat.id,
                user = message.from_user.id)
        await state.update_data(user_entity = message.text)
        await bot.send_message(
            message.from_user.id, 'Выберите категорию пользователя', reply_markup=category_choose_kb)
    
    @dp.message_handler(state = BotStates.get_category)
    async def get_client_category(message: Message, state: FSMContext):
        if not user_is_admin(message.from_user.id):
            return
        category = await try_to_get_category_by_its_string(message.text, message) 
        if category == None:
            return
        user_entity = (await state.get_data())['user_entity']
        id, nick = get_user_nick_or_id_by_entity(user_entity)
        current_client = None
        old_payment_end = datetime(1000, 1, 1, 0, 0, 0)
        if id:
            current_client, is_new = get_client_by_id(id, category)
            if not is_new:
                old_payment_end = current_client.last_payment_date
        elif nick:
            current_client, is_new = await try_to_get_client_by_nick(nick, category, message.from_user.id)
            if not current_client:
                await state.finish()
                return
            if not is_new:
                old_payment_end = current_client.last_payment_date
        if current_client != None:
            await ask_if_client_has_paid(state, message, current_client, old_payment_end)
        else:
            await notify_that_client_is_not_found(nick, id, message)
   
    async def try_to_get_category_by_its_string(str_category: str, message: Message) -> int:
        cat_nameses_ids = {v:k for k,v in message_category_names.items()}
        if str_category in cat_nameses_ids:
            return cat_nameses_ids[str_category]
        else:
            await bot.send_message(message.from_user.id, f'Не удаётся найти категорию: {str_category}')

    def get_user_nick_or_id_by_entity(user_entity) -> Union[int, str]:
        nick = ''
        id = None
        if user_entity.isdigit():
            id = int(user_entity)
            nick = ''
        elif user_entity.startswith('@'):
            nick = user_entity[1:]
        else:
            nick = user_entity
        return id, nick.lower()

    def get_client_by_id(id: int, category: int) -> Union[Client, bool]:
        current_client = Client.get_clients_by_filter(id=id, category = category)
        if not current_client:
            now = datetime.now()
            return Client(id, now, now, category), True  # True means that client is new
        else:
            return current_client[0], False

    async def try_to_get_client_by_nick(nick: str, category: int, requester_id: int) -> Union[Client, bool]:
        users = globals()['user'].get_all_user_ids()
        for u_id in users:
            try:
                user = (await bot.get_chat_member(u_id, u_id)).user
            except ChatNotFound:
                continue
            curr_nick = user.username
            if curr_nick:
                curr_nick = curr_nick.lower()
            if nick == curr_nick:
                current_client = Client.get_clients_by_filter(category, u_id)
                if not current_client:
                    now = datetime.now()
                    return Client(u_id, now, now, category), True
                else:
                    return current_client[0], False
        await bot.send_message(
            requester_id, f'Не удаётся найти пользователя {nick}. Отправьте его id.')
        return None, None

    async def ask_if_client_has_paid(
            state: FSMContext, 
            message: Message, 
            current_client: Client, 
            old_payment_end: datetime
        ):
            await state.finish()
            await BotStates.find_out_if_client_has_paid.set()
            state = dp.current_state(chat = message.chat.id,
                user = message.from_user.id)
            await state.update_data(client = current_client, old_payment_end = old_payment_end)
            await bot.send_message(
                message.from_user.id, 'Заплатил ли клиент?', reply_markup = keyboard_to_find_out_if_client_has_paid)

    async def notify_that_client_is_not_found(nick: str, id: int, message: Message):
        if nick:
            await bot.send_message(
                message.from_user.id, 
                f'Пользователь с ником {nick} не найден. Попробуйте снова или отправьте /cancel'
            )
        elif id:
            await bot.send_message(
                message.from_user.id, f'Пользователь с id {id} не найден. Попробуйте снова или отправьте /cancel')
        else:
            await bot.send_message(message.from_user.id, f'Не удаётся получить пользователя')

    @dp.message_handler(state = BotStates.find_out_if_client_has_paid)
    async def get_answer_if_client_has_paid(message: Message, state: FSMContext):
        if not user_is_admin(message.from_user.id):
            return
        answer = message.text
        if answer != CLIENT_DID_NOT_PAY and answer != CLIENT_PAID:
            await message.answer('Некоректный ответ: ' + answer)
            return
        data = await state.get_data()
        await state.finish()
        if answer == CLIENT_DID_NOT_PAY:
            await BotStates.get_number_of_days.set()
            await bot.send_message(
                message.from_user.id, 
                'Теперь отправьте количество дней, на которое необходимо увеличить срок',
                reply_markup = main_menu_kb
            )
        else:
            await BotStates.get_sum_of_payment.set()
            await bot.send_message(
                message.from_user.id, 
                'Отправьте размер оплаты',
                reply_markup = main_menu_kb
            )
        state = dp.current_state(chat = message.from_user.id, user = message.from_user.id)
        await state.update_data(
            client = data['client'], 
            old_payment_end = data['old_payment_end'], 
            did_pay = answer == CLIENT_PAID
        )

    @dp.message_handler(state = BotStates.get_sum_of_payment)
    async def get_sum_of_payment(message: Message, state: FSMContext):
        if not user_is_admin(message.from_user.id):
            return
        try:
            amount = Decimal(message.text.replace(',', '.').replace(' ', ''))
        except:
            await message.answer('Некоректное значение: ' + message.text + '. Отправьте заново')
            return
        data = await state.get_data()
        can_debit_money_from_referal_balance = False
        if RefClient.has_client_id(data['client'].id):
            ref_client = RefClient.get_client_by_id(data['client'].id)
            can_debit_money_from_referal_balance = ref_client.balance >= amount
            await BotStates.ask_if_bot_should_debit_money_from_referal_account.set()
        if not can_debit_money_from_referal_balance:
            await BotStates.get_number_of_days.set()
        state = dp.current_state(chat = message.from_user.id, user = message.from_user.id)
        await state.update_data(
            client = data['client'], 
            old_payment_end = data['old_payment_end'], 
            did_pay = True,
            amount = amount
        )
        if can_debit_money_from_referal_balance:
            kb = InlineKeyboardMarkup()
            kb.row(
                InlineKeyboardButton('Да', callback_data = DEBIT_MONEY_FROM_REFERAL_ACCOUNT),
                InlineKeyboardButton('Нет', callback_data = DO_NOT_DEBIT_MONEY_FROM_REF_ACCOUNT)
            )
            await bot.send_message(
                message.from_user.id,
                f'На реферальном счёте этого пользоваетля {ref_client.balance} руб. Списать сумму оплаты оттуда?',
                reply_markup = kb
            )
        else:
            await state.update_data(deposit_from_referal = False)
            await bot.send_message(
                message.from_user.id, 
                'Теперь отправьте количество дней, на которое необходимо увеличить срок'
            )

    @dp.callback_query_handler(lambda callback: callback.data in (DEBIT_MONEY_FROM_REFERAL_ACCOUNT, 
    DO_NOT_DEBIT_MONEY_FROM_REF_ACCOUNT), state = BotStates.ask_if_bot_should_debit_money_from_referal_account)
    async def deposit_money_from_referal_account(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        data['deposit_from_referal'] = callback.data == DEBIT_MONEY_FROM_REFERAL_ACCOUNT
        await state.finish()
        await BotStates.get_number_of_days.set()
        state = dp.current_state(chat = callback.from_user.id, user = callback.from_user.id)
        await state.set_data(data)
        await callback.message.edit_text('Теперь отправьте количество дней, на которое необходимо увеличить срок')

    @dp.message_handler(state = BotStates.get_number_of_days)
    async def get_number_of_day_to_increase(message: Message, state: FSMContext):
        if not user_is_admin(message.from_user.id):
            return
        data = await state.get_data()
        text = message.text
        num_of_days = 0
        if text.isdigit() or text[0] == '-' and text[1:].isdigit():
            num_of_days = int(text)
        else:
            await message.answer(f'Введено некорректное значение: {text}. Отправьте заново')
            return
        await state.finish()
        if data['did_pay']:
            await process_expand_period_for_a_fee(message, data, num_of_days)
        else:
            await process_expand_period_for_free(message ,data, num_of_days)

    async def process_expand_period_for_a_fee(message: Message, data: dict, num_of_days: int):
        client: Client = data['client']
        old_payment_end = data['old_payment_end'] 
        amount = data['amount']
        deposit_from_referal = data['deposit_from_referal']
        now = datetime.now()
        old_date = old_payment_end
        if not client.payment_end or client.payment_end < now:
            client.payment_end = now
        it_is_not_single_sub = len(Client.get_client_by_id(client.id)) == 1
        client.add_to_db()
        client.increase_period(num_of_days)
        client.warning_status = NOT_WARNED
        try:
            set_pause_for_expanding_period(client, num_of_days)
        except:
            logging.critical('Failed to set pause while expanding: ', exc_info=True)
        if deposit_from_referal:
            ref_client = RefClient.get_client_by_id(client.id)
            ref_client.balance -= amount
            ref_client.add_to_db()
        had_paid_periods = client.has_paid_period
        client.has_paid_period = True
        now = datetime.now()
        str_date = client.payment_end.strftime("%d.%m.%Y в %H:%M")
        str_amount = '{0:.2f}'.format(amount).replace('.', ',')
        await bot.send_message(
            message.from_user.id,
            f'Оставшийся срок подписки клиента увеличен до: {client.get_payment_days_left()}. '
            f'Подписка кончится {str_date} ' + \
            (f'(старое значение: {old_date})' if  old_payment_end.year != 1000 else '') + \
            ('' if not deposit_from_referal else f'\nС реферального счёта клиента списано {str_amount} руб.'),
            reply_markup = main_menu_kb
        )
        await bot.send_message(
            client.id,
            f'Вам увеличили срок подписки по категории '
            f'<b>{message_category_names[client.sending_mode]}</b> на <b>{num_of_days}</b>\n'
            f'Теперь срок окончания вашей подписки: <b>{str_date}</b>' + \
            ('' if not deposit_from_referal else f'\n(С вашего реферального счёта списано {str_amount} руб.)'),
            reply_markup = None, parse_mode = 'HTML'
        )
        is_new = old_payment_end.year == 1000
        save_to_statistics(
            new_clients = not had_paid_periods and not it_is_not_single_sub, 
            payments_sum = amount,
            new_payments = 1,
            repeated_payments = had_paid_periods,
            new_users = not had_paid_periods and not it_is_not_single_sub,
            conversions_to_client = not had_paid_periods and not is_new,
            trial_activations = 1,
            total_referal_commisions = amount if deposit_from_referal else 0.0,
            total_referal_income = amount if deposit_from_referal else 0.0,
            new_referal_buyers = int(deposit_from_referal and not ReferalPaymentsHistory.clientHasPayments(client.id))
        )
        PaymentHistory.savePayment(
            Payment(
                num_of_days, Decimal(amount) - Decimal(deposit_from_referal), 0.0, 
                client.id, comments = IS_ADDED_MANUALLY, category=client.sending_mode
            )
        )
        if deposit_from_referal:
            ReferalPaymentsHistory.save(ReferalPayment(now.date(), client.id, amount))
        date_of_recieveing_latest_messages = user.date_of_recieveing_latest_messages(client.id)
        if now > old_payment_end and not date_of_recieveing_latest_messages or \
        (now - date_of_recieveing_latest_messages).days >= 2:
            await try_to_send_latest_messages(client, now - old_payment_end)

    def set_pause_for_expanding_period(client: Client, num_of_days: int):
        if str(num_of_days) in pause_periods:
            client.max_pause_days = pause_periods[str(num_of_days)]
        elif num_of_days > days_per_period[ONE_YEAR]:
            client.max_pause_days = pause_periods[ONE_YEAR]
        else:
            greater_than_current = []
            for period in days_per_period:
                if days_per_period[period] > num_of_days:
                    greater_than_current.append(days_per_period[period])
            client.max_pause_days = pause_periods[str(min(greater_than_current))]
        client.used_pause_days = 0

    async def process_expand_period_for_free(message: Message, data: dict, num_of_days: int):
        client = data['client']
        it_is_only_one_sub = len(Client.get_client_by_id(client.id)) <= 1
        old_payment_end = data['old_payment_end']   
        now = datetime.now()
        old_date = old_payment_end
        if client.payment_end < now:
            client.payment_end = now    
        client.add_to_db()
        client.increase_period(num_of_days)
        client.warning_status = NOT_WARNED
        now = datetime.now()
        if client.trial_period_end and client.trial_period_end >= now:
            client.set_trial_period(client.trial_period_end+timedelta(days=num_of_days))
        else:
            client.set_trial_period(now+timedelta(days=num_of_days))
        str_date = client.payment_end.strftime("%d.%m.%Y в %H:%M")
        await bot.send_message(
            message.from_user.id,
            f'Оставшийся срок подписки клиента увеличен до: {client.get_payment_days_left()}. '
            f'Подписка кончится {str_date} ' + \
            (f'(старое значение: {old_date})' if  old_payment_end.year  != 1000 else ''),
            reply_markup = main_menu_kb
        )
        await bot.send_message(
            client.id,
            f'Вам увеличили срок подписки по категории '
            f'<b>{message_category_names[client.sending_mode]}</b> на <b>{num_of_days}</b>\n'
            f'Теперь срок окончания вашей подписки: <b>{str_date}</b>',
            reply_markup = None, 
            parse_mode = 'HTML'
        )
        is_new = old_payment_end.year == 1000
        save_to_statistics(
            new_users = it_is_only_one_sub,
            activated_trial = not it_is_only_one_sub and is_new,
            trial_activations = 1
        )
        date_of_recieveing_latest_messages = user.date_of_recieveing_latest_messages(client.id)
        if now > old_payment_end and not date_of_recieveing_latest_messages or \
        (now - date_of_recieveing_latest_messages).days >= 2:
            await try_to_send_latest_messages(client, now - old_payment_end)

    @dp.message_handler(lambda message: message.text == SEND_MESSAGE_AWAY, state = '*')
    async def get_message_to_send_away(message: Message, state: FSMContext):
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(
            'Этот бот', callback_data=CHOOSE_BOT_TO_SEND_MSG_AWAY+CALLBACK_SEP+str(PAYING_BOT_IS_CHOSEN))
        )
        for category in message_category_names:
            kb.add(InlineKeyboardButton(
                message_category_names[category], callback_data=CHOOSE_BOT_TO_SEND_MSG_AWAY+CALLBACK_SEP+str(category))
            )
        await message.answer('Выберите, в какого бота вы хотите сделать рассылку:', reply_markup=kb)

    @dp.callback_query_handler(lambda c: c.data.startswith(CHOOSE_BOT_TO_SEND_MSG_AWAY), state = "*")
    async def choose_bot_to_send(callback: CallbackQuery, state: FSMContext):
        await state.finish()
        bot_id = int(callback.data.split(CALLBACK_SEP)[1])
        user_id =  callback.from_user.id 
        if not user_is_admin(user_id):
            return
        await BotStates.get_message_to_send_away.set()
        state = dp.current_state(user = user_id, chat = user_id)
        await state.update_data(bot_id = bot_id)
        await bot.send_message(user_id, 'Отправьте текст для рассылки или /cancel')

    @dp.message_handler(state = BotStates.get_message_to_send_away)
    async def get_text_to_send_message_away(message: Message, state: FSMContext):
        from_user_id = message.from_user.id
        if not user_is_admin(from_user_id):
            return
        
        bot_id = (await state.get_data())['bot_id']

        await state.finish()
        await BotStates.get_button_with_link_for_mailing.set()
        state = dp.current_state(user = from_user_id, chat = from_user_id)
        await state.update_data(text = message.html_text, bot_id = bot_id)

        kb = InlineKeyboardMarkup()
        kb.row(
            InlineKeyboardButton('да', callback_data = ATTACH_BUTTON_TO_MESSAGE),
            InlineKeyboardButton('нет', callback_data = DONT_ATTACH_BUTTON)
        )

        text = 'Вы хотите прикрепить кнопку к сообщению?'
        await bot.send_message(from_user_id, text, reply_markup = kb)
    
    @dp.callback_query_handler(lambda call: call.data == ATTACH_BUTTON_TO_MESSAGE, 
        state = BotStates.get_button_with_link_for_mailing
    )
    async def attach_button_to_message(callback: CallbackQuery):
        await callback.message.edit_text('Пришлите через Enter:\n\n\t1)Название кнопки\n\t2)Ссылку для вшивания')

    @dp.message_handler(content_types = ['text'], state = BotStates.get_button_with_link_for_mailing)
    async def attach_button_to_msg(message: Message, state: FSMContext):
        if not user_is_admin(message.from_user.id):
            return
        
        data = (await state.get_data())
        data['button'] = message.text

        button = message.text.split('\n')
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(button[0], button[1]))

        try:
            await bot.send_message(message.from_user.id, 'Как будет выглядеть кнопка:', reply_markup=kb)
        except:
            await bot.send_message(message.from_user.id, 
                'Не удаётся сгенерировать кнопку, перепроверьте правильность ссылки', reply_markup=kb)
            return

        await state.finish()
        await BotStates.get_media_to_send_away.set()
        state = dp.current_state(chat = message.from_user.id, user = message.from_user.id)
        await state.set_data(data)

        kb = InlineKeyboardMarkup()
        kb.row(
            InlineKeyboardButton('да', callback_data = ATTACH_PHOTO_TO_MESSAGE),
            InlineKeyboardButton('нет', callback_data = DONT_ATTACH_PHOTOS)
        )
        
        text = 'Вы хотите прикрепить фото к сообщению?'
        if len(bs(message.text).text) > 1024:
            text += f'\n(Текст содержит {len(bs(message.text).text)} символов, поэтому фото будет отправлено отдельным сообщением)'
        await bot.send_message(message.from_user.id, text, reply_markup = kb)

    @dp.callback_query_handler(lambda call: call.data == DONT_ATTACH_BUTTON, 
        state = BotStates.get_button_with_link_for_mailing
    )
    async def get_media_to_send_message_away(callback: CallbackQuery, state: FSMContext):
        from_user_id = callback.from_user.id
        if not user_is_admin(from_user_id):
            return
        
        data = await  state.get_data()
        await state.finish()
        await BotStates.get_media_to_send_away.set()
        state = dp.current_state(user = from_user_id, chat = from_user_id)
        data['button'] = None
        await state.set_data(data)

        kb = InlineKeyboardMarkup()
        kb.row(
            InlineKeyboardButton('да', callback_data = ATTACH_PHOTO_TO_MESSAGE),
            InlineKeyboardButton('нет', callback_data = DONT_ATTACH_PHOTOS)
        )
        
        text = 'Вы хотите прикрепить фото к сообщению?'
        if len(bs(data['text']).text) > 1024:
            text += f'\n(Текст содержит {len(bs(data["text"]).text)} символов, поэтому фото будет отправлено отдельным сообщением)'
        await callback.message.edit_text(text, reply_markup = kb)
    
    @dp.callback_query_handler(lambda call: call.data == ATTACH_PHOTO_TO_MESSAGE, 
        state = BotStates.get_media_to_send_away
    )
    async def attach_photo_to_message(callback: CallbackQuery):
        await callback.message.edit_text('Пришлите фото')
    
    @dp.message_handler(content_types = ['photo'], state = BotStates.get_media_to_send_away)
    async def send_message_with_photo(message: Message, state: FSMContext):
        if not user_is_admin(message.from_user.id):
            return
        data = (await state.get_data())
        bot_id = data['bot_id']
        if bot_id != PAYING_BOT_IS_CHOSEN:
            await message.answer(
                f'Перешлите это фото в @{bot_names[bot_id]}, чтобы его получилось разослать')
        await state.finish()
        fileid = message.photo[0].file_id
        data['fileid'] = fileid
        await BotStates.get_video_to_send_away.set()
        state = dp.current_state(chat = message.from_user.id, user = message.from_user.id)
        await state.set_data(data)
        kb = InlineKeyboardMarkup()
        kb.row(
            InlineKeyboardButton('да', callback_data=ATTACH_VIDEO_TO_MESSAGE),
            InlineKeyboardButton('нет', callback_data=DONT_ATTACH_VIDEO)
        )
        await message.answer('Вы хотите прикрепить видео?', reply_markup = kb)

    @dp.callback_query_handler(lambda call: call.data == DONT_ATTACH_PHOTOS, 
        state = BotStates.get_media_to_send_away
    )
    async def get_video_for_message_without_photo(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        data['fileid'] = None
        await state.finish()
        await BotStates.get_video_to_send_away.set()
        state = dp.current_state(chat = callback.from_user.id, user = callback.from_user.id)
        await state.set_data(data)
        kb = InlineKeyboardMarkup()
        kb.row(
            InlineKeyboardButton('да', callback_data=ATTACH_VIDEO_TO_MESSAGE),
            InlineKeyboardButton('нет', callback_data=DONT_ATTACH_VIDEO)
        )
        await callback.message.edit_text('Вы хотите прикрепить видео?', reply_markup = kb)
    
    @dp.callback_query_handler(lambda call: call.data == ATTACH_VIDEO_TO_MESSAGE, 
        state = BotStates.get_video_to_send_away
    )
    async def attach_video_to_message(callback: CallbackQuery):
        await callback.message.edit_text('Пришлите видео')

    @dp.message_handler(content_types = ['video'], state = BotStates.get_video_to_send_away)
    async def send_message_with_video(message: Message, state: FSMContext):
        if not user_is_admin(message.from_user.id):
            return
        data = (await state.get_data())
        bot_id = data['bot_id']
        if bot_id != PAYING_BOT_IS_CHOSEN:
            await message.answer(
                f'Перешлите это видео в @{bot_names[bot_id]}, чтобы его получилось разослать')
        await state.finish()
        fileid = message.video.file_id
        data['video_fileid'] = fileid
        await BotStates.get_date_to_send_message.set()
        state = dp.current_state(chat = message.from_user.id, user = message.from_user.id)
        await state.set_data(data)
        kb = InlineKeyboardMarkup()
        kb.row(
            InlineKeyboardButton('сейчас', callback_data = DONT_ADD_TIME_FOR_MSG_SEND),
            InlineKeyboardButton('установить дату', callback_data = ADD_TIME_TO_SEND_MESSAGE)
        )
        await message.answer('Отправить сообщение прямо сейчас или по расписанию?', reply_markup = kb)
    
    @dp.callback_query_handler(lambda call: call.data == DONT_ATTACH_VIDEO, 
        state = BotStates.get_video_to_send_away
    )
    async def get_date_and_time_for_message_wihtout_video(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        data['video_fileid'] = None
        await state.finish()
        await BotStates.get_date_to_send_message.set()
        state = dp.current_state(chat = callback.from_user.id, user = callback.from_user.id)
        await state.set_data(data)
        kb = InlineKeyboardMarkup()
        kb.row(
            InlineKeyboardButton('сейчас', callback_data = DONT_ADD_TIME_FOR_MSG_SEND),
            InlineKeyboardButton('установить дату', callback_data = ADD_TIME_TO_SEND_MESSAGE)
        )
        await callback.message.edit_text('Отправить сообщение прямо сейчас или по расписанию?', reply_markup = kb)

    @dp.callback_query_handler(lambda call: call.data == DONT_ADD_TIME_FOR_MSG_SEND, 
        state = BotStates.get_date_to_send_message)
    async def send_message_away_without_schedule(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        await state.finish()
        await callback.message.edit_text('Идёт рассылка...')
        await send_message_away(callback.from_user.id, data['text'], 
            data['bot_id'], data['button'], data['fileid'], data['video_fileid'])
        await callback.message.delete()

    async def send_message_away(
    from_user_id: int, text: str, bot_id: int, button: str = None, photo: str = None, video: str = None):
        sended = unsended = 0
        message_index = message_deleting.get_index_for_new_message()

        if bot_id == PAYING_BOT_IS_CHOSEN:
            users = user.get_all_user_ids()
            current_bot = bot
        else:
            users = [c.id for c in Client.get_clients_by_filter(category = bot_id)]
            current_bot = Bot(bot_tokens[bot_id])

        media = None
        if photo or video:
            media = MediaGroup()
            if photo:
                media.attach_photo(photo)
            if video:
                media.attach_video(video)

        if media and len(bs(text).text) <= 1024:
            media.media[0].caption = text
            media.media[0].parse_mode = 'HTML'

        if button:
            button = InlineKeyboardButton(*button.split('\n'))

        kb = message_deleting.delete_message_kb(message_index)
        if button:
            kb.add(button)

        msgs = []
        for i in USERS_THAT_ALLOWED_TO_DELETE_MESSAGES if not TESTING else (from_user_id,):
            try:
                if media and media.media[0].caption:
                    _msgs = await current_bot.send_media_group(i, media)
                    await current_bot.send_message(
                        i, '_', reply_markup = kb, parse_mode = 'HTML')
                    for m in _msgs: msgs.append((i, m.message_id))
                else:
                    m = await current_bot.send_message(i, text, reply_markup = kb if not media else None, parse_mode = 'HTML')
                    msgs.append((i, m.message_id))

                    if media:
                        _msgs = await current_bot.send_media_group(i, media)
                        for m in _msgs: msgs.append((i, m.message_id))
                        current_bot.send_message(i, '_', reply_markup = kb)
            except (ChatNotFound, BotBlocked, UserDeactivated):
                pass
            except Exception as e:
                logging.error('FAILED TO SEND MESSAGE TO ADMIN:', exc_info=True)

        _bot_id = bot_id if bot_id != PAYING_BOT_IS_CHOSEN else PAYING_BOT_ID
        if button:
            kb = InlineKeyboardMarkup()
            kb.add(button)
            button = kb

        try:
            for u in users:
                if u in USERS_THAT_ALLOWED_TO_DELETE_MESSAGES:
                    continue

                try:
                    if media and media.media[0].caption:
                        _msgs = await current_bot.send_media_group(u, media)
                        
                        if button:
                            _msgs.append(
                                await current_bot.send_message(
                                    u, '_', reply_markup=button, reply_to_message_id=_msgs[-1].message_id)
                            )

                        for m in _msgs: msgs.append((u, m.message_id))
                    else:
                        msgs.append(
                            (u, (await current_bot.send_message(
                                u, text, parse_mode = 'HTML', reply_markup=button)).message_id)
                        )

                        if media:
                            _msgs = await current_bot.send_media_group(u, media)
                            for m in _msgs: msgs.append((u, m.message_id))
                except (ChatNotFound, BotBlocked, UserDeactivated):
                    unsended += 1
                except Exception as e:
                    unsended += 1
                    logging.error(
                        'Error while sending a message away to {0}: {1}'.format(str(u), str(e)), exc_info = True)
                else:
                    sended += 1
            for u_id, m_id in msgs:
                message_deleting.save_sended_message_data(message_index, u_id, m_id, _bot_id)
        except Exception as e:
            logging.error('Something went wrong during message mailing: '+str(e), exc_info=True)
        finally:
            await bot.send_message(from_user_id, f'Успешно: {sended}, не удалось отправить: {unsended}')
            if bot_id != PAYING_BOT_IS_CHOSEN:
                await (await current_bot.get_session()).close()
            
    @dp.callback_query_handler(lambda call: call.data == ADD_TIME_TO_SEND_MESSAGE, 
        state = BotStates.get_date_to_send_message)
    async def get_message_sending_date(callback: CallbackQuery, state: FSMContext):
        await callback.message.edit_text('Выберите дату отправки сообщения:', reply_markup = \
            await SimpleCalendar().start_calendar())

    @dp.callback_query_handler(simple_cal_callback.filter(), state = BotStates.get_date_to_send_message)
    async def get_message_sending_time(callback: CallbackQuery, callback_data: dict, state: FSMContext):
        selected, date = await SimpleCalendar().process_selection(callback, 
            callback_data)
        if not selected:
            return
        await state.update_data(schedule_date = date)
        await callback.message.edit_text('Теперь пришлите время отправки по МСК в формате <b>ЧЧ:ММ:СС</b>', 
            parse_mode = 'HTML')

    @dp.message_handler(state = BotStates.get_date_to_send_message)
    async def get_time_to_send_message(message: Message, state: FSMContext):
        try:
            due_time = datetime.strptime(message.text, '%H:%M:%S')
        except:
            await message.answer('Не удалось определить время, проверьте, соответсвует ли время формату')
            return
        
        data = await state.get_data()
        await state.finish()

        due_time -= timedelta(hours = 3) # sent time is time in UTC+03, server works in UTC+00
        due_time = due_time.replace(data['schedule_date'].year, data['schedule_date'].month, data['schedule_date'].day)

        set_timer_for_message(due_time, data['text'], data['button'], data['fileid'], data['bot_id'], data['video_fileid'])
        due_time += timedelta(hours = 3)
        
        if due_time.year != date.today().year:
            due_time = due_time.strftime('%b %d %Y %H:%M' + (':%S' if due_time.second else ''))
        else:
            due_time = due_time.strftime('%b %d %H:%M' + (':%S' if due_time.second else ''))
        
        await message.answer(f'Таймер сообщения установлен на {due_time}')

    async def send_statistics_for_period(data: dict, message: Message):
        th  = Thread(target = upload_payments_history_for_period, args = (data['first_date'], data['second_date']))
        th.start()
        await dp.bot.edit_message_text(
            'Статистика выгружена в гугл таблицу',
            message.chat.id, message.message_id, reply_markup = None
        )

    @dp.message_handler(lambda m: m.text == PROMOCODES, state = '*')
    async def edit_promocodes(message: Message, state: FSMContext):
        if not user_is_admin(message.from_user.id):
            return
        await state.finish()
        kb = InlineKeyboardMarkup()
        kb.row(
            InlineKeyboardButton('Добавить', callback_data = ADD_PROMOCODE),
            InlineKeyboardButton('Удалить', callback_data = DELETE_PROMOCODE)
        )
        kb.add(InlineKeyboardButton('Добавить вечную скидку', callback_data=SET_ENDLESS_SALE))
        try:
            text = await get_text_with_promocodes()
        except:
            logging.error('Failed to generate text with promocodes: ', exc_info = True)
        text += '\nВыберите действие:'
        max_tg_msg_length = 4096 
        if len(text) > max_tg_msg_length:
            sections = []
            group = [] # 10 messages per group
            for i in text.split('-----------------------------------'):
                if len(group) < 10:
                    group.append(i)
                else:
                    sections.append('-----------------------------------'.join(group))
                    group = []
            if group:
                sections.append('-----------------------------------'.join(group))
            for i in sections:
                if i != sections[-1]:
                    await message.answer(i, parse_mode='HTML')
                else:
                    await message.answer(i, reply_markup = kb, parse_mode='HTML')
        else:
            await message.answer(text, reply_markup = kb, parse_mode='HTML')

    @dp.callback_query_handler(lambda c: c.data == ADD_PROMOCODE, state = '*')
    async def get_promocode_category(callback: CallbackQuery, state: FSMContext):
        await state.finish()
        if not user_is_admin(callback.from_user.id):
            return
        await bot.send_message(
            callback.from_user.id,
            'Выберите категорию, на которую действует промокод',
            reply_markup=choose_promocode_cat
        )

    @dp.callback_query_handler(lambda c: c.data.startswith(PROMOCODE_CATEGORY), state = '*')
    async def get_promocode_act(callback: CallbackQuery, state: FSMContext):
        await state.finish()
        category = callback.data.split(CALLBACK_SEP)[1]
        text, category = get_info_about_chosen_category_and_category(category)
        await dp.bot.edit_message_text(
            text+'теперь выберите действие промокода',
            callback.message.chat.id, callback.message.message_id,
            reply_markup = get_choose_promocode_act(category), parse_mode = 'HTML'
        )
    
    def get_info_about_chosen_category_and_category(category: str) -> Tuple[str, Union[str, int]]:
        if category not in ('*', 'NULL'):
            category = int(category)
            return f'Вы выбрали категорию <b>{message_category_names[category]}</b>,\n', category
        else:
            return 'Вы выбрали все категории,\n', 'NULL'

    @dp.callback_query_handler(lambda c: c.data.startswith(TRIAL_EXTRA_DAYS), state = '*')
    async def get_trial_extra_days(callback: CallbackQuery, state: FSMContext):
        await state.finish()
        await BotStates.get_promocode_trial_days.set()
        state = dp.current_state(chat = callback.message.chat.id,
            user = callback.from_user.id)
        category = callback.data.split(CALLBACK_SEP)[1]
        await state.update_data(category = category, forever = 0)
        await dp.bot.edit_message_text(
            get_info_about_chosen_category_and_category(category)[0]+'<b>дни пробного периода</b>,\n'
            f'теперь отправьте, сколько дней пробного периода добавить: ',
            callback.message.chat.id, callback.message.message_id,
            reply_markup = None, parse_mode = 'HTML'
        )
    
    @dp.message_handler(state = BotStates.get_promocode_trial_days)
    async def get_extra_days_for_promocode(message: Message, state: FSMContext):
        if not user_is_admin(message.from_user.id):
            return
        if not message.text.isdigit() or '-' == message.text[0]:
            await dp.bot.send_message(message.from_user.id, f'Введено некоректное значение: {message.text}')
            return
        data = await state.get_data()
        category = data['category']
        await state.finish()
        await BotStates.get_promocode_due_time.set()
        state = dp.current_state(chat = message.chat.id,
            user = message.from_user.id)
        await state.update_data(category = category, trial_extra_days = int(message.text), 
            sale = 0.0, period = '0', forever = 0)
        kb = await SimpleCalendar().start_calendar()
        await dp.bot.send_message(
            message.from_user.id, 'Выберите дату окончания промокода', reply_markup = kb)

    @dp.callback_query_handler(lambda c: c.data.startswith(PAYMENT_SALE), state = '*')
    async def get_payment_sale(callback: CallbackQuery, state: FSMContext):
        await state.finish()
        await BotStates.get_promocode_sale.set()
        state = dp.current_state(chat = callback.message.chat.id,
            user = callback.from_user.id)
        category = callback.data.split(CALLBACK_SEP)[1]
        await state.update_data(category = category)
        await dp.bot.edit_message_text(
            get_info_about_chosen_category_and_category(category)[0]+'<b>скидка при оплате</b>,\n'
            f'теперь отправьте размер скидки в процентах: ',
            callback.message.chat.id, callback.message.message_id,
            reply_markup = None, parse_mode = 'HTML'
        )

    @dp.message_handler(state = BotStates.get_promocode_sale)
    async def get_promocode_sale(message: Message, state: FSMContext):
        if not user_is_admin(message.from_user.id):
            return
        value = message.text.replace(',', '.')
        is_valid = True
        if value[0] == '-':
            is_valid = False
        try:
            float(value)
        except ValueError:
            is_valid = False
        if not is_valid:
            await dp.bot.send_message(message.from_user.id, f'Введено некоректное значение: {message.text}')
            return
        data = await state.get_data()
        await state.finish()
        category = data['category']
        kb = InlineKeyboardMarkup()
        str_category = str(category)
        for p in payment_period_costs:
            kb.add(
                InlineKeyboardButton(
                    p+' дн.', callback_data = CALLBACK_SEP.join([GET_PROMOCODE_SALE_PERIOD, p, str_category, value])
                )
            )
        kb.add(
            InlineKeyboardButton(
                'Все периоды', 
                callback_data = CALLBACK_SEP.join([GET_PROMOCODE_SALE_PERIOD, 'NULL', str_category, value])
            )
        )
        await bot.send_message(
            message.from_user.id, 'Выберите период, на котором будет активна скидка:', reply_markup = kb)

    @dp.callback_query_handler(lambda callback: callback.data.startswith(GET_PROMOCODE_SALE_PERIOD), state = '*')
    async def get_promocode_period(callback: CallbackQuery, state: FSMContext):
        await state.finish()
        _, period, category, sale = callback.data.split(CALLBACK_SEP)
        _, category = get_info_about_chosen_category_and_category(category)
        await BotStates.get_info_whether_sale_promocode_is_endless.set()
        state = dp.current_state(chat = callback.from_user.id, user = callback.from_user.id)
        await state.update_data(period = period, category = category, sale = Decimal(sale), trial_extra_days = 0)
        kb = InlineKeyboardMarkup()
        kb.row(InlineKeyboardButton('да', callback_data=GET_INFO_WHETHER_SALE_PROMOCODE_IS_ENDLESS+CALLBACK_SEP+'1'),
               InlineKeyboardButton('нет', callback_data=GET_INFO_WHETHER_SALE_PROMOCODE_IS_ENDLESS+CALLBACK_SEP+'0')
        )
        await callback.message.edit_text('Будет ли скидка промокода действовать вечно?', reply_markup=kb)

    @dp.callback_query_handler(
            lambda call: call.data.startswith(GET_INFO_WHETHER_SALE_PROMOCODE_IS_ENDLESS+CALLBACK_SEP), 
            state = BotStates.get_info_whether_sale_promocode_is_endless
    )
    async def get_info_if_sale_is_for_ever(callback: CallbackQuery):
        value = int(callback.data.split(CALLBACK_SEP)[1])
        state = dp.current_state(chat = callback.from_user.id, user = callback.from_user.id)
        data = await state.get_data()
        data['forever'] = value
        await state.finish()
        await BotStates.get_promocode_due_time.set()
        state = dp.current_state(chat = callback.from_user.id, user = callback.from_user.id)
        await state.set_data(data)
        kb = await SimpleCalendar().start_calendar()
        await callback.message.edit_text('Выберите дату окончания промокода', reply_markup = kb)

    @dp.callback_query_handler(simple_cal_callback.filter(), state = BotStates.get_promocode_due_time)
    async def get_promocode_due_time(callback: CallbackQuery, callback_data: dict):
        selected, date = await SimpleCalendar().process_selection(callback, callback_data)
        if not selected:
            return
        state = dp.current_state(chat = callback.from_user.id, user = callback.from_user.id)
        data = await state.get_data()
        data['due_date'] = date
        await state.finish()
        await BotStates.get_promocode.set()
        state = dp.current_state(chat = callback.from_user.id, user = callback.from_user.id)
        await state.set_data(data)
        await callback.message.edit_text('Теперь введите сам промокод (либо /cancel)')

    @dp.message_handler(state = BotStates.get_promocode)
    async def get_promocode(message: Message, state: FSMContext):
        if not user_is_admin(message.from_user.id):
            return
        promocode = message.text.lower()
        if promocode_is_in_db(promocode):
            await dp.bot.send_message(
                message.from_user.id, f'Промокод {promocode} уже существует. Введите другой или нажмите /cancel')
            return
        data = await state.get_data()
        await state.finish()
        await BotStates.get_promocode_refer.set()
        state = dp.current_state(chat = message.from_user.id, user = message.from_user.id)
        data['promocode'] = promocode
        await state.set_data(data)
        await message.answer('Хотите ли вы привязать промокод к реферальной ссылке?', 
            reply_markup = keyboard_to_find_out_if_promocode_belongs_refer)

    @dp.callback_query_handler(
        lambda callback: callback.data in (PROMOCODE_BELONGS_REFER, PROMOCODE_DOESNT_BELONG_REFER),
        state = BotStates.get_promocode_refer
    )
    async def find_out_if_promocode_belongs_refer(callback: CallbackQuery, state: FSMContext):
        if callback.data == PROMOCODE_DOESNT_BELONG_REFER:
            data = await state.get_data()
            await state.finish()
            data['refer'] = 0
            await callback.message.delete()
            await save_promocode(data, callback.from_user)
        else:
            await callback.message.edit_text('Отправьте id пользователя, которого хотите прикрепить к промокоду')
    
    @dp.message_handler(state = BotStates.get_promocode_refer)
    async def get_promocode_refer(message: Message, state: FSMContext):
        if not user_is_admin(message.from_user.id):
            return
        try:
            refer_id = int(message.text)
        except:
            await message.answer('Некорректное значение, попробуйте ещё раз')
            return
        if RefClient.has_client_id(refer_id):
            refer = RefClient.get_client_by_id(refer_id)
            refer.referal_status = HAS_REFS
        else:
            refer = RefClient(refer_id, HAS_REFS, Decimal('0'), NOT_INVITED)
            refer.add_to_db()
        data = await state.get_data()
        await state.finish()
        data['refer'] = refer_id
        await save_promocode(data, message.from_user)
        
    async def save_promocode(data: dict, from_user: User):
        category = data['category']
        trial_extra_days = data['trial_extra_days']
        payment_sale = data['sale']
        period = data['period']
        due_date = data['due_date']
        promocode = data['promocode']
        refer = data['refer']
        forever = data['forever']
        try:
            add_promocode(promocode, category, trial_extra_days, payment_sale, period, due_date, refer, forever)
        except:
            logging.error(
                f'Failed to add promocode({promocode}, category = {category}, '
                f'trial_days = {trial_extra_days}, sale = {payment_sale}, '
                f'period = {period}, due_date = {due_date}, from_refer = {refer}, forever = {forever}): ',
                exc_info = True
            )
            await dp.bot.send_message(from_user.id, 'При добавлении промокода произошла ошибка')
        else:
            text = 'Промокод успешно добавлен'
            try:
                if refer:
                    user = (await dp.bot.get_chat_member(refer, refer)).user
                    text  += '.\nЕго владельцем установлен ' + (await get_nick(user))
            except:
                logging.error(f'Failed to get nickname for refer {refer} while adding promocode: ', exc_info = True)
            await dp.bot.send_message(from_user.id, text)
            if refer:
                await bot.send_message(
                    refer, f'К вашей реферальной системе был привязан промокод: "<code>{promocode}</code>"', 
                    parse_mode='HTML'
                )

    @dp.callback_query_handler(lambda callback: callback.data == DELETE_PROMOCODE, state = '*')
    async def get_promocode_to_delete(callback: CallbackQuery, state: FSMContext):
        await state.finish()
        if not user_is_admin(callback.from_user.id):
            return
        text = callback.message.text.split('\n')
        text.pop(len(text) - 1) # drop row which ask to choose action
        text = '\n'.join(text)
        text += '\nОтправьте промокод для удаления'
        await BotStates.get_promocode_to_delete.set()
        if callback.message != text:
            await callback.message.edit_text(text, parse_mode = 'HTML')

    async def get_text_with_promocodes() -> str:
        text = 'Ваши текущие промокоды:\n\n'
        promocodes = get_all_promocodes()
        len_promocodes = len(promocodes)
        for i, p in enumerate(promocodes):
            p = p[1:] # first column is an ID
            category = p[1]
            if category != None:
                category = message_category_names[category]
            else:
                category = 'Все категории'
            text += f'"<code>{p[0]}</code>":\n\t- <i>{category}</i>'
            if p[2]: #trial days
                text += f'\n\t- <b>{p[2]}</b> дн. пробного периода'
            elif p[3]:
                if not p[4]: # period is not set (all periods)
                    text += f'\n\t- <b>{p[3]}</b>% на все периоды. '
                else:
                    text += f'\n\t- <b>{p[3]}</b>% для {p[4]} дн. '
            if p[5]:
                text += f'\n\t- До <u>{p[5].strftime("%d.%m.%Y")}</u>'
            try:
                if p[6]:
                    try:
                        user = (await dp.bot.get_chat_member(p[6], p[6])).user
                        nick = await get_nick(user)
                    except:
                        nick = p[6]
                    text += f'\n\t- Рефер: {nick}'
            except Exception as e:
                logging.error(
                    f'Failed to get username from refer {p[6]}, which has promocode "{p[0]}": '+str(e), exc_info=True)
                text += f' Рефер: {p[6]}'
            if p[7]:
                text += f'\n\t- вечная скидка'
            text += '\n'
            if i != len_promocodes - 1:
                text += '-----------------------------------\n'
        return text

    @dp.message_handler(state = BotStates.get_promocode_to_delete)
    async def del_prom(message: Message, state: FSMContext):
        promocode = message.text.lower()
        if not promocode_is_in_db(promocode):
            await dp.bot.send_message(message.from_user.id, 'Не найден промокод "'+message.text+'"')
            return
        await state.finish()
        try:
            delete_promocode(promocode)
        except Exception as e:
            logging.error(f'Failed to delete promocode "{promocode}": {str(e)}', exc_info = True)
            await dp.bot.send_message(message.from_user.id, 'Во время удаления промокода произошла ошибка')
        else:
            await dp.bot.send_message(message.from_user.id, 'Промокод успешно удалён.')

    @dp.callback_query_handler(lambda call: call.data == SET_ENDLESS_SALE, state = '*')
    async def get_promocode_to_set_endless_sale(callback: CallbackQuery, state: FSMContext):
        await state.finish()
        await BotStates.get_promocode_to_set_endless_sale.set()
        await bot.send_message(callback.from_user.id, 'Отправьте промокод со скидкой, чтобы сделать её вечной')

    @dp.message_handler(state = BotStates.get_promocode_to_set_endless_sale)
    async def set_endless_sale(message: Message, state: FSMContext):
        pcd = message.text.lower()
        if not promocode_is_in_db(pcd):
            await message.reply('Не удалось найти такой промокод')
            return
        try:
            promocodes.set_endless_sale_on_promocode(pcd)
        except ValueError:
            await message.reply('Этот промокод добавляет пробные дни, не скидку')
            return
        await message.reply('Скидка на промокоде теперь вечна')

    @dp.message_handler(
        lambda message: message.text == SEND_MESSAGE_TO_SPECIAL_CHANNEL and user_is_admin(message.from_user.id), 
        state = '*')
    async def get_message_for_special_channel(message: Message, state: FSMContext):
        await state.finish()
        await message.answer('Отправьте текст для отправки в чат:')
        await BotStates.get_message_to_send_to_special_channel.set()

    @dp.message_handler(
        lambda message:  user_is_admin(message.from_user.id), state = BotStates.get_message_to_send_to_special_channel,
        content_types = ['text', 'photo']
    )
    async def send_message_to_special_channel(message: Message, state: FSMContext):
        if message.photo:
            await bot.send_photo(SPECIAL_CHAT_ID, message.photo[0].file_id, caption = message.caption)
        else:
            await bot.send_message(SPECIAL_CHAT_ID, message.text)
        await state.finish()

    @dp.callback_query_handler(lambda callback: callback.data == EDIT_STOP_WORDS_CALLBACK, state = '*')
    async def edit_filter_callback_handler(callback: CallbackQuery, state: FSMContext):
        await edit_filter(state, callback=callback)

    async def edit_filter(state: FSMContext, callback: CallbackQuery = None, message: Message = None):
        if callback != None:
            from_user = callback.from_user
        elif message != None:
            from_user = message.from_user
        if not user_is_admin(from_user.id):
            return
        await state.finish()
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for i in range(0, len(message_category_names), 2):
            c = list(message_category_names.keys())[i]
            if i + 1 < len(message_category_names):
                c2 = list(message_category_names.keys())[i + 1]
                kb.row(
                    KeyboardButton(
                        message_category_names[c], callback_data = PROMOCODE_CATEGORY+CALLBACK_SEP+str(c)),
                    KeyboardButton(
                        message_category_names[c2], callback_data = PROMOCODE_CATEGORY+CALLBACK_SEP+str(c2))
                )
            else:
                kb.row(
                    KeyboardButton(
                        message_category_names[c], callback_data = PROMOCODE_CATEGORY+CALLBACK_SEP+str(c)),
                    KeyboardButton('Все', callback_data = PROMOCODE_CATEGORY+CALLBACK_SEP+'*')
                )
        if len(message_categories) % 2 == 0:
            kb.row(KeyboardButton(ALL_CATEGORIES), KeyboardButton('Назад'))
        else:
            kb.add(KeyboardButton('Назад'))
        if message != None:
            await message.answer('Выберите категорию фильтра:', reply_markup = kb)
        elif callback != None:
            await callback.message.delete()
            await bot.send_message(from_user.id, 'Выберите категорию фильтра:', reply_markup = kb)
        await BotStates.get_category_to_edit_filter.set()

    @dp.message_handler(lambda message: message.text == EDIT_STOP_WORDS, state = '*')
    async def edit_filter_message_handler(message: Message, state: FSMContext):
        await edit_filter(state, message=message)

    @dp.message_handler(state = BotStates.get_category_to_edit_filter)
    async def choose_category_to_edit_filter(message: Message, state: FSMContext):
        if not user_is_admin(message.from_user.id):
            return
        if message.text.lower() == 'назад':
            await state.finish()
            await bot.send_message(message.from_user.id, 'активирована панель администратора', 
                reply_markup = main_menu_kb, parse_mode = 'HTML')
            return
        kb = InlineKeyboardMarkup()
        if message.text == ALL_CATEGORIES:
            kb.row(
                InlineKeyboardButton('Добавить', callback_data = ADD_TO_FILTER + CALLBACK_SEP + '*'),
                InlineKeyboardButton('Удалить', callback_data = DEL_FROM_FILTER + CALLBACK_SEP + '*')
            )
            kb.add(
                InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data = EDIT_STOP_WORDS_CALLBACK)
            )
            await state.finish()
            msg =  await message.answer('Удаление клавиатуры', reply_markup = main_menu_kb)
            await msg.delete()
            await message.answer('Выберите действие со всеми фильтрами:', reply_markup=kb)
        else:
            try:
                category = {v: k for k, v in list(message_category_names.items())}[message.text]
            except:
                await message.answer('Введено некорректное значение, попробуйте ещё раз')
                return
            await state.finish()
            kb.row(
                InlineKeyboardButton('Добавить', callback_data = ADD_TO_FILTER + CALLBACK_SEP + f'{category}'),
                InlineKeyboardButton('Удалить', callback_data = DEL_FROM_FILTER + CALLBACK_SEP + f'{category}')
            )
            kb.add(
                InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data = EDIT_STOP_WORDS_CALLBACK)
            )
            with open(MESSAGE_FILTER) as f:
                filter = json.load(f)
            if str(category) in filter:
                filter = '\n'.join(filter[str(category)])
            else:
                filter = ''
            if len(filter) >= 4000:
                filename = 'temp_filter.txt'
                try:
                    with open(filename, 'w') as file:
                        file.write(filter) 
                    await bot.send_document(caption='Текущий фильтр:', 
                        chat_id=message.from_user.id, document=open(filename, 'rb'), reply_markup = main_menu_kb)
                except:
                    logging.critical('Can not send filter to admin:', exc_info=True)
                finally:
                    remove(filename)
            else:
                if filter:
                    await message.answer('Текущий фильтр:\n'+filter, reply_markup = main_menu_kb)
                else:
                    await message.answer('Текущий фильтр пуст', reply_markup = main_menu_kb)
            await message.answer('Выберите действие с фильтром: ', reply_markup=kb)

    @dp.callback_query_handler(lambda callback: callback.data.startswith(ADD_TO_FILTER), state = '*')
    async def add_to_filter(callback: CallbackQuery, state: FSMContext):
        if not user_is_admin(callback.from_user.id):
            return
        await state.finish()
        category = callback.data.split(CALLBACK_SEP)[1]
        try:
            await callback.message.delete()
            await bot.send_message(
                callback.from_user.id,
                'Введите через запятую слова или фразы, которые хотите добавить в стоп-список', 
                reply_markup = main_menu_kb
            )
        except (MessageNotModified, MessageToEditNotFound):
            return
        await BotStates.get_stop_words_to_edit_filter.set()
        state = dp.current_state(chat = callback.from_user.id, user = callback.from_user.id)
        await state.update_data(action = 'add', category = category)

    @dp.callback_query_handler(lambda callback: callback.data.startswith(DEL_FROM_FILTER), state = '*')
    async def del_from_filter(callback: CallbackQuery, state: FSMContext):
        if not user_is_admin(callback.from_user.id):
            return
        await state.finish()
        category = callback.data.split(CALLBACK_SEP)[1]
        try:
            await callback.message.delete()
            await bot.send_message(
                callback.from_user.id,
                'Введите через запятую слова или фразы, которые хотите удалить из стоп-списка', 
                reply_markup = main_menu_kb
            )
        except (MessageNotModified, MessageToEditNotFound):
            return
        await BotStates.get_stop_words_to_edit_filter.set()
        state = dp.current_state(chat = callback.from_user.id, user = callback.from_user.id)
        await state.update_data(action = 'del', category = category)

    @dp.message_handler(state = BotStates.get_stop_words_to_edit_filter)
    async def get_stop_words(message: Message, state: FSMContext):
        words = [w.strip() for w in message.text.lower().split(',')]
        data = await state.get_data()
        await state.finish()
        try:
            with open(MESSAGE_FILTER, 'r') as f:
                filter = json.load(f)
        except FileNotFoundError:
            with open(MESSAGE_FILTER, 'w') as f:
                f.write('{}')
            filter = {}
        if data['category'] == '*':
            for c in message_category_names:
                edit_bot_filter(filter, words, c, data['action'])
        else:
            edit_bot_filter(filter, words, data['category'], data['action'])
        with open(MESSAGE_FILTER, 'w') as f:
            json.dump(filter, f)
        if data['action'] == 'add':
            if data['category'] == '*':
                await message.answer('Новые слова были добавлены во все фильтры', reply_markup=main_menu_kb)
            else:
                await message.answer('Слова были добавлены в фильтр', reply_markup=main_menu_kb)
        else:
            if data['category'] == '*':
                await message.answer('Новые слова были удалены из всех фильтров', reply_markup=main_menu_kb)
            else:
                await message.answer('Слова были удалены из фильтра', reply_markup=main_menu_kb)

    @dp.message_handler(lambda message: message.from_user.id in admin_id_list and \
        message.text == CHANGE_REFERAL_CONDITIONS, state='*')
    async def change_ref_conditions(message: Message, state: FSMContext):
        await state.finish()
        await message.answer('Отправьте ID пользователя, которому хотите изменить реферальные условия')
        await BotStates.get_id_of_refer_to_customize_conditions.set()

    @dp.message_handler(lambda message: message.from_user.id in admin_id_list and \
        message.text == CHANGE_CHANNEL_OF_TRIAL_PERIOD, state='*')
    async def change_channel_for_trial(message: Message, state: FSMContext):
        await state.finish()
        await message.answer(
            'Отправьте через пробел ссылку на канал, а затем его ник и обязательно добавьте в него бота.')
        await BotStates.get_link_of_new_channel.set()
        
    @dp.message_handler(state=BotStates.get_link_of_new_channel)
    async def get_id_of_new_channel(message: Message, state: FSMContext):
        await state.finish()

        with open(BOT_DATA_FILE) as f:
            js = json.load(f)

        link = message.text.split()

        js['channel-for-using-trial'] = list(link)
        with open(BOT_DATA_FILE, 'w') as f:
            json.dump(js, f)
        await message.answer(f'Теперь подписка на {link[1]} обязательна для пользования пробным периодом')

    @dp.message_handler(lambda message: message.from_user.id in admin_id_list, 
        state = BotStates.get_id_of_refer_to_customize_conditions)
    async def catch_id_of_referal_to_customize_him(message: Message, state: FSMContext):
        try:
            ref_id = int(message.text)
        except:
            await message.answer('Введенно некорректное значение')
            return
        referal = None
        if not RefClient.has_client_id(ref_id):
            referal = RefClient(id, HAS_REFS, Decimal(0), NOT_INVITED)
            referal.add_to_db()
        else:
            referal = RefClient.get_client_by_id(ref_id)
        await state.finish()
        text = 'Текущие условия: \n'\
            f'\t' + str(int(referal.percent1*100)).replace('.', ',') + '% - начальный процент\n'\
            f'\t' + str(int(referal.percent2*100)).replace('.', ',') + '% - увеличенный процент\n'\
            f'\t{referal.required_referal_number} - требуемое количество активных рефералов для получения '\
            'увеличенного процента\n'\
            'Выберите условия, которые хотите поменять:'
        await message.answer(text, reply_markup=get_keyboard_to_customize_referal_conditions(ref_id))

    @dp.callback_query_handler(lambda callback: callback.from_user.id in admin_id_list and \
        callback.data.startswith(CUSTOMZE_REF_CONDITION+';'), state = '*')
    async def get_referal_condition_to_change(callback: CallbackQuery, state: FSMContext):
        await state.finish()
        _, what_edit, referal_id = callback.data.split(';')
        await BotStates.get_new_value_of_referal_condition.set()
        state = dp.current_state(chat = callback.from_user.id, user = callback.from_user.id)
        await state.update_data(what_edit = what_edit, referal_id = int(referal_id))
        await bot.send_message(callback.from_user.id, 'Введите новое значение:')

    @dp.message_handler(lambda message: message.from_user.id in admin_id_list,
        state = BotStates.get_new_value_of_referal_condition)
    async def customize_referal_condition(message: Message, state: FSMContext):
        data = await state.get_data()
        referal = RefClient.get_client_by_id(data['referal_id'])
        if data['what_edit'].startswith('percent'):
            try:
                value = Decimal(message.text.replace(',', '.')) / 100
            except InvalidOperation:
                await message.answer('Введенно некорректное значение')
                return
            if data['what_edit'] == 'percent1':
                referal.percent1 = value
            else:
                referal.percent2 = value
        elif data['what_edit'] == 'required_referal_number':
            try:
                value = int(message.text)
            except InvalidOperation:
                await message.answer('Введенно некорректное значение')
                return
            referal.required_referal_number = value
        referal.add_to_db()
        await state.finish()
        text = 'Текущие условия: \n'\
            f'\t' + str(int(referal.percent1*100)).replace('.', ',') + '% - начальный процент\n'\
            f'\t' + str(int(referal.percent2*100)).replace('.', ',') + '% - увеличенный процент\n'\
            f'\t{referal.required_referal_number} - требуемое количество активных рефералов для получения '\
            'увеличенного процента\n'\
            'Выберите условия, которые хотите поменять:'
        await message.answer(text, reply_markup=get_keyboard_to_customize_referal_conditions(data['referal_id']))
        await state.finish()
