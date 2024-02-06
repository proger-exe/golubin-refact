from datetime import datetime
from config import *
from Statistics.config import *

admin_id_list = (191004724, 1026133582, 1236978331, 253131227, 
	5091768057, 5035325356, 833663612, 476806184, 486877869, 1617121573, 1787839420)

TOKEN = '5023421808:AAHvhN8e4lxPI_npm4kxVpLb5u078-x4maY'

INCREASE_PERIOD = 'Увеличить период'
SEND_MESSAGE_AWAY = 'Сделать рассылку'
PROMOCODES = 'Промокоды'
ADD_PROMOCODE = 'add_prm'
DELETE_PROMOCODE = 'del_prm'
SET_ENDLESS_SALE = 'set_endless_sale'
SEND_MESSAGE_TO_SPECIAL_CHANNEL = 'Отправить сообщение в чат'
EDIT_STOP_WORDS = 'Стоп слова'
PROMOCODE_CATEGORY = 'get_prm_cat'
PROMOCODE_ACTION = 'get_prm_act'
TRIAL_EXTRA_DAYS = 'trl_d'
PAYMENT_SALE = 'get_pymnt_sale'
CHOOSE_STAT_COLUMN = 'chs_stat_clmn'
GET_TO_PERIOD_CHOOSING = 'gt_to_p_chs'
CLIENT_PAID = 'да'
CLIENT_DID_NOT_PAY = 'нет'
PROMOCODE_BELONGS_REFER = 'prmcd_blng_rf'
PROMOCODE_DOESNT_BELONG_REFER = 'prmcd_dsnt_blng_rf'
ATTACH_BUTTON_TO_MESSAGE = 'atch_bt'
DONT_ATTACH_BUTTON = 'dnt_atch_bt'
ATTACH_PHOTO_TO_MESSAGE = 'atch_media'
DONT_ATTACH_PHOTOS = 'dnt_atch_media'
ATTACH_VIDEO_TO_MESSAGE = 'atch_VIDEO'
DONT_ATTACH_VIDEO = 'dnt_atch_video'
DEBIT_MONEY_FROM_REFERAL_ACCOUNT = 'debit_ref'
DO_NOT_DEBIT_MONEY_FROM_REF_ACCOUNT = 'dont_deb_ref'
ALL_CATEGORIES = 'Все'
ADD_TO_FILTER = 'fltr_add'
DEL_FROM_FILTER = 'del_from_fltr'
ADD_TIME_TO_SEND_MESSAGE = 'add_msg_timer'
DONT_ADD_TIME_FOR_MSG_SEND = 'send_msg_rn'
EDIT_STOP_WORDS_CALLBACK = 'edit_stop_word'
CHOOSE_BOT_TO_SEND_MSG_AWAY = 'chs_bot'
PAYING_BOT_IS_CHOSEN = -1

STAT_COLUMN_INDICES = {
	'new_clients' : 0,
	'payments_sum': 1,
	'payments_n': 2,
	'new_users': 3,
	'repated_payments': 4,
	'conversions_to_clients': 5
}
SERVICE_ANALYTICS_SPRSHT = '16EdgiHx5ie0kdfX5bIW_KUvahnl88qIC01YOzCSQz5c' if not TESTING else \
	'1Cgv3cp7yNXL-ns_iJVvCmW4e2LZqqDeLnpX_BOxFF7c'
STATISITCS_COLUMN_NAMES = ['Новые клиенты', 'Сумма оплат', 'Новые продажи', 'Новые подписчики', 'Повторные покупки',
	'Конверсия в клиента', 'Активаций бота', 'Активаций пробного периода'
]
STATISTICS_GOOGLE_SHEETS_FIELDS = (NEW_CLIENTS, TOTAL_PAYMENT_SUM, PAYMENT_NUMBER, NEW_USERS, REPEATED_PAYMENTS, 
    CONVERSIONS_TO_CLIENT, BOT_ACTIVATES, TRIAL_ACTIVATIONS, 
)
ANALYTICS_INDICES_N = len(STATISITCS_COLUMN_NAMES)
analytics_indices = tuple(range(ANALYTICS_INDICES_N))
STAT_COLUMN_INDICES_NUM = len(STATISITCS_COLUMN_NAMES)	
CONVERSIONS_COLUMNS = ['Конверсия из активации в пробный период', 'Конверсия из активации в продажу', 
	'Конверсии из пробного периода в продажу']
