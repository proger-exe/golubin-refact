import asyncio
from datetime import datetime
import json
import logging
from aiogram import Bot
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram_calendar import SimpleCalendar, simple_cal_callback
from src.apis.ClientsData.StopWords import edit_bot_filter
from src.data import bot_data, config
from db import JUST_DEL_MSG, THROW_MSG_TO_SPAM, generate_statistics_texts_for_message
from src.utils.client import Client 
from src.data.bot_data import MESSAGE_FILTER, MIN_PERIOD_TO_GET_VOTE_BUTTONS, days_per_period
from src.utils.errors import MessageInvalid
from src.utils.message_deleting import del_spam_message

async def get_vote_period_for_statistics(msg: Message, fsm: FSMContext):
    """
    Функция для получения периода статистики.

    :param msg: Объект сообщения (тип данных: `Message`) - входящее сообщение, инициирующее запрос статистики.
    :param fsm: Объект состояния конечного автомата (тип данных: `FSMContext`) - состояние пользовательского взаимодействия с ботом.
    """
    subscribes = Client.get_clients_by_filter(id=msg.from_id, payment_period_end=datetime.now(), greater=True)
    paid_for_year = any(subscribe.has_paid_period and subscribe.payment_period >= days_per_period[MIN_PERIOD_TO_GET_VOTE_BUTTONS] for subscribe in subscribes)
    
    if not paid_for_year:
        await msg.answer("Для использования статистики необходимо приобрести годовую подписку")
        return 
    
    await fsm.set_state("get_period_for_votes_statistics")
    await msg.answer(
        'Выберите дату начала периода отображения статистики:',
        reply_markup=await SimpleCalendar().start_calendar()
    )


async def set_period(call: CallbackQuery, callback_data: dict, state: FSMContext):
    """
    Функция для установки периода статистики.

    :param call: Объект обратного вызова (тип данных: `CallbackQuery`) - обратный вызов после выбора даты.
    :param callback_data: Словарь данных из обратного вызова (тип данных: `dict`) - данные, переданные в обратном вызове от календаря.
    :param state: Объект состояния конечного автомата (тип данных: `FSMContext`) - состояние пользовательского взаимодействия с ботом.
    """
    selected, date = await SimpleCalendar().process_selection(call, callback_data)
    
    if not selected:
        return 
    
    data = await state.get_data()
    if not data:
        await state.update_data(first_date=date)
        await call.message.edit_text("Выберите дату конца периода для отображения статистики:", reply_markup=await SimpleCalendar().start_calendar())
        return 
    
    try:
        await call.message.delete()
    except:
        return 
    
    await state.finish()
    
    date_period = (data['first_date'], date)
    period = [d.strftime(r"%d.%m.%Y") for d in date_period]
    
    message = await call.message.answer(
        f"Статистика отмеченных заявок за период с {period[0]} по {period[1]}\n"
        f"(Пожалуйста, подождите, идет сбор информации...)"
    )
    
    statistics = generate_statistics_texts_for_message(message.bot, message.from_user.id, date_period)  # TODO: rewrite generate_statistics_texts_for_message
    if not statistics:
        try:
            await message.edit_text(f'У вас нет отмеченных заявок за период с {period[0]} по {period[1]}')
        except:
            pass 
        return 
    
    try:
        await message.edit_text(
            message.text.split('\n')[0]
        )
    except MessageInvalid:
        pass 
    
    for text in statistics:
        try:
            await call.message.answer(text, "html")
        except:
            await asyncio.sleep(5)
            await call.message.answer(text, "html")

async def set_message_as_spam(call: CallbackQuery, state: FSMContext):
    """
    Функция для установки сообщения как спам.

    :param call: Объект обратного вызова (тип данных: `CallbackQuery`) - обратный вызов после подтверждения сообщения как спама.
    :param state: Объект состояния конечного автомата (тип данных: `FSMContext`) - состояние пользовательского взаимодействия с ботом.
    """
    await state.finish()
    
    _, action, to_user, relative_msg_id, category, orig_msg_id = call.data.split(":")
    to_user, relative_msg_id, category, orig_msg_id = map(int, (to_user, relative_msg_id, category, orig_msg_id))
    
    current_bot = Bot(bot_data.bot_tokens[category])
    
    try:
        admin_id = call.from_user.id
    except:
        logging.critical('Failed to get id of admin who pressed delete button:', exc_info=True)
        return 

    if action == THROW_MSG_TO_SPAM:
        try:
            nick_is_found = False 
            if call.message.entities: 
                nicks = [
                    n for n in call.message.entities 
                    if n.type in ('mention', 'url', 'email', 'phone_number', 'text_mention')
                ]
                if len(nicks) > 1:
                    nick = nicks[-1].get_text(call.message.text)
                    nick_is_found = True 
                    with open(MESSAGE_FILTER, 'r') as f:
                        filter = json.load(f)
                    for cat in config.message_categories:
                        edit_bot_filter(filter, [nick.lower()], cat, 'add')
                    with open(MESSAGE_FILTER, 'w') as f:
                        json.dump(filter, f)

                    await call.message.edit_text(
                        f'Пользователь {nick} заблокирован. Соответствующие сообщения будут удалены.'
                    )
                    await current_bot.send_message(
                        to_user, 
                        f'Администратор проверил это сообщение: {nick} заблокирован.',
                        reply_to_message_id=orig_msg_id
                    )
            if not nick_is_found:
                await call.message.edit_text("К содержанию, не удалось получить контакт автора заявки для блокировки. Сообщение просто будет удалено")
                
                await current_bot.send_message(
                    to_user, 
                    'Администратор проверил это сообщение: сообщения будут удалены.',
                    reply_to_message_id=orig_msg_id
                )

        except:
            logging.error('Failed to notify about spam blocking:', exc_info=True)
    
    elif action == JUST_DEL_MSG:
        try:
            await call.message.edit_text("Это сообщение будет удалено.")
            await current_bot.send_message(
                to_user, 
                'Администратор проверил это сообщение: сообщения будут удалены.',
                reply_to_message_id=orig_msg_id
            )
        except:
            logging.error("Failed to notify about spam-message-deleting: ", exc_info=True)
        
    await (await current_bot.get_session()).close()

    succesfully, unsuccesfully, total = await del_spam_message(relative_msg_id, category, (to_user, orig_msg_id))

    text = ( 
        f'Всего: <b>{total}</b>\n'
        f'Успешно: <b>{succesfully}</b>\n' 
        f'Не удалось удалить: <b>{unsuccesfully}</b>'
    )
    try:
        await call.message.edit_text(text, parse_mode='HTML')
    except:
        await call.bot.send_message(admin_id, text, parse_mode='HTML')

async def cancel_setting_message_as_spam(callback: CallbackQuery, state: FSMContext):
    """
    Функция для отмены установки сообщения как спам.

    :param callback: Объект обратного вызова (тип данных: `CallbackQuery`) - обратный вызов после отмены установки сообщения как спама.
    :param state: Объект состояния конечного автомата (тип данных: `FSMContext`) - состояние пользовательского взаимодействия с ботом.
    """
    await state.finish()
    _, to_user, orig_msg_id, category = callback.data.split(bot_data.CALLBACK_SEP)
    to_user, orig_msg_id, category = map(int, (to_user, orig_msg_id, category))
    await callback.message.edit_text('Отмена операции.')
    current_bot = Bot(bot_data.bot_tokens[category])
    await current_bot.send_message(to_user, 'Администратор не подтвердил, что это сообщение является спамом.', 
        reply_to_message_id=orig_msg_id)
    await (await current_bot.get_session()).close()
