from config import *
from decimal import Decimal

# webhook
PAYING_BOT_WEBHOOK_URL = 'https://vm-ce351742.na4u.ru'
WEBAPP_HOST = '127.0.0.1'
WEBAPP_PORT = 5000
# bot constants
PAYING_BOT_TOKEN = '5023421808:AAHvhN8e4lxPI_npm4kxVpLb5u078-x4maY' if not TESTING else \
    '5074243256:AAF_PYSJC9CE4QwloDdJYxbyzF8eDJQjTL8'
COURSE_PRICE = Decimal(2500)
# admin data
EUGENIY_ID = 191004724
DEVELOPER_ID = 1026133582
USERS_THAT_ALLOWED_TO_DELETE_MESSAGES = (EUGENIY_ID, 476806184, 454528448, 829894707, 5035325356, 1787839420,
    1236978331, 5091768057, 486877869, 1617121573) if not TESTING else (DEVELOPER_ID,)
EUGENIY_NICK = 'COJ_ZhIV'
# bot keyboards
CHOOSE_CATEGORY_MESSAGE = 'Выберите категорию:'
PROCESS_NEWBIE = 'prc_nwb'
TEXT_TO_GET_LAST_MESSAGES_OR_TEST_PERIOD = 'Чтобы получить заявки за прошедшие '\
    'сутки для ознакомления нажми на '\
    'соответствующую кнопку.\n\n'\
    'А чтобы получать новые заявки в режиме '\
    'реального времени выберите тариф '
