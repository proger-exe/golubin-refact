from datetime import datetime, timedelta
import logging, asyncio, aiogram
import Votes

from History import *
from typing import Dict, Tuple, Union
from aiogram.types import *
from bot_config import *
from client import Client
from yoomoney import Quickpay
from yoomoney import Client as ymClient
from hashlib import blake2b
from telebot.types import InlineKeyboardMarkup as OldKbType
from telebot.types import InlineKeyboardButton as OldButtonType
from config import *
from Referal import RefClient
from Referal.config import * 
from decimal import Decimal
from Statistics import *

from Promocodes import *
from os import listdir
from ClientsData import *
import json

failed_to_delete = [] # messages that can not be deleted

main_kb = ReplyKeyboardMarkup(resize_keyboard = True)
main_kb.row(
    KeyboardButton(NEW_ORDER),
    KeyboardButton(TAB_HELPFUL_BUTTON)
)
main_kb.row(
    KeyboardButton(REPORT_ERROR),
    KeyboardButton(PARTNER_SHOWCASE)
)
main_kb.add(
    KeyboardButton(PERSONAL_CABINET),
    KeyboardButton(ADDITIONAL_OPTIONS)
)

personal_cabinet_kb = ReplyKeyboardMarkup(resize_keyboard = True)
personal_cabinet_kb.row(
    KeyboardButton(SUBSRIBES_BUTTON),
    KeyboardButton(STOP_WORDS)
)
personal_cabinet_kb.row(
    KeyboardButton(REFERAL_SYSTEM_BUTTON),
    KeyboardButton(Accounts.ACCOUNTS_BUTTON)
)
personal_cabinet_kb.row(
    KeyboardButton(Votes.GET_VOTE_STATISTICS),
    KeyboardButton('📋 Гугл таблицы') # can not import GoogleSheets (it causes a big circular import)
)
personal_cabinet_kb.add(
    KeyboardButton(MAIN_MENU)
)

additional_options_kb = ReplyKeyboardMarkup(resize_keyboard = True)
additional_options_kb.row(
    KeyboardButton(POST_APPLICATION),
    KeyboardButton(ADD_EXTERNAL_CHAT)
)
additional_options_kb.row(
    KeyboardButton(BUY_NEW_CATEGORY),
    KeyboardButton(ADS)
)
additional_options_kb.row(
    KeyboardButton(MAIN_MENU)
)

def get_kb_with_categories(
    text_for_back_button: str = '', requested_from: str = '', 
    for_callback:str = CHOOSE_CATEGORY
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    for cat in message_categories:
        callback_data = for_callback + CALLBACK_SEP + str(cat)
        if requested_from:
            callback_data += CALLBACK_SEP + requested_from
        kb.add(InlineKeyboardButton(message_category_names[cat], 
            callback_data = callback_data))
    if requested_from and text_for_back_button:
        kb.add(InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data = text_for_back_button))
    return kb

# this keyboard is sended when a client has used a trial period but didn't payed new one after the end
def kb_with_answers_why_didnt_buy_period(category: int, kb_type: type = OldKbType, bt_type: type = OldButtonType)\
 -> Union[InlineKeyboardMarkup, InlineKeyboardButton]:
    kb = kb_type()
    for answer in ANSWERS_WHY_DIDNT_BUY:
        i = list(ANSWERS_WHY_DIDNT_BUY.keys()).index(answer)
        kb.add(
            bt_type(answer, callback_data = CALLBACK_SEP.join([GET_ANSWER_WHY_DIDNT_BUY, str(i), str(category)]))
        )
    return kb
    
kb_for_newbie = ReplyKeyboardMarkup(resize_keyboard=True)
kb_for_newbie.row(
    KeyboardButton(NEW_ORDER),
    KeyboardButton(REFERAL_SYSTEM_BUTTON)
)
kb_for_newbie.row(
    KeyboardButton(TAB_HELPFUL_BUTTON),
    KeyboardButton(POST_APPLICATION)
)
kb_for_newbie.row(
    KeyboardButton(REPORT_ERROR),
    KeyboardButton(BUY_NEW_CATEGORY)
)
bot_senders = {}
for c in message_categories:
    if bot_tokens[c]:
        bot_senders[c] = aiogram.Bot(bot_tokens[c])
