from config import PAING_BOT_NAME as PAYING_BOT_NICK
from decimal import Decimal

REFERAL_INFO_TABLE = "referals_info"
CLIENT_ID = "client_id"
BALANCE = 'balance'
INVITED_BY = "invited_by"
REFERAL_STATUS = 'referal_status'
REFERAL_LINKS = 'ref_links'
REF_PERCENT_FOR_LITTLE_AMOUNT_OF_REFERALS = 'percent1'
REQUIRED_AMOUNT_OF_REFERALS_TO_GET_BIGGER_PERCENT = 'required_referal_number'
REF_PERCENT_FOR_BIG_AMOUNT_OF_REFERALS = 'percent2'
SHOW_NOTIFICATIONS = 'send_notifications'
REF_LINK_NAME = 'name'
REF_URL = 'url'
#statuses
NOT_INVITED = 0
HASNT_REFS = 0
HAS_REFS = 1
#bot buttons
REFERAL_SYSTEM_BUTTON = '💵 Реферальная система'
REFERAL_SYSTEM_BUTTON_FOR_NEWBIE = 'Реферальная система'
REF_START = 'ref'
#	inline buttons
REQUIRE_WITHDRAWAL_OF_REFERAL_BALANCE = 'wthdwl_of_ref_blnc'
WITHDRAW_REFERAL_BALANCE = 'wthdwl_ref_blnc'
BACK_TO_REFERAL_MENU = 'ref_back'
WITHDRAW_TO = 'wthdw_to'
QIWI = '0'
YOOMONEY = '1'
CARD = '2'
WALLET_NAMES = {
	QIWI: 'Qiwi кошелёк',
	YOOMONEY: 'ЮМани кошелёк',
	CARD: 'Банковская карта'
}
RESTORE_BALANCE = 'rstr_ref_blnc'
CONFIRM_WITHDRAWAL = 'confirm_wthdwl'
BACK_TO_WALLET_CHOOSING = 'wallet_back'
TURN_NOTIFICATIONS_OFF = 'notif_off'
TURN_NOTIFICATIONS_ON = 'notif_on'
MY_PROMOCODES = 'show_prm'
SHOW_REFERAL_STATISTS = 'ref_stats'
#defs
DEFAUL_REFERAL_PAYMENT_PERCENT = Decimal('0.10')
DEFAULT_PAYMENT_PERCENT_FOR_REFERAL_WITH_BIG_AMOUNT_OF_REFERS = Decimal('0.5')
DEFAULT_NUM_OF_ACTIVE_REFERALS_TO_GET_BIGGER_PERCENT = 15
REFERAL_ADDITIONAL_TRIAL_DAYS = 3

REFERAL_INFO_TEXT = '''
Ваша ссылка для приглашения: t.me/'''+PAYING_BOT_NICK+'?start='+REF_START+'''{0}

Баланс: {1} руб.

Текущее количество рефералов: {2}

Начисления: {3}% от каждой оплаты

Количество активаций: {4}

Количество оплативших: {5}

Количество оплат: {6}

Сумма оплат: {7} руб.

Чтобы начать получать {8}%,  необходимо иметь {9} активных рефералов.'''