NEW_ORDER = '🤑 Категории заявок'
NEW_ORDER_FOR_NEWBIE = 'Категория заявок'
NEW_ORDER_BUTTON = 'категория заявок'
ACTIVATE_TRIAL = 'act_tr'
STOP_WORDS = '⛔️ Стоп слова ⛔️' 
STOP_WORDS_CALLBACK = 'stop words'
SHOW_STOP_WORDS = 'show stop words'
ADD_STOP_WORDS = 'add stop words'
CLEAR_STOP_WORDS = 'clear stop words'
DELETE_STOP_WORDS = 'delete stop words'
INVITE_ACCOUNT_TO_EXTERNAL_CHAT = 'invite_acc_ex_ch'
SEND_LINK_TO_EXTERNAL_CHAT = 'send_ln_ex_ch'
REPORT_ERROR = '⚙️ Техподдержка'
REPORT_ERROR_BUTTON = 'report'
PERSONAL_CABINET = '👤 Личный кабинет'
ADDITIONAL_OPTIONS = '➕Доп услуги'
MAIN_MENU = 'В главное меню'
DESCIPTIONS_ABOUT_REPORT = [
    'сообщил о новой ошибке:', 'не оплатил подписку из-за тех. проблемы:', 'не оплатил подписку из-за:'
]
ENROLL_IN_COURSE = 'enroll_client_in_course'
USE_PROMOCODE_BUTTON = 'ent_prm'
SUBSRIBES_BUTTON = '✅ Мои подписки'
SUBSCRIBES_CALLBACK = 'sbscrbs'
TAB_HELPFUL_BUTTON = '⭐️ Полезное'
TAB_HELPFUL_BUTTON_FOR_NEWBIE = 'Полезное'
TAB_HELPFUL_CALLBACK = 'helpful_tabs'
GET_LAST_MSGS_PER_DAY = 'gt_lst_msgs_per_d'
GET_CATEGORY_FOR_FILTER = 'gt_ct_to_fltr'
GET_CATEGORY_OF_POST = 'gt_ct_of_pst'
BACK_BUTTON_TEXT = '⬅️ Назад'
ADD_EXTERNAL_CHAT = '➕ Добавить чат'
ADD_EXTERNAL_CHAT_CALLBACK = 'add_ex_ch'
MAIN_MENU_TEXT = '''
«🤑<b>Категории заявок</b>» - выбор
категории по которой будут приходить
заявки, можешь выбрать нужную
категорию и попробовать ее в деле
запросив заявки за прошедшие сутки

«⭐️ <b>Полезное</b>» - много полезных статей
по использованию бота

«⚙️ <b>Техподдержка</b>» - можно задать
любой вопрос по работе бота

«🤝 <b>Партнерская витрина</b>» - Различные бонусы для клиентов бота от наших партнеров

«👤 <b>Личный кабинет</b>» - подписки, стоп слова, реф система, аккаунты и многое другое

«➕ <b>Доп услуги</b>» - размещение объявлений, добавление чатов для перессылки, заказ нового направления 
'''
MAIN_MENU_FOR_NEWBIES_TEXT = f'''
Привет! Ты активировал Golubin bot. Бот
ежедневно присылает более 100 заявок на
услуги фриланса.

📌 «Категории заявок>» - выбор
категории по которой будут приходить
заявки, можешь выбрать нужную
категорию и попробовать ее в деле

📌 «Реферальная система» - дает твою
личную реферальную ссылку. Отправь ее
друзьям для регистрации и с каждой
оплаты будешь получать до 50% на свой
счет. Эти деньги можно вывести или
оплатить категорию заявок

📌 «Полезное» - много полезных статей
по использованию бота.

📌 «Разместить объявление» -
разместить объявление в боте о поиске
специалиста

📌 «Техподдержка» - можно задать
любой вопрос по работе бота.

📌 "Заказать направление" - если
вашего направления нет в "Категории заявок", 
то можете заказать его разработку
'''
PERSONAL_CABINET_TEXT = '''
«✅<b> Мои подписки</b>» -  список твоих активных подписок, приостановка или перенос подписки

«⛔️<b> Стоп слова </b>⛔️» - добавление слов по которым не будут пересылаться сообщения

«💵 <b>Реферальная система</b>» - условия и реф ссылка

«👥 <b>Аккаунты</b>» - добавление до 3-х аккаунтов в каждом направлении*

«📊 <b>Статистика</b>» - скольким людям написал с каждого аккаунта*

«📋 <b>Гугл таблицы</b>» - выгрузка статистики в гугл таблицу*

*Доступно только при годовой подписке
'''
ADDITIONAL_OPTIONS_TEXT = '''
«⬆️ <b>Разместить объявление</b>» - разместить
объявление в боте о поиске специалиста

«➕ <b>Добавить чат</b>» - добавление в бота чата для дальнейших пересылок сообщений из него.

«📝 <b>Заказать направление</b>» - если вашего направления нет в "Категории заявок", то можете заказать его разработку
'''
CALLBACK_SEP = ';'
CHOOSE_CATEGORY = 'choose_category'
CHOOSE_PERIOD_PREFIX = 'chp'
SELECT_MAIN_KB = '$'
SELECT_PER_CHOOSE_KB = '<-'
PAY_FOR_PERIOD_PREFFIX = 'p'
TRIAL_PERIOD = 'trial'
WITH_SALE = 's-'
GET_ANSWER_WHY_DIDNT_BUY = 'get_answer_why_didnt_buy'
KEYBOARD_WITH_ANSWERS = 'get_kb_with_answers_why_didnt_by'
ANSWERS_WHY_DIDNT_BUY = {
    'Не нашел клиентов' : 
'''Не отчаивайся! За тестовый период
сложно найти клиента, тем более, если
делаешь это в первый раз.

Многим кому ты уже написал будут
отвечать еще в течение 6 месяцев и это
серьезно. Мне в июне пишут клиенты
которым я писал в январе, поэтому время
которое ты уделил сейчас оно не
потрачено в пустую.

Я сам продаю через этого бота и делаю в
среднем по 10 продаж в месяц со средним
чеком 25 000 руб.

Предлагаю консультацию на которой мы с
тобой разберем все диалоги и ошибки в
них за тестовый период. Ты поймешь как
продавать эффективней и закрывать на
большие чеки.
Записывайся!''',
    'Многим писал, но ответа не было' : 
'''Не отчаивайся! Продажи в Telegram
имеют свою специфику. Я сам продаю
через бота и делаю в среднем по 10
продаж в месяц со средним чеком 25 000
руб.

Конкуренция тут большая, если написать: "
Ищу таргетолога", то сразу же напишет
человек 100. Поэтому тут важно несколько
факторов:
1) Оперативность, обрабатывать заявки
сразу как они пришли
2) Оформление профиля. Должна стоять
твоя фотография, чтобы было хорошо
видно лицо, а также имя.
3) Приветствие - короткое и
информативное. По какому вопросу, опыт,
кейсы.

Не ответили сегодня - напиши завтра,
сообщение могло улететь
вниз.

Даже если после всего этого тебе не
ответили, эту заявку архивируем и
работаем с другими. В моем боте более
100 заявок ежедневно в каждой тематике,
а по этой заявке могут ответить и через
пол года, так что работа была проделана не
зря.

Важна система, если каждый день
обрабатывать заявки и писать новым
людям, то одну продаж за месяц точно
можно сделать даже не умея продавать, а
это значит, что бот 100% окупится.

Оформляй подписку и забирай заказы!''',

    'Нет интересных предложений': 
'''Понимаю тебя, может показаться, что в
Telegram чатах сидят одни халявщики и
новички, но это не так. Я это знаю по
своему опыту. Сам продаю через своего
бота и я находил заявки от таких
компаний как: Синергия, IKEA, Total,
Маричева, Юниты и даже зарубежных,
русскоговорящих заказчиков.

(Оформляй подписку и возможно найдешь
еще более крупных клиентов)''',
    'Технические проблемы' : 
'''Очень жаль, что вы столкнулись с
техническими проблемами. Напишите,
пожалуйста, конкретно с какими
столкнулись вы.

Мы постоянно усовершенствуем бота и
добавляем новый функционал, к
сожалению, от багов никто не застрахован.''',
    'Много спама' : 
'''Мы постоянно усовершенствуем бота,
чтобы он присылал меньше спама, но тут
нужно быть осторожным, чтобы не
потерять целевые заявки.

Я сам продаю через бота и в день пишу
порядка 30 заказчикам. За счет этого я
получаю порядка 10 продаж в месяц со
средним чеком 25 000 руб.

Оформляй подписку и получай заказы!''',
    'Другое' : 
'''Напиши свой вариант:'''
}
text_about_subscribe_pauses = '''
Останавливать подписку можно только на платных тарифах.
Паузы можно использовать несколько раз, но их общая сумма не дожна превышать:
    1 неделя — 3 дня паузы
    2 недели — 5 дней паузы
    3 недели — 10 дней паузы
    1 месяц — 14 дней паузы
    3 месяца - 40 дня паузы
    6 месяцев - 80 дня паузы
    12 месяцев - 150 дней паузы
''' 
ANSWER_WITH_ENROLL_IN_COURSE = list(ANSWERS_WHY_DIDNT_BUY.keys()).index('Не нашел клиентов')
ANSWER_WITH_GET_REPORT = list(ANSWERS_WHY_DIDNT_BUY.keys()).index('Технические проблемы')
ANSWER_WITH_GET_MESSAGE_TO_DEVELOPER = list(ANSWERS_WHY_DIDNT_BUY.keys()).index('Другое')
CHOOSE_CONSULTATION_TIME = 'chs_cnslt_t'
MORNING = 'm'
HIGH_NOON = 'hn'
EVENING = 'e'
WROTE_REVIEW = 'wrote_review'
SEND_BONUS_DAYS_FOR_REVIEW = 'send_bonus_for_review'
MARK_REVIEW_AS_FAKE = 'fake_rvw'
consultation_time = {
    MORNING: 'утро',
    HIGH_NOON: 'обед',
    EVENING: 'вечер'
}
NOTFIY_ABOUT_NEW_COURSE = 'N'
SURCHARGE = 'surcharge'
EXPAND_PERIOD = 'expndp'
CHOOSE_SUB_CAT_TO_PAUSE = 'chs_sub_to_ps'
PAUSE_PERIOD = 'pause_period'
TRANSFER_ACCOUNT = 'transfer_sub'
SEND_TRANSFER_CONFIRMATION = 'send_transfer_cnfm'
CONFIRM_TRANSFER_SUB = 'confirm_transfer'
POST_APPLICATION = '⬆️ Разместить объявление' 
POST_APPLICATION_FOR_NEWBIE = 'Разместить объявление'
BUY_NEW_CATEGORY = '📝Заказать направление'
ADS = 'Реклама в боте 💸'
ACCOUNTS_BUTTON = '👥 Аккаунты'
PARTNER_SHOWCASE = '🤝Партнерская витрина'
POST_APPLICATION_CALLBACK = 'post_app'
CONFIRM_CHECK_APPLICATION = 'confirm_check_app'
DENY_CHECK_APPLICATION = 'deny_check_app'
ALLOW_APPLICATION = 'allow_app'
DECLINE_APPLICATION = 'decline_app'
GET_INFO_ABOUT_BOT_FOR_NEWBIE = 'get_bot_about'
GET_PROMOCODE_SALE_PERIOD = 'gt_prm_s_p'
GET_INFO_WHETHER_SALE_PROMOCODE_IS_ENDLESS = 'pcd_is_endless'
REPLY_TO_USER = 'rpl_to_user' # after report
REPLY_TO_ADMIN = 'rpl_to_admin'
BOT_INFO = 'get_bot_info'
NEW_ORDER_WITHOUT_PROMOCODE = 'new_order_without_promocode'
ATTACH_COMMENT_ABOUT_APP_REFUSAL = 'add_cmnt_rfsl'
GET_BACK_TO_CHOOSING_COMMENT_ABOUT_REFUSAL = 'bck_to_cmnt_attch'
CONFIRM_SENDING_COMMENT_ABOUT_REFUSAL = 'yes_snd_rfsl_cmnt'
DECLINE_SENDING_COMMENT_ABOUT_REFUSAL = 'no_dnt_snd_rfsl_cmnt'
PAY_USING_REFERAL_BALANCE = 'prfb'

