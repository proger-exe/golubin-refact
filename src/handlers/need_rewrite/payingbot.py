import json
import logging
import os
import requests
from AdminBot.google_sheets import upload_month_income, upload_stat_about_each_category
from Statistics import statistics
from Statistics.config import FIRST_SERVICE_ANALYTICS_DATE
import Statistics
from typing import Union
import aiogram
from aiogram.types import *
from pandas import DataFrame
from telebot import TeleBot
from aiogram import types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.executor import start_polling, start_webhook
from Statistics.statistics import save_to_statistics
import Votes 
import bot_keyboards
from client import Client
from time import sleep
from threading import Thread
import yoomoney
import AdminBot
from AdminBot import user_is_admin, main_menu_kb
from bot_config import *
from telebot.types import InlineKeyboardMarkup as OldInlineKb
from telebot.types import InlineKeyboardButton as OldInlineButton
import schedule
from datetime import date, datetime, timedelta 
from config import *
from Referal import bot_referal, REF_START
import user
import Referal
from aiogram.dispatcher.storage import FSMContext
from ClientsData import Accounts, GoogleSheets
from ClientsData.Accounts.account_managing_keyboards import MAX_NUMBER_OF_ACCOUNTS
from src.handlers.rewrited.chat_collector import init_new_chat_handler

get_messages_number_per_month = None # function
do_clients_check = True
bot = aiogram.Bot(PAYING_BOT_TOKEN)
dp = aiogram.Dispatcher(bot, storage = MemoryStorage())
dp.middleware.setup(LoggingMiddleware())
checker_thread = None
ym_client = yoomoney.Client(CLIENT_TOKEN)
telebot = TeleBot(PAYING_BOT_TOKEN)

@dp.message_handler(commands='cancel', state='*')
async def stop_operation(message: Message, state: FSMContext):
    await state.finish()
    try:
        await bot.send_message(message.from_user.id, 'Операция отменена')
    except:
        pass

@dp.message_handler(commands = 'start', state = '*')
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    referal_id = None
    if REF_START in message.text:
        referal_id = await bot_referal.handle_start_with_referal_info(bot, message)
    try:
        if not await is_newbie(message.from_user.id, referal_id):
            await bot.send_message(
                message.from_user.id, 
                MAIN_MENU_TEXT,
                reply_markup = bot_keyboards.main_kb,
                parse_mode = 'HTML'
            )
        else:
            await process_newbie(message.from_user.id)
    except Exception as e:
        logging.error(f'Failed to process /start to ({message.from_user.id}): '+str(e), exc_info = True)

AdminBot.init_message_handlers(dp)
bot_keyboards.init_callback_query_handlers(dp, ym_client)
bot_referal.init_referal_m_handlers(dp)
Votes.set_main_bot_votes_statistics(dp)
Accounts.set_accounts_managing_handlers(dp)
GoogleSheets.set_google_sheet_add_handlers(dp)
init_new_chat_handler(dp)

async def is_newbie(user_id: int, referal_id: Union[int, None]) -> bool:
    '''
    Checks if an user is newbie. If it is, the function will save a new user to database and increase number
    of bot activates in statistics.
    Returns bool value of whether an user is newbie
    '''
    if not user.user_is_having_launched_bot(user_id):
        user.set_user_as_having_launched(user_id)
        ref_link = ''
        if referal_id:
            ref_link = f't.me/{PAING_BOT_NAME}?start=ref{referal_id}'
        save_to_statistics(
            bot_activates = 1,
            ref_link = ref_link
        )
        return True
    client = Client.get_client_by_id(user_id)
    if not client:
        return True
    return False

async def process_newbie(user_id: int):
    await bot.send_message(
        user_id, MAIN_MENU_FOR_NEWBIES_TEXT, reply_markup = bot_keyboards.kb_for_newbie, parse_mode = 'HTML')

@dp.callback_query_handler(lambda callback: callback.data == PROCESS_NEWBIE)
async def process_new_user(callback: CallbackQuery):
    await callback.message.edit_text(
        TEXT_TO_GET_LAST_MESSAGES_OR_TEST_PERIOD, reply_markup = bot_keyboards.kb_for_newbie)

@dp.message_handler(commands = 'admin', state = '*')
async def start_admin(message: types.Message):
    is_admin = user_is_admin(message.from_user.id)
    if not is_admin:
        return
    await bot.send_message(message.from_user.id, 'активирована панель администратора', 
        reply_markup = main_menu_kb, parse_mode = 'HTML')