admin_bot = aiogram.Bot(PAYING_BOT_TOKEN)

def get_period_choosing_keyboard(
    mode: Union[int, str],
    sales: dict = {},
    with_sale_during_trial: bool = 0,
    keyboardType: type = InlineKeyboardMarkup, 
    ButtonType: type = InlineKeyboardButton,
    from_client: int = None,
    requested_from: str = '',
    with_get_last_msgs_button = False,
    referal_link: str = ''
) -> Union[InlineKeyboardMarkup, OldKbType]:
    kb = keyboardType()
    mode = int(mode)
    p = CHOOSE_PERIOD_PREFIX + CALLBACK_SEP
    str_sales = sales.copy()
    for i in str_sales:
        str_sales[i] = float(str_sales[i])
    str_sales = str(str_sales).replace(' ', '').replace('{','').replace('}', '')
    postfix = CALLBACK_SEP.join([str(mode), str_sales, str(int(with_sale_during_trial)), referal_link, requested_from])
    for i in payment_period_costs:
        kb.add(
            ButtonType(
                generate_inline_text_of_period_cost(i, mode, sales),
                callback_data = p+i+CALLBACK_SEP+postfix
            )    
        )
    if mode != TARGET_MODE and not with_sale_during_trial:
        attach_trial = True
        if from_client:
            client = Client.get_clients_by_filter(id = from_client, category = mode)
            if client:
                attach_trial = False
        if attach_trial:
            kb.add(
                ButtonType(
                    f'Пробный период на {TRIAL_PERIOD_DAYS} дн.', 
                    callback_data = CALLBACK_SEP.join([ACTIVATE_TRIAL, str(mode), referal_link])
                )
            )
    if with_get_last_msgs_button:
        kb.add(
            ButtonType('Получить последние сообщения за сутки', 
                callback_data = GET_LAST_MSGS_PER_DAY+CALLBACK_SEP+str(mode))
        )
    if requested_from:
        kb.add(
            ButtonType(BACK_BUTTON_TEXT, callback_data = requested_from)
        )
    return kb

def get_sale(sales: dict, period: str) -> Decimal:
    keys = list(sales.keys())
    if not keys:
        return Decimal(0)
    first_key = keys[0]
    if not '*' in first_key:
        if not period in sales:
            return Decimal(0)
        return Decimal(sales[period])
    if first_key  == '*': # for all periods
        return Decimal(sales['*'])
    if first_key.startswith('*^'): # for all except
        exceptions = first_key[2:].split(',')
        if period in exceptions:
            return Decimal(0)
        return Decimal(sales[first_key])
    return Decimal(0)

def generate_inline_text_of_period_cost(
    period: str, category: int, sales: dict
) -> str:
    prefix = ''
    if period == ONE_WEEK:
        prefix = '1 нед.'
    elif period == TWO_WEEKS:
        prefix = '2 нед.'
    elif period == THREE_WEEKS:
        prefix = '3 нед.'
    elif period == ONE_MONTH:
        prefix = '1 мес.'
    elif period == THREE_MONTHS:
        prefix = '3 мес.'
    elif period == SIX_MONTHS:
        prefix = '6 мес.'
    elif period == ONE_YEAR:
        prefix = '12 мес.'
    prefix += ' '
    sale = get_sale(sales, period)
    cost = 0
    if not sale:
        cost = get_period_cost_without_sales(period, category)
    else:
        cost = get_period_cost(period, category, sale)
    str_cost = delete_float_point_if_is_not_fraction(cost)
    if period == ONE_YEAR and len(str(int(cost))) >= 5:
        str_cost = str_cost[:2]+' '+str_cost[2:]
    usd_cost = convert_to_usd(Decimal(cost))
    usd_cost = delete_float_point_if_is_not_fraction(usd_cost)
    result = prefix + f'{str_cost} р | {usd_cost} $'
    return result