range_of_conversions_columns = 'X1:Z2'
column_indices_of_conversions_columns = (ord('X')-ord('A'), ord('Z')-ord('A'))
GOOGLE_SPRSHT_ID = '1CwkgFC8YyTxdtcj_ika_mpbnvZHjZuVOtQ_hOffX4F4' \
	if not TESTING else '1Cgv3cp7yNXL-ns_iJVvCmW4e2LZqqDeLnpX_BOxFF7c'
SRVS_STAT_SHEET_ID = 1498250871 if not TESTING else 590607195
SRVS_STAT_SHEET_NAME = 'Лог по дням' 
CREDENTIAL_FILES = 'AdminBot/gsh_keys.json'
GOOGLE_SHEETS_API_URL = 'https://www.googleapis.com/auth/spreadsheets'
GOOGLE_DRIVE_API_URL = 'https://www.googleapis.com/auth/drive'
PAYMENTS_HISTORY_SPREADSHEET_ID = '1-ydHHJkZiQ6TWyJS5OKq5PJ9Gf5JIEsq8PBQEkq-RCo' \
	if not TESTING else '1Cgv3cp7yNXL-ns_iJVvCmW4e2LZqqDeLnpX_BOxFF7c'
ANALYTICS_SPREAD_SHEET_ID = '16EdgiHx5ie0kdfX5bIW_KUvahnl88qIC01YOzCSQz5c' if not TESTING else \
	'1Cgv3cp7yNXL-ns_iJVvCmW4e2LZqqDeLnpX_BOxFF7c'
REFERAL_STATS_SHEET_ID = '1ZWtzYdang7r-AKavOwJ8oHc_MoY3OJ2uCc7XlKwAcZ4'
PAYMENTS_HISTORY_SHEET_ID = 0
PAYMENTS_HISTORY_SHEET_NAME = 'Оплаты'
MONTHS_INCOMES_SHEET_NAME = 'Прибыль мес'
NEW_MESSAGES_NUMBER_TABLE = 'Новые сообщения'
MESSAGES_NUMBER_PER_EACH_HOUR_TABLE = 'Стат по часам (new)'
FUNNEL_STAT_TABLE = 'Воронка'
REFERAL_STAT_TABLE = 'Реферальная статистика'
ACTIVE_USERS_TABLE = 'Активные пользователи'
ACTIVE_USERS_SHEET_ID = 229298595 if not TESTING else 1711368172
#launching dates of old clients, that launched bot before it was added the funnel
FAKE_LAUNCHING_DATES = (datetime(2022, 3, 28, 22, 20, 56), datetime(2022, 1, 1, 0, 0, 0,))
CLIENTS_SHEETS_NAME = 'Клиенты'
REFERAL_PAYMENTS_HISTORY_TABLE_NAME = 'Расходы'
EXTERNAL_CHATS_TABLE_NAME = 'Чаты'
PAYMENT_FORECAST_TABLE = 'График оплат(new)'
REFERAL_PAYMENTS_HISTORY_TABLE_ID = 891425320 if not TESTING else 16370380
SPECIAL_CHAT_ID = -1001646856955 # chat with targetologs where bot does not send messages if he is not required to do
PATH_TO_BLAKLIST_OF_INSIDE_BOT = '../message_handler_bot/{}/blacklist.csv'
PERIOD_FOR_CALCULATING_AVERAGE_MESSAGE_NUMBER = 30
METRICS_TABLE = 'Пользователи'
month_names = {
	1: 'Январь', 
	2: 'Февраль', 
	3: 'Март', 
	4: 'Апрель', 
	5: 'Май', 
	6: 'Июнь', 
 	7: 'Июль', 
	8: 'Август',
	9: 'Сентябрь',
	10: 'Октябрь',
	11: 'Ноябрь',
	12: 'Декабрь'
}
CHANGE_REFERAL_CONDITIONS = 'Изменить реферальные условия'
CHANGE_CHANNEL_OF_TRIAL_PERIOD = 'Изменить канал для пробного'
CUSTOMZE_REF_CONDITION = 'change_ref'
CHANGE_PERCENT1 = ('Начальный %', f'{CUSTOMZE_REF_CONDITION};percent1')
CHANGE_PERCENT2 = ('Увеличенный %', f'{CUSTOMZE_REF_CONDITION};percent2')
CHANGE_REQUIRED_MIN_NUM_OF_REFERALS_TO_GET_BIGGER_PERCENT = ('Количество активных рефералов', 
	f'{CUSTOMZE_REF_CONDITION};required_referal_number')
