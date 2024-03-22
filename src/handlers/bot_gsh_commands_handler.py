import logging
from aiogram.dispatcher import FSMContext
from aiogram.types import *
from src.markups.users import google_sheets_panel
from src.apis.ClientsData.GoogleSheets.daily_clients_gsh_uploading import connect_to_gsh_and_get_sheet_id
from src.apis.db.accounts import get_admin_of_account
from src.apis.db.votes import check_if_client_is_allowed_to_get_vote_buttons
from src.utils.bot_get_nick import get_nick
from src.apis.ClientsData.GoogleSheets.clients_google_sheets import *



# dp.msg_handler(lambda msg: msg.text == GOOGLE_SHEETS_BUTTON, state = '*')
handle_get_google_sheets_customing_panel = lambda dp: dp.register_message_handler(get_google_sheets_customing_panel, text=GOOGLE_SHEETS_BUTTON, state="*")
async def get_google_sheets_customing_panel(msg: Message, state: FSMContext):
    await state.finish()
    admin = get_admin_of_account(msg.from_user.id)

    if admin:
        nick = await get_nick(
            (await msg.bot.get_chat_member(admin, admin)).user
        )  # нахуя было этот пиздец делать?
        await msg.answer('Вы не можете настривать гугл таблицы, так как ваш аккаунт привязан к '
            f'{nick}')
        return

    if not check_if_client_is_allowed_to_get_vote_buttons(msg.from_user.id):
        await msg.answer(
            'Вы можете подключить гугл таблицы для выгрузки статистики отмеченных вами '
            'и вашими подключенными аккаунтами заявок. Для того, чтобы подключить свою таблицу, вам нужно оплатить'
            ' годовую подписку.'
        )
        return
    spread_sheet, sheet_id = get_google_sheet_of_client(msg.from_user.id)

    if not spread_sheet:
        await msg.answer('На данный момент у вас не подключена никакая гугл таблица', reply_markup = google_sheets_panel(False))
    else:
        await msg.answer(
            f'Ваша текущая гугл таблица: {GOOGLE_SHEET_URL_TEMPLATE.format(spread_sheet, sheet_id)}', 
            reply_markup = google_sheets_panel(True)
        )

# dp.call_query_handler(lambda call: call.data == ADD_GOOGLE_SHEET, state = '*')
handle_pludge_google_sheet = lambda dp: dp.register_callback_query_handler(pludge_google_sheet, text=ADD_GOOGLE_SHEET, state="*")
async def pludge_google_sheet(call: CallbackQuery, state: FSMContext):
    await state.finish()
    spread_sheet_id, sheet_id = get_google_sheet_of_client(call.from_user.id)
    if spread_sheet_id:
        await call.answer(f'У вас уже подключена таблица')
        return
    if not check_if_client_is_allowed_to_get_vote_buttons(call.from_user.id):
        await call.answer('У вас не оплачена годовая подписка')
        return
    screenshots = MediaGroup()
    for photo in photos_which_describes_how_to_pludge_google_sheets:
        screenshots.attach_photo(photo)  # type: ignore
    await call.message.edit_text(
        'Для того чтобы подключить гугл таблицу к боту, следуйте следующим инструкциям:\n\n'
            '\t1)Перейдите на https://docs.google.com/spreadsheets/u/0/?tgif=d, для '
            'того, чтобы создать таблицу, если у вас её нет.\n\n'
            '\t2)Перейдите в <i>Настройки Доступа</i> вашей таблицы.\n\n'
            f'\t3)Вставьте адрес <code>{GOOGLE_SERVICE_EMAIL}</code> в поле '
            '"<i>Добавьте пользователей или группы</i>"'
            '. Проверьте, чтобы в раскрывающемся списке справа от ввода был выбран пункт <b>"редактор"</b>.\n\n'
            '\t4)Скопируйте ID вашей гугл таблицы, для этого выделите часть в ссылке между \'<b>d/</b>\' и '
            '\'<b>/edit</b>\' (Или просто скопируйте всю ссылку).\n\n'
            '\t5)Перешлите скопированный ID (или ссылку) в этот чат.\n\n'
        'Бот создаст новый лист, в который будет ежедневно выгружать статистику выделенных '
        'заявок вами и вашими подключенными аккаунтами'
        ' по каждой категории, на которую у вас действует годовая подписка.\n'
        f'Пример таблицы: {GOOGLE_SPREAD_SHEET_EXAMPLE}.\n\nОтправьте ссылку на таблицу, следуя инструкции:',
        parse_mode = 'HTML',
        disable_web_page_preview = True
    )
    await call.bot.send_media_group(call.from_user.id, screenshots)
    await state.set_state("get_spread_sheet_id")

# dp.msg_handler(state = States.get_spread_sheet_id)
handle_get_spread_sheet_id = lambda dp: dp.register_message_handler(get_spread_sheet_id, state="get_spread_sheet_id")
async def get_spread_sheet_id(msg: Message, state: FSMContext):
    spread_sheet = msg.text
    if 'docs.google.com/spreadsheets/' in spread_sheet:
        spread_sheet = spread_sheet[spread_sheet.find('d/') + 2 : ]
        spread_sheet = spread_sheet[ : spread_sheet.find('/')]
    if spread_sheet in GOOGLE_SPREAD_SHEET_EXAMPLE:
        await msg.answer('Нельзя пользоваться этой таблицей')
        return
    sheet_id = connect_to_gsh_and_get_sheet_id(spread_sheet)
    if sheet_id == -1:
        await msg.answer('Произошла ошибка при попытке подключиться к таблице. Проверьте, '
            'дали ли вы доступ боту к вашей таблице, верен ли введеный '
            'вами ID и попробуйте ввести его заново. (либо отправьте /cancel)')
        return
    await state.finish()
    try:
        save_google_sheet_to_client(msg.from_user.id, spread_sheet, sheet_id)
    except:
        logging.critical(
            F'Failed to save client`s({msg.from_user.id}) google sheet ("{spread_sheet}", {sheet_id}):', 
            exc_info = True
        )
        await msg.answer('При подключении произошла ошибка.')
        return
    await msg.answer('Гугл таблица успешно подключена и доступна по ссылке: ' + \
        GOOGLE_SHEET_URL_TEMPLATE.format(spread_sheet, sheet_id))

# dp.call_query_handler(lambda call: call.data == DEL_GOOGLE_SHEET, state = '*')
handle_unpludge_google_sheet = lambda dp: dp.register_callback_query_handler(unpludge_google_sheet, text=DEL_GOOGLE_SHEET, state="*")
async def unpludge_google_sheet(call: CallbackQuery, state: FSMContext):
    await state.finish()
    spread_sheet_id, sheet_id = get_google_sheet_of_client(call.from_user.id)
    if not spread_sheet_id:
        await call.answer('У вас не подключена гугл таблица')
        return
    delete_spread_sheet_of_client(call.from_user.id)
    try:
        await call.message.edit_text('Таблица отключена')
    except:
        return


def register_handler(dp):
    handle_get_google_sheets_customing_panel(dp)
    handle_pludge_google_sheet(dp)
    handle_get_spread_sheet_id(dp)
    handle_unpludge_google_sheet(dp)