def delete_float_point_if_is_not_fraction(
    num:Union[Decimal, float]
) ->  str:
    int_num = int(num)
    if int_num - num == 0:
        num = str(int_num)
    else:
        num = '{0:.2f}'.format(num).replace('.', ',')
    return num

def get_period_cost_without_sales(period: str, mode: int) -> Decimal:
    cost = payment_period_costs[period]
    if mode not in CATEGORIES_WITHOUT_SALES:
        cost = payment_for_additional_categories_costs[period]
    if mode == PROPERTY_MODE:
        cost *= 5
    return cost

def get_period_cost(
    period: str,    
    mode: int, 
    sale: Decimal = Decimal(0),
) -> Decimal:
    cost = get_period_cost_without_sales(period, mode)
    cost -= cost*sale
    return cost

def convert_to_usd(cost_in_rubles: Decimal) -> Decimal:
    with open(BOT_DATA_FILE, 'r') as js:
        data = json.load(js)
    return cost_in_rubles / Decimal(f"{data['rub-to-usd']}")

def get_back_to_period_choosing( 
    mode: int, 
    sales: str, 
    with_sales_during_trial, 
    referal_link: str, 
    requested_from: str,
    ButtonType: type = InlineKeyboardButton 
) -> Union[InlineKeyboardButton,OldButtonType]: 
    return ButtonType(
        BACK_BUTTON_TEXT, callback_data = CALLBACK_SEP.join([
                SELECT_PER_CHOOSE_KB, str(mode), 
                str(sales).replace('{', '').replace('}', '').replace(' ', ''), 
                str(int(with_sales_during_trial)), referal_link, requested_from
            ])
    )

def client_is_in_sale_period(client: Client):
    offering_date = client.sale_offering_date
    if not offering_date:
        return False
    return (datetime.now() - offering_date).days <= SALE_PERIOD and not client.used_sale and client.was_offered_sale

async def send_latest_messages(client: Client, for_period: timedelta = timedelta(days = 1)):
    for_period = min(for_period, timedelta(days = 1))
    path_to_message = (NEW_MESSAGES_PATH+SENDED_DIR+msg_categories[client.sending_mode]) if not TESTING else \
        (TEMP_MESSAGES_PATH+SENDED_DIR+msg_categories[client.sending_mode])
    now = datetime.now()
    for m in listdir(path_to_message):
        m_dir = path_to_message + '/' + m
        try:
            files = listdir(m_dir)
        except FileNotFoundError:
            continue
        m_date = datetime.utcfromtimestamp(path.getctime(m_dir+'/'+files[0]))
        if now - m_date >= for_period: # out of period
            continue
        date_format = "%d.%m %H:%M"
        if TEXT_INFO in files:
            kb = None if not Votes.check_if_client_is_allowed_to_get_vote_buttons(client.id, client.sending_mode) else\
                Votes.generate_vote_keyboard()
            file_path = m_dir+'/'+TEXT_INFO
            try:
                with open(file_path, 'r') as f:
                    text = f.read() + '\n(Заявка за <b>{}</b>)'.format(
                        m_date.strftime(date_format)
                    )
            except FileNotFoundError:
                continue
            try:
                await bot_senders[client.sending_mode].send_message(client.id, text, reply_markup = kb,
                    parse_mode = 'HTML')
            except aiogram.utils.exceptions.CantParseEntities:
                pass
        elif FORWARD_INFO in files:
            kb = None if not Votes.check_if_client_is_allowed_to_get_vote_buttons(client.id, client.sending_mode) else\
                Votes.generate_vote_keyboard_for_forwarded_message()
            file_path = m_dir+'/'+FORWARD_INFO
            try:
                with open(file_path, 'r') as f:
                    info = f.read().split('\n')
            except FileNotFoundError:
                continue
            chat_id, message_id = int(info[0]), int(info[1])
            try:
                await bot_senders[client.sending_mode].forward_message(client.id, chat_id, message_id)
                if kb:
                    await bot_senders[client.sending_mode].send_message(client.id, '_', reply_markup = kb)
            except (ChatNotFound, BotBlocked):
                continue
            except Exception as e:
                logging.error(
                    f'Failed to forward message ({chat_id}, {message_id}) to new client: '+str(e), exc_info=True)
        await asyncio.sleep(5)

