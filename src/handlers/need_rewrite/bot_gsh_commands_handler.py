from asyncio.log import logger
import logging
from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import *
from yoomoney import Account


raise Exception("File need to rewrite")
import Votes
from ...apis.ClientsData.GoogleSheets.daily_clients_gsh_uploading import connect_to_gsh_and_get_sheet_id
from bot_config import CALLBACK_SEP
from ...apis.ClientsData.GoogleSheets.config import DEL_GOOGLE_SHEET, GOOGLE_SHEETS_BUTTON
from ..Accounts import get_admin_of_account
from Votes import check_if_client_is_allowed_to_get_vote_buttons
from bot_get_nick import get_nick
from ...apis.ClientsData.GoogleSheets.clients_google_sheets import *

class States(StatesGroup):
    get_spread_sheet_id = State()

def set_google_sheet_add_handlers(dp: Dispatcher):
    bot = dp.bot

    @dp.message_handler(lambda message: message.text == GOOGLE_SHEETS_BUTTON, state = '*')
    async def get_google_sheets_customing_panel(message: Message, state: FSMContext):
        await state.finish()
        admin = get_admin_of_account(message.from_user.id)
        if admin:
            await message.answer('Вы не можете настривать гугл таблицы, так как ваш аккаунт привязан к '
                f'{await get_nick((await bot.get_chat_member(admin, admin)).user)}')
            return
        if not check_if_client_is_allowed_to_get_vote_buttons(message.from_user.id):
            await message.answer(
                'Вы можете подключить гугл таблицы для выгрузки статистики отмеченных вами '
                'и вашими подключенными аккаунтами заявок. Для того, чтобы подключить свою таблицу, вам нужно оплатить'
                ' годовую подписку.'
            )
            return
        spread_sheet, sheet_id = get_google_sheet_of_client(message.from_user.id)
        kb = InlineKeyboardMarkup()
        if not spread_sheet:
            kb.add(InlineKeyboardButton('Подключить', callback_data = ADD_GOOGLE_SHEET))
            await message.answer('На данный момент у вас не подключена никакая гугл таблица', reply_markup = kb)
        else:
            kb.add(InlineKeyboardButton('Отключить', callback_data = DEL_GOOGLE_SHEET))
            await message.answer(
                f'Ваша текущая гугл таблица: {GOOGLE_SHEET_URL_TEMPLATE.format(spread_sheet, sheet_id)}', 
                reply_markup = kb
            )

    @dp.callback_query_handler(lambda callback: callback.data == ADD_GOOGLE_SHEET, state = '*')
    async def pludge_google_sheet(callback: CallbackQuery, state: FSMContext):
        await state.finish()
        spread_sheet_id, sheet_id = get_google_sheet_of_client(callback.from_user.id)
        if spread_sheet_id:
            await callback.answer(f'У вас уже подключена таблица')
            return
        if not Votes.check_if_client_is_allowed_to_get_vote_buttons(callback.from_user.id):
            await callback.answer('У вас не оплачена годовая подписка')
            return
        screenshots = MediaGroup()
        for photo in photos_which_describes_how_to_pludge_google_sheets:
            screenshots.attach_photo(photo)
        await callback.message.edit_text(
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
        await bot.send_media_group(callback.from_user.id, screenshots)
        await States.get_spread_sheet_id.set()

    @dp.message_handler(state = States.get_spread_sheet_id)
    async def get_spread_sheet_id(message: Message, state: FSMContext):
        spread_sheet = message.text
        if 'docs.google.com/spreadsheets/' in spread_sheet:
            spread_sheet = spread_sheet[spread_sheet.find('d/') + 2 : ]
            spread_sheet = spread_sheet[ : spread_sheet.find('/')]
        if spread_sheet in GOOGLE_SPREAD_SHEET_EXAMPLE:
            await message.answer('Нельзя пользоваться этой таблицей')
            return
        sheet_id = connect_to_gsh_and_get_sheet_id(spread_sheet)
        if sheet_id == -1:
            await message.answer('Произошла ошибка при попытке подключиться к таблице. Проверьте, '
                'дали ли вы доступ боту к вашей таблице, верен ли введеный '
                'вами ID и попробуйте ввести его заново. (либо отправьте /cancel)')
            return
        await state.finish()
        try:
            save_google_sheet_to_client(message.from_user.id, spread_sheet, sheet_id)
        except:
            logging.critical(
                F'Failed to save client`s({message.from_user.id}) google sheet ("{spread_sheet}", {sheet_id}):', 
                exc_info = True
            )
            await message.answer('При подключении произошла ошибка.')
            return
        await message.answer('Гугл таблица успешно подключена и доступна по ссылке: ' + \
            GOOGLE_SHEET_URL_TEMPLATE.format(spread_sheet, sheet_id))

    @dp.callback_query_handler(lambda callback: callback.data == DEL_GOOGLE_SHEET, state = '*')
    async def unpludge_google_sheet(callback: CallbackQuery, state: FSMContext):
        await state.finish()
        spread_sheet_id, sheet_id = get_google_sheet_of_client(callback.from_user.id)
        if not spread_sheet_id:
            await callback.answer('У вас не подключена гугл таблица')
            return
        delete_spread_sheet_of_client(callback.from_user.id)
        try:
            await callback.message.edit_text('Таблица отключена')
        except:
            return