CHOOSE_PERIOD_TEXT = 'Выберите категорию:'
TEXT_AFTER_FIRST_PAYMENT = 'Важно ❗\n\nАктивируйте этого бота @{0},'\
    ' если вы ещё не сделали это\n\nВ него будут поступать заявки, иначе вы их не увидите!'
PAYMENT_END_DATE_FORMAT = "%d.%m.%Y в %H:%M"
TEXT_AFTER_CATEGORY_CHOOSE = f'''
При оплате из других стран (не РФ) или через криптовалюту пишите на аккаунт @{EUGENIY_NICK}

<b>При оплате годового тарифа консультация по продажам с создателем бота - в подарок.</b>

Выберите период:
'''
APPLICATIONS_FROM_USERS_DIR = './new messages/from_clients' if not TESTING else './temp new messages/from_clients'
TEXT_ABOUT_BOT = '''Бот парсит чаты по ключевым словам и переслывает сообщения от потенциальных клиентов. 
Пример: "Ищу таргетолога", "ищу дизайнера" и др. Все что вам остается - это написать человеку на его запрос.

Заявки берутся из открытых источников, чаты, каналы, а также сторонние сайты.

В боте есть 11 направлений. По кнопке "Категории заявок" вы можете выбрать нужную категорию. 

Подбирать свои ключевые слова пока нельзя. Выбирать можно только из готовых категорий.'''
TEXT_AFTER_RFUSAL_OF_CLIENTS_APPLICATION = 'Заявка удалена. Выберите причину отказа: '
comments_about_refusal = [
    'Объявление о рекламе специалиста. В боте публикуются объявления только по поиску специалистов',
    'Не подходит к категории. Переопубликуйте с другой категорией',
    'Другое (свой вариант)'
]
# periods
ONE_WEEK = '7'
TWO_WEEKS = '14'
THREE_WEEKS = '21'
ONE_MONTH = '30'
THREE_MONTHS = '90'
SIX_MONTHS = '180'
ONE_YEAR = '365'
all_possible_periods = (ONE_WEEK, TWO_WEEKS, THREE_WEEKS, ONE_MONTH, THREE_MONTHS, SIX_MONTHS, ONE_YEAR)
payment_period_costs = { # rub
    ONE_YEAR : Decimal('20990'),
    SIX_MONTHS : Decimal('11190'),
    THREE_MONTHS : Decimal('5980'),
    ONE_MONTH : Decimal('2190' if not TESTING else '10'),
}
payment_for_additional_categories_costs = {
    ONE_YEAR : Decimal('10490'),
    SIX_MONTHS : Decimal('5590'),
    THREE_MONTHS : Decimal('2950'),
    ONE_MONTH : Decimal('1090' if not TESTING else '10'),
}
TRIAL_PERIOD_DAYS = 3
days_per_period = {
    ONE_MONTH : 30,
    THREE_MONTHS : 90,
    SIX_MONTHS : 180,
    ONE_YEAR : 365,
    TRIAL_PERIOD : TRIAL_PERIOD_DAYS
}
pause_periods = { # days
    ONE_MONTH : 14,
    THREE_MONTHS : 40,
    SIX_MONTHS : 80,
    ONE_YEAR : 150
}
surcharges = { # surcharges that client has to pay if he wants to get higher period during hour
    ONE_MONTH : Decimal(500),
    THREE_MONTHS : Decimal('2699'),
    SIX_MONTHS : Decimal('3199'),
    ONE_YEAR : Decimal(4350)
}