async def try_to_send_latest_messages(client: Client, for_period: timedelta = timedelta(days = 1)):
    print('STARTED TO SEND LATEST MESSAGES')
    try:
        await bot_senders[client.sending_mode].send_message(client.id, 'Сейчас Вам придут заявки за последние сутки')
    except (ChatNotFound, BotBlocked):
        await admin_bot.send_message(
            client.id, 
            f'Пожалуйста, активируйте бота рассылщика (@{bot_names[client.sending_mode]}) в течении 2-х минут, '
            'чтобы мы смогли отправить вам сообщения за последние сутки'
        ) 
        passed_time = 0
        delay = 10
        while passed_time < 120:
            passed_time += delay
            try:
                await bot_senders[client.sending_mode].send_message(client.id, 'Сейчас Вам придут заявки за последние сутки')
            except (ChatNotFound, BotBlocked):
                await asyncio.sleep(delay) # wait before client activates bot-sender
            else:
                break
    try:
        await send_latest_messages(client, for_period)
    except (ChatNotFound, BotBlocked, UserDeactivated):
        pass
    except Exception as e:
        logging.error('Failed to send latest messages to new user: '+str(e), exc_info = True)
        print('ENDED TO SEND LATEST MESSAGES')
        return
    print('ENDED TO SEND LATEST MESSAGES')
 