@dp.message_handler(lambda message: message.chat.id == message.from_user.id, state=None) # keep at the bottom only!
async def unknown_command(message: Message):
    try:
        await message.answer('Команда не распознана, '
            'для управлением бота используйте меню, если у вас его нет нажмите /start')
    except:
        pass

def start_bot():
    if not TESTING:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        logging.basicConfig(
            filename = 'logs/bot-paying.log',
            filemode = 'a',
            level = logging.WARNING,
            format='[%(asctime)s]:(%(levelname)s):%(message)s', datefmt='%b/%d %H:%M:%S'
        )
        start_webhook(
            dispatcher = dp,
            webhook_path = '',
            on_startup = on_startup,
            on_shutdown = on_shutdown,
            skip_updates = False,
            host = WEBAPP_HOST,
            port = WEBAPP_PORT
        )
    else:
        logging.basicConfig(level = logging.INFO)
        start_polling(
            dispatcher = dp,
            on_shutdown = on_shutdown,
            on_startup = on_startup,
            skip_updates = True
        )

async def on_startup(dp: aiogram.Dispatcher):
    if not TESTING:
        await bot.set_webhook(PAYING_BOT_WEBHOOK_URL)
    global checker_thread
    checker_thread = Thread(target = clients_check, args = (telebot,))
    checker_thread.start()

async def on_shutdown(dp: aiogram.Dispatcher):
    global do_clients_check
    logging.warning('Paying bot is shutting down')
    do_clients_check = False
    checker_thread.join()
    if not TESTING:
        await bot.delete_webhook()
    logging.warning('Paying bot finished')    

def client_is_about_to_be_offered_sale(client: Client):
    period_end = client.trial_period_end
    if not period_end:
        return True
    return client.get_payment_days_left() <= DAYS_BEFORE_TRIAL_END_TO_OFFER_SALE and not client.was_offered_sale