# yoomoney api
CLIENT_TOKEN =  '4100118433534009.B9B194F84B8B862B211F0A2D9CD0ED2F47F72E023B009F31D40A9D054C6971E03D25D5F8387F92803204E114F3C632A0A64CC2D403D4F1A621A62EA87A9C4584F454340CD0DE6B3F38CBFD3D6DDF3DC5390E79CF14B53FE5E8A6E1867FF6AC0FDBD899E56A62E440E097E456326598847B75CF345735DAC3DF1CD5F1B557665A'

# client working constants
DAYS_BEFORE_PAYMENT_OVER_TO_WARN = 3 # the number of days before disconnection, for which the client will be warned
DAYS_BEFORE_TRIAL_END_TO_OFFER_SALE = 1
SALE_PERIOD = 1 # day
PERIOD_TO_PAY_SUBSCRIBE_WITH_SALE = 1 
PERIOD_WITH_BONUS_DAYS_AFTER_THE_END_OF_TRIAL = ONE_MONTH
BONUS_DAYS_AT_THE_END_OF_TRIAL = 7
CATEGORIES_WITHOUT_SALES = (TARGET_MODE, CONTEXT_MODE, SMM_MODE, JURISPRUDENCE_MODE, SITES_MODE, TUTOR_MODE)
COEFICIENT_FOR_ADDITIONAL_CATEGORIES = Decimal('0.5')
#   number of days that gotta past from moment when client sended start command to main bot after which client is offered trial period
DAYS_AFTER_ACTIVATING_TO_OFFER_TRIAL = 1 
#   period during which a client can extra pay and expand his period to higher period than he has paid 
SURCHARGE_PERIOD = 3600 # seconds (one hour)
DAYS_AFTER_TRIAL_END_TO_OFFER_NEW_SALE = 1
SALE_AFTER_TRIAL = Decimal('0.5')
PERIOD_WITH_SALE_AFTER_TRIAL_END = ONE_MONTH
PERIOD_OF_SALE_AFTER_TRIAL_END = 1