def generate_text_and_keboard_for_payment(
    mode: int, period: str, cost: Decimal, sales: Dict[str, Decimal], client_id: int, 
    with_sale_during_trial: bool, requested_from: str, message_id: int, referal_link: str, with_back_button: bool = True,
    check_if_client_can_use_sale: bool = True,
    inline_kb_type: type = InlineKeyboardMarkup, inline_button_type: type = InlineKeyboardButton
) -> Tuple[bool, str, InlineKeyboardMarkup]:
    '''
    returns: 
        1) whether user is allowed to pay in this message, 
        2) text for payment, 
        3) keyboard to pay and activate
    '''
    kb = inline_kb_type()
    if check_if_client_can_use_sale:
        client = Client.get_clients_by_filter(category = mode, id = client_id)
        if with_sale_during_trial:
            if client:
                client = client[0]
                is_allowed_to_pay = True
                text = ''
                if client.trial_period_end < datetime.now():
                    if with_back_button:
                        kb.add(get_back_to_period_choosing(mode, sales, with_sale_during_trial, referal_link, requested_from))
                    else:
                        kb = None
                    text = 'Срок действия бонусных дней истек'
                    is_allowed_to_pay = False
                if client.used_sale:
                    if with_back_button:
                        kb.add(get_back_to_period_choosing(mode, sales, with_sale_during_trial, referal_link, requested_from))
                    else:
                        kb = None
                    is_allowed_to_pay = False
                    text = 'Вы уже использовали бонусные дни', kb
                if not is_allowed_to_pay:
                    return is_allowed_to_pay, text, kb
        if isinstance(client, list) and client:
            client = client[0]
        if client and client.id_of_message_with_sale_after_end_of_trial == message_id:
            if with_back_button:
                kb.add(get_back_to_period_choosing(mode, sales, with_sale_during_trial, referal_link, requested_from))
            else:
                kb = None
            return False, 'Время действия бонусных дней истекло', kb
    h = blake2b((str(period)+str(datetime.now())+str(client_id)+str(cost)).encode('utf-8'), digest_size = 10)
    ym_user = ym_client.account_info()
    paying_buttons = []
    paying_buttons.append(
        inline_button_type('Оплатить', url = get_yoomoney_payment_link(
            h.hexdigest(), period, ym_user.account, mode, cost if cost < YOOMONEY_TRANSFER_CAP else cost / Decimal('2'))
        )
    )
    str_mode = str(mode)
    str_with_sale_during_trial = str(int(with_sale_during_trial))
    callback_data = CALLBACK_SEP.join(
        [PAY_FOR_PERIOD_PREFFIX, period, h.hexdigest(), str_mode, str_with_sale_during_trial, referal_link, 
         '1' if cost < YOOMONEY_TRANSFER_CAP else '2']) # how many trasnfers an user must commit
    paying_buttons.append(
        inline_button_type('Оплатил ✅', callback_data = callback_data))
    kb.row(*paying_buttons)
    referal_payment_text = generate_text_about_oportunity_of_paying_from_ref_bal(client_id, cost)
    str_cost = delete_float_point_if_is_not_fraction(cost)
    str_sales = str(sales).replace('{', '').replace('}', '').replace(' ', '')
    try:
        referal_callback_data = CALLBACK_SEP.join(
            [PAY_USING_REFERAL_BALANCE, period, str_mode, str_cost.replace(',', '.'), str_with_sale_during_trial,
                str_sales, referal_link, requested_from]
        )
        kb.add(inline_button_type('Оплатить с реферального счёта', callback_data = referal_callback_data))
    except:
        logging.error(
            f'Failed to add button to pay using referal balance with callback data: "{referal_callback_data}": ', 
            exc_info = True
        )
    if with_back_button:
        kb.add(get_back_to_period_choosing(mode, sales, with_sale_during_trial, referal_link, requested_from))
    cost_without_sales = get_period_cost_without_sales(period, mode)
    cost_without_sales = delete_float_point_if_is_not_fraction(cost_without_sales)
    str_cost = f'<b>{str_cost}</b>' if str_cost == cost_without_sales else f'<s>{cost_without_sales}</s> <b>{str_cost}</b>'
    return \
        True, \
        f'Вы выбрали тариф на <b>{days_per_period[period]}</b> '\
        f'дней (категория <b>{message_category_names[mode]}</b>), '\
        f'стоимость: {str_cost} руб.' + referal_payment_text + \
        ('\nВ подарок консультация по продажам с создателем бота' \
            if days_per_period[period] > days_per_period[SIX_MONTHS] else '') + \
        ('' if cost < YOOMONEY_TRANSFER_CAP else 
         F'\n\n<b>Внимание!</b> Yoomoney имеет ограничение на переводы через API (до {YOOMONEY_TRANSFER_CAP} руб.). ' + 
         f'Поэтому, для оплаты, вам нужно 2 раза перевести {cost/Decimal(2)} руб.'), \
        kb

def get_yoomoney_payment_link(
    label: str, payment_period: str, ym_user_id: str, mode:int, cost: Decimal
) -> str:
    quickpay = Quickpay(
        receiver=ym_user_id,
        quickpay_form="shop",
        targets=\
            f"Оплата работы Golubin бота на {days_per_period[payment_period]} дней "
            f"(категория: {message_category_names[mode]})",
        paymentType = "SB",
        sum = cost,
        label = label
    )
    return quickpay.redirected_url

def generate_text_about_oportunity_of_paying_from_ref_bal(user_id: int, cost: Decimal) -> str:
    if not RefClient.has_client_id(user_id):
        return ''
    ref_client = RefClient.get_client_by_id(user_id)
    if ref_client.balance < cost:
        return ''
    return f'\nНа вашем реферальном балансе сейчас <b>{ref_client.balance}</b> руб. ' \
        'Вы можете использовать его для оплаты.'

