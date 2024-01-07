from datetime import date
from decimal import Decimal

TESTING = True  # if it is turned on bot will work via test token, use test mysql database and test data

# mysql
# database and table names
CLIENTS_DATABASE_NAME = 'service_bot' if not TESTING else 'service_bot_test'
TRIAL_PERIOD_INFO_TABLE = 'trial_period_info'
CLIENTS_SUBSCRIBES = 'clients_subscribes' 
ACTIVATED_BOT_TABLE = 'activated_bot'
SENDED_MESSAGES = 'sended_messages'
TRIAL_PERIOD_INFO_TABLE = 'trial_periods'
USERS_TABLE_NAME = 'all_users'
AWARED_CLIENTS = 'awared_clients'
PAYING_BOT_ID = 0
SENDER_BOT_ID = 1
#   host and user data
HOST = '45.86.182.198'
USER = 'admin'
PASSWORD =  'zmtoslgh'
#    table columns names
ID_COL = 'id'
LAUNCHING_DATE = 'launching_date'
IS_OFFERED_TRIAL = 'is_offered_trial'
DATE_OF_RECIEVEING_MESSAGES = 'date_of_recieveing_messages'
IS_ACTIVE = 'is_active' # not blocked bot
INDEX_OF_WRITTEN_REVIEW = 'index_of_written_review'
WROTE_REVIEW_IN_THE_END_OF_TRIAL = 1
WROTE_REVIEW_IN_THE_MIDDLE_OF_PAID_SUBSCRIBE = 2
WROTE_REVIEW_IN_THE_END_OF_PAID_SUBSCIRBE = 3
ORIGIN = 'origin' # where did a client get url to bot from
DATE_OF_PAYMENT_TRYING = 'time_of_last_trying_to_buy'
IS_ASKED_TO_CONTINUE_PAYMENT = 'is_said_that_didnt_buy'
LAST_PAYMENT = 'last_payment' 
PAYMENT_PERIOD_END = 'payment_period_end'
CATEGORY = 'category'
TRIAL_START =  'trial_start'
TRIAL_PERIOD_END = 'trial_end'
WAS_OFFERED_SALE = 'was_offered_sale'
SALE_OFFERING_DATE = 'offering_date'
USED_SALE = 'used_sale'
IS_AWARE_ABOUT_REFERAL = 'is_aware_about_ref_system'
IS_ASKED = 'is_asked_why_didnt_buy'
RELATIVE_MSG_ID = 'relative_message_id'
INSIDE_BOT_MSG_ID = 'inside_bot_msg_id'
RECIEVER_ID = 'reciever_id' # id of the client that has recieved the message
SENDED_MSG_ID = 'id_of_message_sended_to_user'
BOT_ID = 'bot_id'
PAYMENT_ENDING_WARNING_STATUS = 'warning_status'
IS_PAID = 'is_paid'
CLIENTS_PAUSES = 'pauses'
CATEGORY = 'category'
MAX_PAUSE_DAYS = 'max_days'
PAUSE_DAYS_USED = 'days_used'
UNPAUSE_DATE = 'unpause_date'
CLIENT_ID = 'client_id'
MSG_ID_WITH_SALE_AFTER_TRIAL_END = 'message_with_sale_if_didnt_buy'
EXTERNAL_CHATS = 'external_chats'
CHAT_URL = 'url'
WHAT_AWARED_ABOUT = 'what_awared_about'
#   clients values in database
NOT_WARNED = 0
WARNED_ONCE = 1
WARNED_TWICE = 2
OFFERED_TO_PAY_AFTER_TWO_DAYS_OF_PAID_SUB_END = 3 # also warning status
IS_ASKED_WHY_DIDNT_PAY = 4
UNSUBSCRIBED = WARNED_TWICE
#   category ids
TARGET_MODE = 0
SMM_MODE = 1
COPYRIGHT_MODE = 2
SITES_MODE = 3
CHAT_BOTS_MODE = 4
SEO_MODE = 5
DESIGN_MODE = 6
CONTEXT_MODE = 7
PRODUSER_MODE = 8
MARKETING_MODE = 9
AVITOLOG_MODE = 10
JURISPRUDENCE_MODE = 11
PSYCHOLOGY_MODE = 12
SURGERY_MODE = 13
INTERIOR_MODE = 14
TUTOR_MODE = 15
TUTOR_ENGLISH_MODE = 1501
ASSISTANT_MODE = 16
MARKETPLACES_MODE = 17
BOTS_MODE = 18
SALES_MODE = 19
INVESTMENTS_MODE = 20
ACCOUNTANT_MODE = 21    
NUTRITION_MODE = 22    
MARKING_MODE = 23    
CARGO_MODE = 24    
FULLFILLMENT_MODE = 25    
ANALYTICS_MODE = 26    
BEAUTYDUBAI_MODE = 27    
METODOLOGY_MODE = 28
CROPS_MODE = 29
CRYPTO_MODE = 30
CERTIFICATION_MODE = 31
ENGINEER_MODE = 32
COUCH_MODE = 33
MANAGER_MODE = 34
PHOTOGRAPHER_MODE = 35
PROPERTY_MODE = 36
SUGARING_DEPILATION_MODE = 37
ANIMATOR_MODE = 38
TRANSPORTATION_MODE = 39
GERMAN_MODE = 40
DENT_MODE = 41
REVIEWS_MODE = 42
VIDEOGRAPH_DUBAI_MODE = 43
HRIT_MODE = 44
PR_MODE = 45
VOCALS_MODE = 46
TAILORING_MODE = 47
TRANSLATE_MODE = 48
CUSTOMS_MODE = 49
FURNITURE_MODE = 50
MUSIC_MODE = 51
TECH_FIXING_MODE = 52
GEN_WROKERS_MODE = 53
HR_MODE = 54
CLEANNING_MODE = 55
BUSINESS_SALE_MODE = 56
REELSMAKER_MODE = 57