def clients_check(bot: TeleBot):
    '''checks if somebody's payment period is over'''
    def check():
        clients = Client.get_all_clients_from_db()
        now = datetime.now()
        for user_id in user.get_all_user_ids():
            date_of_trying_to_buy = user.date_of_trying_to_buy(user_id)
            if not user.user_is_offered_trial(user_id):
                date = user.get_user_launching_date(user_id)
                if date and (now - date).days >= DAYS_AFTER_ACTIVATING_TO_OFFER_TRIAL:
                    ref_link = ''
                    refer = Referal.RefClient.get_client_by_id(user_id)
                    if refer and refer.referal_id:
                        ref_link = f'{REFERAL_ID}{refer.referal_id}'
                    
                    category = None 
                    
                    kb = OldInlineKb()
                    kb.add(OldInlineButton('Получить пробный период', 
                        callback_data = ACTIVATE_TRIAL_WITHOUT_CATEGORY))
                    if try_to_send_message(bot, user_id,
                        'Вижу, что ты даже не '
                        'активировал бесплатную подписку. '
                        'Наверно тебе не нужны клиенты сейчас, '
                        'но если все же нужны, то активируй '
                        'подписку прямо сейчас и получишь '
                        'приятный бонус. К тому же это тебя ни к '
                        'чему не обязывает)', 
                        reply_markup = bot_keyboards.get_kb_with_categories()
                    ):
                        user.set_user_as_offered_trial(user_id)
            if date_of_trying_to_buy and not user.is_asked_to_continue_payment(user_id):
                subscribes = Client.get_clients_by_filter(
                    id = user_id, payment_period_end = datetime.now(), greater = True)
                if (now - date_of_trying_to_buy).days < 1:
                    continue
                ask_to_continue = True
                for sub in subscribes:
                    if sub.last_payment_date >= date_of_trying_to_buy:
                        ask_to_continue = False
                        break
                    if sub.has_paid_period:
                        ask_to_continue = False
                if ask_to_continue:
                    kb = OldInlineKb()
                    kb.add(OldInlineButton('Выбрать категорию', callback_data = NEW_ORDER_BUTTON))
                    if try_to_send_message(
                        bot, user_id, 
                        'Ты вчера хотел оформить подписку. Продолжим? Чтобы ты все же получил бесплатные заявки)',
                        reply_markup = kb
                    ):
                        user.set_as_asked_to_continue_payment(user_id)
        for client in clients:
            client: Client
            days_left = client.get_payment_days_left()
            c_n = message_category_names[client.sending_mode]
            unpause_date = client.unpause_date
            if unpause_date and unpause_date <= datetime.now():
                try_to_send_message(bot, 
                    client.id, f'Время приостановки вашей подписки по категории {c_n} истекло.')
                client.unpause_date = None
            if (not client.did_activate_bot()) and (datetime.now() - client.last_payment_date).seconds >= 3600: #hour
                if try_to_send_message(bot, client.id,
                    'Внимание ❗\n\n'
                    f'Вы до сих пор не активировали этого бота <b>@{bot_names[client.sending_mode]}</b>\n\n'
                    'Сделайте это прямо сейчас, чтобы видеть новые заявки!', parse_mode = 'HTML'
                ):
                    client.set_as_activated_bot()
            if client.is_using_trial:
                if client_is_about_to_be_offered_sale(client):
                    if try_to_send_message(bot, client.id,
                        'Осталось меньше суток бесплатного '
                        f'тарифа по категории {c_n}\n\n'
                        f'При оплате тарифа на {PERIOD_WITH_BONUS_DAYS_AFTER_THE_END_OF_TRIAL} дн. в течение '
                        f'<b>суток</b>, вы получите бесплатно <b>{BONUS_DAYS_AT_THE_END_OF_TRIAL}</b> бонусных дней',
                        reply_markup = bot_keyboards.get_period_choosing_keyboard(client.sending_mode, {},
                            True, OldInlineKb, OldInlineButton), parse_mode = 'HTML'
                    ):
                        client.was_offered_sale = True
                        client.sale_offering_date = datetime.now()
            elif not client.has_paid_period:
                days_passed = (now - client.payment_end).days
                if not days_left and client.warning_status < WARNED_ONCE:
                    if try_to_send_message(
                        bot, client.id, f'Твой тариф по категории {c_n} закончился. Оплати чтобы не потерять заявки',
                        reply_markup = bot_keyboards.get_period_choosing_keyboard(
                            client.sending_mode, from_client=client.id, 
                            keyboardType=OldInlineKb, ButtonType=OldInlineButton
                        )
                    ):
                        client.warning_status = WARNED_ONCE
                elif not days_left and days_passed >= DAYS_AFTER_TRIAL_END_TO_OFFER_NEW_SALE and not \
                client.is_offered_sale_after_end_of_trial:
                    time = globals()['date'].today() - timedelta(days=1)
                    number_of_messages = statistics.get_new_messages_number(time, client.sending_mode)
                    if number_of_messages:
                        try:
                            message = bot.send_message(
                                client.id,
                                f'За прошедший день было {number_of_messages} заявок по категории {c_n}. '
                                'Оплати тариф и получи их!',
                                reply_markup = bot_keyboards.get_period_choosing_keyboard(
                                    client.sending_mode, {}, False, OldInlineKb, OldInlineButton, from_client = client.id)
                            )
                        except Exception as e:
                            str_e = str(e)
                            if str_e not in (CHAT_NOT_FOUND_DESCRIPTION, FORBIDDEN_BY_USER, USER_IS_DEACTIVATED):
                                logging.error(
                                    'Failed to offer client sale after '
                                    f'{DAYS_AFTER_TRIAL_END_TO_OFFER_NEW_SALE} days of trial end: ', 
                                    exc_info=True
                                )
                        else:
                            client.id_of_message_with_sale_after_end_of_trial = message.message_id
                if not days_left and days_passed >= 2 and not client.is_asked_why_didnt_pay:
                    if try_to_send_message(bot, client.id,
                        f'Твой пробный тариф категории {c_n} закончился\nПочему не готов оплатить',
                        reply_markup = bot_keyboards.kb_with_answers_why_didnt_buy_period(client.sending_mode)
                    ):
                        client.is_asked_why_didnt_pay = True
                        if not user.get_index_of_written_review(client.id):
                            kb = OldInlineKb()
                            kb.add(OldInlineButton('Написал', 
                                callback_data = CALLBACK_SEP.join([WROTE_REVIEW, str(client.sending_mode)])))
                            if try_to_send_message(bot, client.id, 
                                f'Если есть вопросы - напишите на @{EUGENIY_NICK}\n'
                                'Если тебе понравился бот - можешь '
                                'написать отзыв и получить'
                                'дополнительные дни тестового периода:\n\n'
                                '1 - просто отзыв в группу\n\n'
                                '3 - отзыв в котором будут содержаться ответы на вопросы\n'
                                '\t- Почему выбрали именно нас?\n'
                                '\t- Что вы о нас думаете?\n'
                                '\t- Какой результат получили?\n'
                                '\t- Кому вы могли бы еще порекомендовать наш сервис?\n\n'
                                '7 - видеоотзыв\n\n'
                                'https://vk.com/topic-210255350_48577580', reply_markup = kb
                            ):
                                user.set_index_of_written_review(client.id, WROTE_REVIEW_IN_THE_END_OF_TRIAL)
            elif client.payment_end > now:
                if (now - client.last_payment_date).days >= DAYS_AFTER_PAYMENT_TO_NOTIFY_ABOUT_REFERAL and \
                (not client.is_aware_about_referal) and not Referal.RefClient.get_client_by_id(client.id):
                    kb = OldInlineKb()
                    kb.add(
                        OldInlineButton('Подробнее', callback_data = Referal.BACK_TO_REFERAL_MENU)
                    )
                    if try_to_send_message(bot, client.id,
                        'Привет! У нас есть реферальная система, '
                        'по которой можешь получать до '
                        f'<b>{int(Referal.DEFAULT_PAYMENT_PERCENT_FOR_REFERAL_WITH_BIG_AMOUNT_OF_REFERS * 100)}%</b>.\n\n'
                        'Жми подробнее', reply_markup = kb, parse_mode = 'HTML'
                    ):
                        client.is_aware_about_referal = True
                # middle of the period
                elif (now - client.last_payment_date).days / client.payment_period >= 0.5 \
                and client.warning_status < WARNED_ONCE and client.has_paid_period and not \
                user.get_index_of_written_review(client.id):
                    client.warning_status = WARNED_ONCE
                    kb = OldInlineKb()
                    kb.add(OldInlineButton('Написал', 
                        callback_data = CALLBACK_SEP.join([WROTE_REVIEW, str(client.sending_mode)])))
                    if try_to_send_message(
                        bot, client.id,
                        F'Напиши отзыв и получи дополнительные '
                        f'дни пользования ботом по категории {c_n}:\n\n'
                        '1 - просто отзыв в группу\n\n'
                        '3 - отзыв в котором будут содержаться ответы на вопросы\n'
                        '\t- Почему выбрали именно нас?\n'
                        '\t- Что вы о нас думаете?\n'
                        '\t- Какой результат получили?\n'
                        '\t- Кому вы могли бы еще порекомендовать наш сервис?\n\n'
                        '7 - видеоотзыв\n\n'
                        'https://vk.com/topic-210255350_48577580',
                        kb
                    ):
                        user.set_index_of_written_review(client.id, WROTE_REVIEW_IN_THE_MIDDLE_OF_PAID_SUBSCRIBE)
            else:
                days_after_payment_period_end = (now - client.payment_end).days + \
                    (now - client.payment_end).seconds / (24 * 3600)
                if client.warning_status < WARNED_ONCE:
                    client.warning_status = WARNED_ONCE
                    cost = payment_period_costs[ONE_YEAR] - SALE_TO_YEAR_SUBSCRIBE_AFTER_END_OF_PAID_SUBSCRIBE 
                    try_to_send_message(
                        bot, client.id,
                        TEXT_AFTER_PAID_PERIOD_END.format(c_n, (now + timedelta(days = 1)).strftime('%d.%m.%Y'), 
                            MAX_NUMBER_OF_ACCOUNTS),
                        reply_markup = bot_keyboards.generate_text_and_keboard_for_payment(
                            client.sending_mode, ONE_YEAR, cost, {}, client.id, False, 
                            '', -1, '', False, False, inline_kb_type = OldInlineKb, 
                            inline_button_type = OldInlineButton
                        )[-1],
                        parse_mode = 'HTML'
                    )
                elif client.warning_status < WARNED_TWICE and days_after_payment_period_end >= 1:
                    client.warning_status = WARNED_TWICE
                    cost = payment_period_costs[ONE_YEAR] - SALE_TO_YEAR_SUBSCRIBE_AFTER_END_OF_PAID_SUBSCRIBE 
                    try_to_send_message(
                        bot, client.id,
                        SECOND_TEXT_AFTER_ONE_DAY_FROM_PAID_PERIOD_END,
                        reply_markup = bot_keyboards.generate_text_and_keboard_for_payment(
                            client.sending_mode, ONE_YEAR, cost, {}, client.id, False, 
                            '', -1, False, False, inline_kb_type = OldInlineKb, inline_button_type = OldInlineButton
                        )[-1],
                        parse_mode = 'HTML'
                    )
                elif client.warning_status < OFFERED_TO_PAY_AFTER_TWO_DAYS_OF_PAID_SUB_END and\
                days_after_payment_period_end >= 2:
                    client.warning_status = OFFERED_TO_PAY_AFTER_TWO_DAYS_OF_PAID_SUB_END
                    try_to_send_message(
                        bot, client.id,
                        f'Твой тариф по категории {c_n} закончился. Оплати чтобы не потерять заявки',
                        bot_keyboards.get_period_choosing_keyboard(
                            client.sending_mode, {}, False, OldInlineKb, OldInlineButton, client.id)
                    )
                elif client.warning_status < IS_ASKED_WHY_DIDNT_PAY and days_after_payment_period_end >= 3:
                    if try_to_send_message(
                        bot, client.id, f'Твой тариф по категории {c_n} закончился\nПочему не готов оплатить',
                        reply_markup = bot_keyboards.kb_with_answers_why_didnt_buy_period(client.sending_mode)
                    ):
                        client.warning_status = IS_ASKED_WHY_DIDNT_PAY
                        if not user.get_index_of_written_review(client.id):
                            kb = OldInlineKb()
                            kb.add(OldInlineButton('Написал', 
                                    callback_data = CALLBACK_SEP.join([WROTE_REVIEW, str(client.sending_mode)])))
                            if try_to_send_message(
                                bot, client.id,
                                'Напиши отзыв и получи дополнительные дни пользования ботом:\n\n'
                                '1 - просто отзыв в группу\n\n'
                                '3 - отзыв в котором будут содержаться ответы на вопросы\n'
                                '\t- Почему выбрали именно нас?\n'
                                '\t- Что вы о нас думаете?\n'
                                '\t- Какой результат получили?\n'
                                '\t- Кому вы могли бы еще порекомендовать наш сервис?\n\n'
                                '7 - видеоотзыв\n\n'
                                'https://vk.com/topic-210255350_48577580',
                                kb
                            ):
                                user.set_index_of_written_review(client.id, WROTE_REVIEW_IN_THE_END_OF_PAID_SUBSCIRBE)
            if (now - client.last_payment_date).days >= 1 and client.sending_mode in (TARGET_MODE, CONTEXT_MODE) \
            and not client.is_awared_about('vitamin'):
                if try_to_send_message(
                    bot, client.id, 
                    'Привет! Специально для таргетологов и директологов мы запартнерились с сервисом Vitamin.tools и теперь пользователи Golubin_bot могут получать до 20% от затрат на рекламу.\n\n'
                    'Проценты:\n'
                    'Контекстная реклама 15%\n'
                    'Таргетированная реклама 20%\n'
                    '2ГИС 23%\n'
                    'Avito 15%\n\n'
                    'Vitamin дает сразу максимальный процент, нет привязки к обороту и начисляет его после пополнения рекламного кабинета, а не после открутки. Важно! Регистрироваться нужно по реферальной ссылке ниже, если не по ней, то проценты будут ниже. Вывод на карту или Р/С без комиссии.\n\n'
                    'P.S. мне на карту выводят день в день)\n\n'
                    'Регистрируйся!\n'
                    'https://vitamin.tools/?ref2=bf27aa45-dbea-48a5-a398-6c29bc5cb699'
                ):
                    client.set_as_awared_about('vitamin')
    if not TESTING:
        print('schedulers are set')
        schedule.every(3).hours.do(check)
        schedule.every().day.at('00:00').do(upload_data_into_gsh, bot)
        schedule.every().day.do(update_exchange_rates)
        schedule.every(MESSAGE_NUMBER_LEVEL_CHECKING_FOR_EACH_CATEGORY_DELAY).hours.do(
            check_if_number_of_msgs_per_last_hour_is_too_low, bot)
        schedule.every(PERIOD_OF_NOTIFYING_ABOUT_LOW_NUMBER_OF_MESSAGES).hours.do(
            check_number_of_messages_for_each_category, bot)
    else:
        schedule.every().second.do(check)
    while do_clients_check:
        try:
            schedule.run_pending()
        except Exception as e:
            logging.critical('Error occured while schedule.pending: ', exc_info=True)
        sleep(10)