# error tracebacks
CHAT_NOT_FOUND_DESCRIPTION = "A request to the Telegram API was unsuccessful. Error code: 400. Description: Bad Request: chat not found"
FORBIDDEN_BY_USER = "A request to the Telegram API was unsuccessful. Error code: 403. Description: Forbidden: bot was blocked by the user"
USER_IS_DEACTIVATED = "A request to the Telegram API was unsuccessful. Error code: 403. Description: Forbidden: user is deactivated"

LAST_HANDLED_BOTS_UPDATES = 'last_handled_bot_updates.json' if not TESTING else 'tests/last_handled_bot_updates.json'

#bot senders
BOT_SENDER_POLLING_TIMEOUT = 1
bot_tokens = {
    TARGET_MODE: '5096903131:AAHotW2Wbzon6OhGooF4q4cK4LbVvkdOFm0' if not TESTING else '5017859009:AAFlfrZGpgZFjmlPItWi6ODr_e0HVNihITA',
    SMM_MODE: '5302119349:AAFY3EKhgyAkd6CoQPTrqYWTn7wWSMR5uCA' if not TESTING else '',
    COPYRIGHT_MODE: '5371959061:AAEpPUEXTSGAMXVuFWs3rNCokUC2cr4iHpQ' if not TESTING else '',
    SITES_MODE: '5939090257:AAELmjm9E8Gzqr_ovBdKE0nEfDAA1u922rQ' if not TESTING else '',
    CHAT_BOTS_MODE: '5314134561:AAFYUFMiCi7ZJA-VkYBj8Zfb-X5B1_VjaHI' if not TESTING else '',
    SEO_MODE: '5345468905:AAE5cP_p6DoJl1BMMi1xmliL95mk7dbqGCA' if not TESTING else '',
    DESIGN_MODE: '5233479598:AAG27SLV5hA6yYe3iU1v-JAaljmOHuLdgA0' if not TESTING else '',
    CONTEXT_MODE: '5190691774:AAGYtpL7f61I_Jsh8_KLs84ReyJslNTZNno' if not TESTING else '',
    PRODUSER_MODE: '5328569451:AAFQu8KmhS47_MjFz-mcDO9n_yPjRJQ64kY' if not TESTING else '',
    #MARKETING_MODE: '5359352487:AAG_eA6wul9OSQN9cY3C5Cyd41k03OLSdBE' if not TESTING else '',
    AVITOLOG_MODE: '5285936482:AAFep2-hYpHObVLV_OCnkIagCxljAu9cLjo' if not TESTING else '',
    JURISPRUDENCE_MODE: '5433997522:AAENpja1NWkZY3ChqIHgnj4FTwbNRhk7Qtw' if not TESTING else '',
    PSYCHOLOGY_MODE: '6262966675:AAHuYSKvuZuf1TPTA6U9-NA0Feks9JX12_I' if not TESTING else '',
    SURGERY_MODE: '6126851961:AAGS54TjvwMbwQ3aIr3pbtPvfCob_XuXR7I' if not TESTING else '5165724922:AAGpFdffemYGZaDJunn5jcw-wqxmI9AFA9M',
    INTERIOR_MODE: '6182503785:AAHmssoZ_yJbtQhuQtj57YhMB1VT4--WncE' if not TESTING else '5394143236:AAGhzfpkAVCj6RXuEMFUZ6Hg3qs59wyEtOg',
    TUTOR_MODE: '6368697157:AAF7yFkaOVAsqhfFE80GVdmvOT672AF5ltU' if not TESTING else '',
    TUTOR_ENGLISH_MODE: '6096717890:AAFVof9jQO9IrpeD-bj1UDNP6h_TNxDQJL4' if not TESTING else '6096717890:AAFVof9jQO9IrpeD-bj1UDNP6h_TNxDQJL4',
    ASSISTANT_MODE: '6365924046:AAH5RCppD6XKNSuvx8xFyH6YQ1o_SK1sTI8' if not TESTING else '',
    MARKETPLACES_MODE: '6285785063:AAFgDphuAE88ZAYdtzISNuwIgEnDIRlzWc0' if not TESTING else '',
    BOTS_MODE: '6592499623:AAHM3Cak_HcQR_KwuNO5HW7HNlqml0TG-cw' if not TESTING else '',
    SALES_MODE: '6552420841:AAHYMojHMBsmuSDs5I9izMpg-rliRtBJUIQ' if not TESTING else '',
    INVESTMENTS_MODE: '6400491190:AAFMlCTnYY5dKTk_u1KsQn8uu-M0cRNQRaI' if not TESTING else '',
    ACCOUNTANT_MODE: '6546669411:AAGiFx4JrTp7DxZfzpYX8UEtGkIR6M28LNo' if not TESTING else '',
    NUTRITION_MODE: '6438000419:AAEKsPyp_W7W7lYsShZSiDWEKHa-SWfUSFc' if not TESTING else '',
    MARKING_MODE: '6401381238:AAF9qNCOngEqD8NYfgpwqsP6oZ06qUBvgh8' if not TESTING else '',
    CARGO_MODE: '6339760906:AAEbIziByIs8dFalIWXuapl7GNB9XloSk6o' if not TESTING else '',
    FULLFILLMENT_MODE: '6515209009:AAFgx0p3rq5CmbuFark4rYbI8oqmSId3zfU' if not TESTING else '',
    ANALYTICS_MODE: '6483567603:AAG6CjVjM7dUYnKf6WKL2qszRhzqQI547s8' if not TESTING else '',
    BEAUTYDUBAI_MODE: '6471148189:AAHrq0Bk7GHL66yfM_FnBOIdIjqFSHZDNcc' if not TESTING else '',
    METODOLOGY_MODE: '6099323781:AAFPTIKso030MJLWnrG8eGiFnM9R_PMJtVM' if not TESTING else '',
    CROPS_MODE: '6671170791:AAFW-l4_spKVdFlqmO7AcrtPOs9vzql0klY' if not TESTING else '',
    CRYPTO_MODE: '6664614378:AAFsISLjaggjt3RnwZ2yeq8d7MJFohbMTgI' if not TESTING else '',
    CERTIFICATION_MODE: '6368407592:AAHVOhToqOny0tGJOwFMWD_1Vo0c_kPqllk' if not TESTING else '',
    ENGINEER_MODE: '6469650695:AAGK_KBKLw_4N3a_tpq25Fp3L5JayQKDP8k' if not TESTING else '', 
    COUCH_MODE: '6484118843:AAE8fuFpGiljQp4h1KHs2o64Z1Z89iZsTpI' if not TESTING else '',
    MANAGER_MODE: '6901781390:AAEE3dkXVL4Z_eF0YRi8RzRVDW3UrSEKZrU' if not TESTING else '',
    PHOTOGRAPHER_MODE: '6854628650:AAEtC2Wut8PS0_5xpbZj2EMbyTAyOQnalbk' if not TESTING else '',
    PROPERTY_MODE: '6582621869:AAFwDJFIRHlWh79jylc5DpEkH4GH2kJQgI8' if not TESTING else '',
    SUGARING_DEPILATION_MODE: '6665765680:AAGlRQsx-eZoRcBnVb2QLVgc4mx7eNswzM8' if not TESTING else '',
    ANIMATOR_MODE: '6981435860:AAGVkWIJ4PpcyhthNg0vtHSNn2AwrV-uQqE' if not TESTING else '',
    TRANSPORTATION_MODE: '6871043011:AAHXfiCSenuMUrFYC9uyn5ODn04WnAVwGns' if not TESTING else '',
    GERMAN_MODE: '6972699690:AAEtLJ8sGQPDwoZRvQ9I3_oI_KQEyKBUiIQ' if not TESTING else '',
    DENT_MODE: '6965522067:AAFoyqs9oWwbwTlEiIb8fJ8Vkn0tv1WWPp0' if not TESTING else '',
    REVIEWS_MODE: '6951500758:AAGm2OUuO4Qd8uJm3THAwpBR17gCAGYZY8E' if not TESTING else '',
    VIDEOGRAPH_DUBAI_MODE: '6925307897:AAGuBhYzEwo3G2_U5Bc8hMhD8y7xSizR5j4' if not TESTING else '',
    HRIT_MODE: '6785487249:AAFQom2M3rsKNsPapmiWAe95yLs4aCssjlU' if not TESTING else '',
    PR_MODE: '6866862068:AAGYuQfRrhg8jkLHTH9pjBQ7FcTA4l_pFFY' if not TESTING else '',
    VOCALS_MODE: '6955720090:AAHdbd6Ef0M5eptWDXZKoSyi8O8PgBumCaI' if not TESTING else '',
    TAILORING_MODE: '6582789621:AAEJypLOe2Vhr08OniijglRhj3BBH27xkJQ' if not TESTING else '',
    TRANSLATE_MODE: '6657375465:AAE6grc_HrSxXYQa9dhRbmpCyJW3uqvqa1g' if not TESTING else '',
    CUSTOMS_MODE: '6502941955:AAH4fCFayZnVQomy2T-1v2W7LtvA6Zd0NH8' if not TESTING else '',
    FURNITURE_MODE: '6808181937:AAHvRuJJr8_lVeFd88IbnQ8MSdL0Z6VLGAw' if not TESTING else '',
    MUSIC_MODE: '6969167896:AAGua1_hXlV5b-xMbr6F4kwBK7kQr4C1viw' if not TESTING else '',
    TECH_FIXING_MODE: '6551553767:AAE5cs0O4LvJCyxstybJRJqVu8tVvcnK5LQ' if not TESTING else '',
    GEN_WROKERS_MODE: '6409080274:AAGthreEctjdfRD5EsskxEf-1Ymz-7AIz0I' if not TESTING else '',
    HR_MODE: '6807907768:AAHCbdsIMTiF7XuTG1Jvb16Xk7Gu2yj9lr8' if not TESTING else '',
    CLEANNING_MODE: '6730954087:AAHAbfH_7SWj6lV8Djr3vH-K8V3vipBfaiI' if not TESTING else '',
    BUSINESS_SALE_MODE: '6885773906:AAFlIJ4O2o1tgIAsgqlt7dgNNjD8Yxa3s7k' if not TESTING else '',
    REELSMAKER_MODE: '6958769078:AAEEQ9PsDeL2u_7l06otRM6h47y-YpxYXzM' if not TESTING else '',
    BUILDING_MODE: '6927580854:AAH_LXgGhlhHlSKCmuXR4KBytCBekeC5lpc' if not TESTING else '',
    ASTROLOGY_MODE: '6834055606:AAEYnabzPSkYYKOjModxQdh6AX3aSB4fBB4' if not TESTING else '',
    MAILER_MODE: '6690171971:AAEc5fLX4Jxlr42Sx3YMd-9xLec2sannJWE' if not TESTING else '',
    APPARTMENT_FIX_MODE: '6714109424:AAEBN5ynu-TCaZS2XU0PzYWc2qz12P0AUts' if not TESTING else '',
    DREAM_MODE: '6539575446:AAFhobpGEnWAdhPBAmw5BtOdGj-QgyCOjZY' if not TESTING else ''
}
bot_names = {
    TARGET_MODE: 'golubin_target_bot' if not TESTING else 'golubin_target_test_bot',
    SMM_MODE: 'golubin_smm_bot' if not TESTING else 'golubin_smm_test_bot',
    COPYRIGHT_MODE: 'golubin_copyright_bot' if not TESTING else 'golubin_copyright_test_bot',
    SITES_MODE: 'golubin_web_bot' if not TESTING else 'golubin_sties_test_bot',
    CHAT_BOTS_MODE: 'golubin_chat_bots_bot',
    SEO_MODE: 'golubin_seo_bot',
    DESIGN_MODE: 'golubin_design_bot',
    CONTEXT_MODE: 'golubin_context_bot',
    PRODUSER_MODE: 'golubin_producer_bot',
    MARKETING_MODE: 'golubin_marketing_bot',
    AVITOLOG_MODE: 'golubin_avitolog_bot',
    JURISPRUDENCE_MODE: 'golubin_jurisprudence_bot',
    PSYCHOLOGY_MODE: 'golubin_psychology_bot',
    SURGERY_MODE: 'golubin_surgery_bot',
    INTERIOR_MODE: 'golubin_interior_design_bot',
    TUTOR_MODE: 'golubin_tutor_bot',
    TUTOR_ENGLISH_MODE: 'golubin_tutor_english_bot',
    ASSISTANT_MODE: 'golubin_assistant_bot',
    MARKETPLACES_MODE: 'golubin_marketplaces_bot',
    BOTS_MODE: 'golubin_bots_bot',
    SALES_MODE: 'golubin_sales_bot',
    INVESTMENTS_MODE: 'golubin_investments_bot',
    ACCOUNTANT_MODE: 'golubin_accountant_bot',
    NUTRITION_MODE: 'golubin_nutrition_bot',
    MARKING_MODE: 'golubin_marking_bot',
    CARGO_MODE: 'golubin_cargo_bot',
    FULLFILLMENT_MODE: 'golubin_fullmillment_bot',
    ANALYTICS_MODE: 'golubin_analytics_bot',
    BEAUTYDUBAI_MODE: 'golubin_beautydubai_bot',
    METODOLOGY_MODE: 'golubin_metodology_bot',
    CROPS_MODE: 'golubin_crops_bot',
    CRYPTO_MODE: 'golubin_crypto_bot',
    CERTIFICATION_MODE: 'golubin_certification_bot',
    ENGINEER_MODE: 'golubin_engineer_bot', 
    COUCH_MODE: 'golubin_couch_bot',
    MANAGER_MODE: 'golubin_manager_bot',
    PHOTOGRAPHER_MODE: 'golubin_photographer_bot',
    PROPERTY_MODE: 'golubin_property_bot',
    SUGARING_DEPILATION_MODE: 'golubin_sugaring_depilation_bot',
    ANIMATOR_MODE: 'golubin_animator_bot',
    TRANSPORTATION_MODE: 'golubin_transportation_bot',
    GERMAN_MODE: 'golubin_deutch_bot',
    DENT_MODE: 'golubin_dent_bot',
    REVIEWS_MODE: 'golubin_reviews_bot',
    VIDEOGRAPH_DUBAI_MODE: 'golubin_videograph_dubai_bot',
    HRIT_MODE: 'golubin_hrit_bot',
    PR_MODE: 'golubin_pr_bot',
    VOCALS_MODE: 'golubin_vocals_bot',
    TAILORING_MODE: 'golubin_tailoring_bot',
    TRANSLATE_MODE: 'golubin_translate_bot',
    CUSTOMS_MODE: 'golubin_customs_bot',
    FURNITURE_MODE: 'golubin_furniture_bot',
    MUSIC_MODE: 'golubin_music_bot',
    TECH_FIXING_MODE: 'golubin_tech_fixing_bot',
    GEN_WROKERS_MODE: 'golubin_gen_workers_bot',
    HR_MODE: 'golubin_hr_bot',
    CLEANNING_MODE: 'golubin_cleanning_bot',
    BUSINESS_SALE_MODE: 'golubin_business_sale_bot',
    REELSMAKER_MODE: 'golubin_reelsmaker_bot',
    BUILDING_MODE: 'golubin_building_bot',
    ASTROLOGY_MODE: 'golubin_astrology_bot',
    MAILER_MODE: 'golubin_mailer_bot',
    APPARTMENT_FIX_MODE: 'golubin_apartment_fix_bot',
    DREAM_MODE: 'golubin_dream_bot'
}
MESSAGE_FILTER = 'bot_filter.json' if not TESTING else 'tests/bot_filter.json'
MIN_PERIOD_TO_GET_VOTE_BUTTONS = ONE_YEAR
TEXT_ABOUT_REFERAL_WITHDRAWAL_FOR_PAYMENT = 'руб. списаны с вашего реферального счёта в цену)'
DAYS_AFTER_PAYMENT_TO_NOTIFY_ABOUT_REFERAL = 3
SALE_TO_YEAR_SUBSCRIBE_AFTER_END_OF_PAID_SUBSCRIBE = Decimal(3000)
TEXT_AFTER_PAID_PERIOD_END = '''
Твой тариф по категории '''+'{0}'+f''' заканчивается. Вижу тебе понравился бот.
Предлагаю обеспечить себя заявками на
весь год.

А также получить приятные бонусы:

1) Запись вебинара по продажам
- Как продавать
- Как эффективней работать в боте
- Автоматизация ответов на сообщения

2) Часовая консультация по продажам со
мной. Разберем переписки и
скорректируем скрипт продаж для
увеличения конверсии в продажу

3) Возможность подключить до ''' + '{1}' + f'''
аккаунтов.
- Возможность отслеживать скольким
людям написал, для контроля менеджеров
и избежания банов
- Если один аккаунт все же заблокируют,
то не нужно будет пересылать сообщения
с одного аккаунта на другой

4) Мой скрипт продаж

5) Успешные диалоги
И если примешь решение в течение суток,
дополнительно скидка <b>{int(SALE_TO_YEAR_SUBSCRIBE_AFTER_END_OF_PAID_SUBSCRIBE)}</b> руб. Итоговая
стоимость 20990 руб актуально до ''' + '<b>{1}</b>\n\nПодключайся!'
SECOND_TEXT_AFTER_ONE_DAY_FROM_PAID_PERIOD_END = '''
Вижу, что ты не воспользовался моим
предложением. К сожалению, время
истекло.
@yourself_realize
20 000 руб, то мы получим 2 275 000 руб
выручки. А это 14 500% ROMI! Какой еще
канал даст такую окупаемость?

Каждый имеет второй шанс и я даю тебе
его. Скидка будет действовать еще в
течение суток. Не упусти эту
возможность, третьего шанса не будет!'''
PROMOCODE_ID = 'p'
REFERAL_ID = 'r'

CHANNELS_OF_CATEGORIES = {
    TARGET_MODE: -1001917355681,
    SMM_MODE: -1001934664610,
    COPYRIGHT_MODE: -1001944818545
}

SALE_FOR_UPSALE = Decimal('0.10')
MAIN_CHANNEL = '@yourself_realize'
ACTIVATE_TRIAL_WITHOUT_CATEGORY = 'trial_wo_cat'