# datas for categories
message_categories = (
    TARGET_MODE, SMM_MODE, SITES_MODE, SEO_MODE, DESIGN_MODE, 
    CONTEXT_MODE, PRODUSER_MODE, AVITOLOG_MODE, JURISPRUDENCE_MODE,
    PSYCHOLOGY_MODE, INTERIOR_MODE, CHAT_BOTS_MODE, COPYRIGHT_MODE,
    ASSISTANT_MODE, MARKETPLACES_MODE, TUTOR_MODE, SALES_MODE, 
    ACCOUNTANT_MODE, CARGO_MODE, FULLFILLMENT_MODE, ANALYTICS_MODE, 
    BEAUTYDUBAI_MODE, METODOLOGY_MODE, CROPS_MODE, CERTIFICATION_MODE, 
    ENGINEER_MODE, COUCH_MODE, MANAGER_MODE, PHOTOGRAPHER_MODE, 
    PROPERTY_MODE, ANIMATOR_MODE, TRANSPORTATION_MODE, GERMAN_MODE,
    DENT_MODE, REVIEWS_MODE, VIDEOGRAPH_DUBAI_MODE, HRIT_MODE,
    PR_MODE, VOCALS_MODE, TAILORING_MODE, TRANSLATE_MODE, CUSTOMS_MODE,
    FURNITURE_MODE, MUSIC_MODE, TECH_FIXING_MODE, CLEANNING_MODE,
)
message_category_names = {
    TARGET_MODE: 'Таргет',
    SMM_MODE: 'SMM',
    COPYRIGHT_MODE: 'Копирайтинг',
    SITES_MODE: 'Сайты',
    CHAT_BOTS_MODE: 'Чат боты',
    SEO_MODE: 'SEO',
    DESIGN_MODE: 'Дизайн',
    CONTEXT_MODE: 'Контекст',
    PRODUSER_MODE: 'Продюсер',
    MARKETING_MODE: 'Маркетинг',
    AVITOLOG_MODE: 'Авитолог',
    JURISPRUDENCE_MODE: 'Юриспруденция',
    PSYCHOLOGY_MODE: 'Психология',
    SURGERY_MODE: 'Хирургия',
    INTERIOR_MODE: 'Дизайн интерьера',
    TUTOR_ENGLISH_MODE: 'Репетитор английского',
    ASSISTANT_MODE: 'Ассистент',
    MARKETPLACES_MODE: 'Менеджер маркетплейсов',
    BOTS_MODE: 'Боты',
    TUTOR_MODE: 'Репетитор',
    SALES_MODE: 'Продажи',
    INVESTMENTS_MODE: 'Инвестиции',
    ACCOUNTANT_MODE: 'Бухгалтерия',
    NUTRITION_MODE: 'Нутрициолог',
    MARKING_MODE: 'Маркировка',
    CARGO_MODE: 'Карго',
    FULLFILLMENT_MODE: 'Фулфилмент',
    ANALYTICS_MODE: 'Аналитика',
    BEAUTYDUBAI_MODE: 'Бьюти Дубай',
    METODOLOGY_MODE: 'Методолог',
    CROPS_MODE: 'Посевы',
    CRYPTO_MODE: 'Крипта',
    CERTIFICATION_MODE: 'Сертификация',
    ENGINEER_MODE: 'Инженер', 
    COUCH_MODE: 'Коуч',
    MANAGER_MODE: 'Менеджер',
    PHOTOGRAPHER_MODE: 'Фотограф',
    PROPERTY_MODE: 'Недвижимость',
    SUGARING_DEPILATION_MODE: 'Шугаринг Депиляция РФ',
    ANIMATOR_MODE: 'Аниматор',
    TRANSPORTATION_MODE: 'Перевозки',
    GERMAN_MODE: 'Немецкий',
    DENT_MODE: 'Стоматология',
    REVIEWS_MODE: 'Отзывы',
    VIDEOGRAPH_DUBAI_MODE: 'Видеограф Дубай',
    HRIT_MODE: 'HRiT',
    PR_MODE: 'Пиар',
    VOCALS_MODE: 'Вокал',
    TAILORING_MODE: 'Пошивка одежды',
    TRANSLATE_MODE: 'Переводчик',
    CUSTOMS_MODE: 'Таможня', 
    FURNITURE_MODE: 'Мебель', 
    MUSIC_MODE: 'Музыка',
    TECH_FIXING_MODE: 'Ремонт техники',
    GEN_WROKERS_MODE: 'Разнорабочие', 
    HR_MODE: 'HR', 
    CLEANNING_MODE: 'Клининг',
    BUSINESS_SALE_MODE: 'Продажа бизнеса',
    REELSMAKER_MODE: 'Рилсмейкер'
}
msg_categories = {
    TARGET_MODE: 'target',
    SMM_MODE: 'smm',
    COPYRIGHT_MODE:'copyright',
    SITES_MODE: 'sites',
    CHAT_BOTS_MODE: 'chatbots',
    SEO_MODE: 'seo',
    DESIGN_MODE: 'design',
    CONTEXT_MODE: 'context',
    PRODUSER_MODE: 'producer',
    MARKETING_MODE: 'marketing',
    AVITOLOG_MODE: 'avitolog',
    JURISPRUDENCE_MODE: 'jurisprudence',
    PSYCHOLOGY_MODE: 'psychology',
    SURGERY_MODE: 'surgery',
    INTERIOR_MODE: 'interior',
    TUTOR_MODE: 'tutor',
    TUTOR_ENGLISH_MODE: 'tutor_english',
    ASSISTANT_MODE: 'assistant',
    MARKETPLACES_MODE: 'marketplaces',
    BOTS_MODE: 'bots',
    SALES_MODE: 'sales',
    INVESTMENTS_MODE: 'investments',
    ACCOUNTANT_MODE: 'accountant',
    NUTRITION_MODE: 'nutrition',
    MARKING_MODE: 'marking',
    CARGO_MODE: 'cargo',
    FULLFILLMENT_MODE: 'fullfillment',
    ANALYTICS_MODE: 'analytics',
    BEAUTYDUBAI_MODE: 'beautydubai',
    METODOLOGY_MODE: 'metodology',
    CROPS_MODE: 'crops',
    CRYPTO_MODE: 'crypto',
    CERTIFICATION_MODE: 'certification',
    ENGINEER_MODE: 'engineer', 
    COUCH_MODE: 'couch',
    MANAGER_MODE: 'manager',
    PHOTOGRAPHER_MODE: 'photographer',
    PROPERTY_MODE: 'property',
    SUGARING_DEPILATION_MODE: 'sugaring_depilation',
    ANIMATOR_MODE: 'animator',
    TRANSPORTATION_MODE: 'transportation',
    GERMAN_MODE: 'german',
    DENT_MODE: 'dent',
    REVIEWS_MODE: 'reviews',
    VIDEOGRAPH_DUBAI_MODE: 'videograph_dubai',
    HRIT_MODE: 'hrit',
    PR_MODE: 'pr',
    VOCALS_MODE: 'vocals',
    TAILORING_MODE: 'tailoring',
    TRANSLATE_MODE: 'translate',
    CUSTOMS_MODE: 'customs', 
    FURNITURE_MODE: 'furniture', 
    MUSIC_MODE: 'music',
    TECH_FIXING_MODE: 'tech_fixing',
    GEN_WROKERS_MODE: 'gen_worker', 
    HR_MODE: 'hr', 
    CLEANNING_MODE: 'cleanning',
    BUSINESS_SALE_MODE: 'business_sale',
    REELSMAKER_MODE: 'reelsmaker'
}