def try_to_send_message(
    bot: TeleBot, 
    chat_id: int, 
    message: str, 
    reply_markup: Union[InlineKeyboardMarkup, ReplyKeyboardMarkup] = None,
    parse_mode: str = None
) -> bool: # return True is sended succesfuly else False
    try:
        bot.send_message(chat_id, message, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        str_e = str(e)
        if str_e in (CHAT_NOT_FOUND_DESCRIPTION, FORBIDDEN_BY_USER, USER_IS_DEACTIVATED):
            return False
        logging.error('Error while sending message to client: '+str_e, e)
        return False
    return True

def upload_data_into_gsh(bot: TeleBot):
    yesterday = date.today() + timedelta(days = -1)
    logging.warning(f'started to upload google info for {yesterday}')
    try_to_call_google_sheets_updater(lambda : AdminBot.upload_payments_history_for_period(yesterday, yesterday),
        'Failed to update payments history:')
    try_to_call_google_sheets_updater(lambda: upload_clients_data(bot), 'Failed to upload clients data:')
    try_to_call_google_sheets_updater(lambda :\
        AdminBot.upload_analytics_to_google_sheet_for_period(FIRST_SERVICE_ANALYTICS_DATE, yesterday),
        'Failed to update analytics:'
    )
    try_to_call_google_sheets_updater(lambda: check_and_upload_month_info(bot),
        'FAILED TO UPLOAD MONTH INCOME:')
    try_to_call_google_sheets_updater(lambda: AdminBot.upload_new_messages_number(yesterday),
        'Failed to upload new messages number:')
    try_to_call_google_sheets_updater(lambda: AdminBot.upload_funnel_statistics(yesterday),
        'Failed to upload funnel statistics')
    try_to_call_google_sheets_updater(lambda: AdminBot.upload_referal_statistics(yesterday),
        'Failed to upload referal statistics')
    try_to_call_google_sheets_updater(AdminBot.update_new_messages_number_per_hour, 
        'FAILED TO UPDATE AVERAGE NUMBER OF MESSAGE PER HOUR')
    try_to_call_google_sheets_updater(lambda: GoogleSheets.upload_statistics_for_all_clients(yesterday),
        'FAILED TO UPLOAD STATISTICS OF BUTTON-CLICKINGS:')
    try_to_call_google_sheets_updater(lambda: AdminBot.upload_real_and_planned_income_for_the_day(yesterday),
        'FAILED TO UPLOAD STATISTICS OF REAL AND PLANNED INCOME:')
    try_to_call_google_sheets_updater(lambda: AdminBot.upload_referal_links_statistics_to_google_sheets(yesterday, bot),
        'FAILED TO UPLOAD STATISTICS OF REFERAL LINKS:', False)
    logging.warning('ended to upload info to google')

def try_to_call_google_sheets_updater(call_function, log_info: str, do_sleep: bool = True):
    ''' call_function is a lambda which calls the googlesheet-updating function '''
    try:
        call_function()
    except:
        logging.critical(log_info, exc_info = True)
    if do_sleep:
        sleep(60)

def upload_clients_data(bot: TeleBot):
    data_sheets, _, _, _, _ = AdminBot.generate_client_data_sheets()
    try:
        get_extra_information(bot, data_sheets)
    except Exception as e:
        logging.error(
            'Failed to get extra information of clients while uploading data into client google sheets: '+str(e), 
            exc_info  = True
        )
    try:
        AdminBot.upload_client_data_into_gsh(data_sheets)
    except Exception as e:
        logging.error('Failed to upload data into client google sheets: '+str(e), exc_info = True)

def get_extra_information(bot: TeleBot, data_sheets: DataFrame):
    for i in range(len(data_sheets)):
        id = data_sheets['id'][i]
        try:
            user = bot.get_chat_member(id, id)
        except:
            data_sheets['ник'][i] = 'Unknown'
        else:
            data_sheets['ник'][i] = user.user.username if user.user.username else user.user.full_name
        data_sheets['срок жизни'][i], data_sheets['суммарный доход'][i] = \
            AdminBot.get_term_and_total_income_of_client(data_sheets.id[i])

def check_and_upload_month_info(bot: TeleBot):
    today = date.today()
    with open(BOT_DATA_FILE) as f:
        bot_data = json.load(f)
    next_month_to_update = bot_data['next-month-to-update']
    if today.month - next_month_to_update >= 1 or (next_month_to_update == 12 and today.month == 1):
        try:
            year_to_update = today.year
            if next_month_to_update == 12:
                year_to_update -= 1
            upload_month_income(year_to_update, next_month_to_update)
            upload_stat_about_each_category(year_to_update, next_month_to_update)
        except Exception as e:
            logging.critical(f'FAILED TO UPLOAD TOTAL MONTH INCOME: {e}', exc_info = True)
        else:
            with open(BOT_DATA_FILE, 'r') as f:
                bot_data = json.load(f)
            bot_data['next-month-to-update'] = (next_month_to_update + 1) % 12
            with open(BOT_DATA_FILE, 'w') as f:
                json.dump(bot_data, f, indent = 4)
        upload_info_about_active_users(bot)

def upload_info_about_active_users(bot: TeleBot):
    active_n = user.set_unactive_users_and_get_active_number (
        bot, 'Проверка активности пользователей. Если вы увидели это сообщение - просто проигнорируйте его.'
    )
    try:
        AdminBot.upload_number_of_active_users(date.today(), active_n)
    except Exception as e:
        logging.critical(f'FAILET TO UPLOAD ACTIVE USERS NUMBER: ', exc_info=True)
        bot.send_message(DEVELOPER_ID, 'Failed to upload active users number')

def check_if_number_of_msgs_per_last_hour_is_too_low(bot: TeleBot):
    now = datetime.now()
    last_hour = now - timedelta(seconds = 3600)
    number_of_messages = Statistics.get_new_messages_number(last_hour)
    avg = Statistics.get_average_messages_number(last_hour.hour, week_day=now.weekday())
    if number_of_messages < avg * MIN_ALLOWED_PERCENT_OF_MSGS_NUM_DEVIATION:
        for id in (DEVELOPER_ID, EUGENIY_ID) if not TESTING else (DEVELOPER_ID,):
            #bot.send_message(DEVELOPER_ID, 'Быстрее чекать!')
            #import pdb; pdb.set_trace()
            bot.send_message(
                id, f'За последний час было только '
                f'<b>{number_of_messages}</b> сообщений (норма <b>{int(avg)}</b>)', parse_mode='HTML'
            )

def check_number_of_messages_for_each_category(bot: TeleBot):
    now = datetime.now()
    last_check_time = now - timedelta(seconds = 3600 * PERIOD_OF_NOTIFYING_ABOUT_LOW_NUMBER_OF_MESSAGES)
    text = f'За последние {PERIOD_OF_NOTIFYING_ABOUT_LOW_NUMBER_OF_MESSAGES} ч. в категории:\n'
    for category in message_categories:
        number_of_messages = sum([Statistics.get_new_messages_number(last_check_time + timedelta(seconds=3600*i), category)
            for i in range(PERIOD_OF_NOTIFYING_ABOUT_LOW_NUMBER_OF_MESSAGES)])
        avg = sum([Statistics.get_average_messages_number(last_check_time.hour+i, week_day=now.weekday(), category=category)
            for i in range(PERIOD_OF_NOTIFYING_ABOUT_LOW_NUMBER_OF_MESSAGES)])
        if number_of_messages < avg * MIN_ALLOWED_PERCENT_OF_MSGS_NUM_DEVIATION:
            text += \
                f'<i>{message_category_names[category]}</i> '\
                f'<b>{number_of_messages}</b> сообщений (норма <b>{int(avg)}</b>)\n'
    for id in (DEVELOPER_ID, EUGENIY_ID) if not TESTING else (DEVELOPER_ID,):
        bot.send_message(
            id, text, parse_mode='HTML'
        )

def update_exchange_rates():
    with open(BOT_DATA_FILE, 'r') as js:
        data = json.load(js)
    rates = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()
    data['rub-to-usd'] = rates['Valute']['USD']["Value"]
    with open(BOT_DATA_FILE, 'w') as js:
        json.dump(data, js, indent=4)

if __name__ == '__main__':
    start_bot()