# ids of clients who send messages to this bot via telethon
TARGET_CLIENT_ID = 5097101810 if not TESTING  else 1026133582
SMM_CLIENT_ID = 1568499464
TELEGRAM_CLIENT_IDS = {
    TARGET_MODE: TARGET_CLIENT_ID,
    SMM_MODE: SMM_CLIENT_ID,
    COPYRIGHT_MODE: TARGET_CLIENT_ID,
    SITES_MODE: 5045668734,
    CHAT_BOTS_MODE: 5024963244,
    SEO_MODE: 5077148928,
    DESIGN_MODE: 5035325356,
    CONTEXT_MODE: 5003533746,
    PRODUSER_MODE: 5060636645,
    MARKETING_MODE: None,
    AVITOLOG_MODE: 5098521396,
    JURISPRUDENCE_MODE: 5045434356,
    PSYCHOLOGY_MODE: None,
    SURGERY_MODE: None,
    TUTOR_ENGLISH_MODE: None,
    ASSISTANT_MODE: 6227362369,
    MARKETPLACES_MODE: None
}
#messages directories
NEW_MESSAGES_PATH = 'msgs/new messages/' if not TESTING else 'msgs/temp new messages/'
TEMP_MESSAGES_PATH = './temp new messages/'
SENDED_DIR = 'msgs/sended/'
FORWARD_INFO = 'msgs/to forward.txt' 
TEXT_INFO = 'text.txt'
MESSAGE_DIR_TIME_FORMAT = '%m_%d_%H_%M_%S_%f'

FIRST_SERVICE_ANALYTICS_DATE = date(2022, 3, 4)

BOT_DATA_FILE = 'bot_data.json' if not TESTING else 'tests/bot_data.json'
URL_WITH_REVIEWS = 'https://vk.com/topic-210255350_48577580'

MESSAGE_NUMBER_LEVEL_CHECKING_FOR_EACH_CATEGORY_DELAY = 1 # hours
PERIOD_OF_NOTIFYING_ABOUT_LOW_NUMBER_OF_MESSAGES = 3 # hour
MIN_ALLOWED_PERCENT_OF_MSGS_NUM_DEVIATION = 0.5
PAING_BOT_NAME = 'golubin_bot' if not TESTING  else "golubin_test_bot"

YOOMONEY_TRANSFER_CAP = Decimal(15000)
