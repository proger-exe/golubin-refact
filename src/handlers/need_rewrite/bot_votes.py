import asyncio
from datetime import datetime
import json
from aiogram.dispatcher import FSMContext
from aiogram import Dispatcher
from aiogram_calendar import SimpleCalendar, simple_cal_callback
from ClientsData.StopWords import edit_bot_filter


def set_main_bot_votes_statistics(dp: Dispatcher):

    @dp.message_handler(lambda message: message.text == GET_VOTE_STATISTICS, state = '*')
    async def get_period_for_votes_statistics(message: Message):
        subscribes = Client.get_clients_by_filter(id = message.from_user.id, payment_period_end=datetime.now(), greater=True)
        paid_for_year = False
        for s in subscribes:
            if s.has_paid_period and s.payment_period >= days_per_period[MIN_PERIOD_TO_GET_VOTE_BUTTONS]:
                paid_for_year = True
                break
        if not paid_for_year:
            await message.answer('Для того, чтобы пользоваться статистикой вам нужно купить годовую подписку')
            return
        await States.get_period_for_votes_statistics.set()
        await message.answer(
            'Выберите дату начала периода отображения статистики:',
            reply_markup = await SimpleCalendar().start_calendar()
        )

    @dp.callback_query_handler(simple_cal_callback.filter(), state = States.get_period_for_votes_statistics)
    async def set_period(callback: CallbackQuery, callback_data: dict, state: FSMContext):
        selected, date = await SimpleCalendar().process_selection(callback, callback_data)
        if not selected:
            return
        data = await state.get_data()
        if not data:
            await state.update_data(first_date = date)
            await callback.message.edit_text('Выберите дату конца периода для отображения статистики:', 
                reply_markup = await SimpleCalendar().start_calendar())
            return
        try:
            await callback.message.delete()
        except:
            return
        await state.finish()
        date_period = (data['first_date'], date)
        period = [d.strftime('%d.%m.%Y') for d in date_period]
        message = await dp.bot.send_message(
            callback.from_user.id, 
            f'Статистика отмеченных заявок за период с {period[0]} по {period[1]}\n(Пожалуйста, подождите, идёт сбор ифнормации...)'
        )
        statistics = await __generate_statistics_texts_for_message(dp.bot, callback.from_user.id, date_period)
        if not statistics:
            try:
                await message.edit_text(f'У вас нет отмеченных заявок за период с {period[0]} по {period[1]}')
            except:
                return
            return
        try:
            await message.edit_text(message.text.split('\n')[0])
        except (MessageNotModified, MessageCantBeEdited, MessageTextIsEmpty):
            pass
        for text in statistics:
            try:
                await dp.bot.send_message(callback.from_user.id, text, parse_mode = 'HTML')
            except:
                await asyncio.sleep(5)
                await dp.bot.send_message(callback.from_user.id, text, parse_mode = 'HTML')

    @dp.callback_query_handler(lambda callback: callback.data.startswith(CONFIRM_SPAM), state = '*')
    async def set_message_as_spam(callback: CallbackQuery, state: FSMContext):
        await state.finish()
        _, action, to_user, relative_msg_id, category, orig_msg_id = callback.data.split(CALLBACK_SEP)
        to_user, relative_msg_id, category, orig_msg_id = \
            int(to_user), int(relative_msg_id), int(category), int(orig_msg_id)
        current_bot = Bot(bot_tokens[category])
        try:
            admin_id = callback.from_user.id
        except:
            logging.critical('Failed to get id of admin who pressed delete button:', exc_info=True)
        if action == THROW_MSG_TO_SPAM:
            try:
                nick_is_found = False
                if callback.message.entities:
                    nicks = [e for e in callback.message.entities if \
                        e.type in ('mention', 'url', 'email', 'phone_number', 'text_mention')]
                    if len(nicks) > 1: # 1 means that there is only nick of client who reported spam
                        nick = nicks[-1].get_text(callback.message.text)
                        nick_is_found = True
                        with open(MESSAGE_FILTER, 'r') as f:
                            filter = json.load(f)
                        for cat in message_categories:
                            edit_bot_filter(filter, [nick.lower()], cat, 'add')
                        with open(MESSAGE_FILTER, 'w') as f:
                            json.dump(filter, f)
                        await callback.message.edit_text(
                            f'Пользователь {nick} заблокирован. Соответсвующие сообщения будут удалены.')
                        await current_bot.send_message(
                            to_user, 
                            f'Администратор проверил это сообщение: {nick} заблокирован.',
                            reply_to_message_id = orig_msg_id
                        )
                if not nick_is_found:
                    await callback.message.edit_text('К сожалению, не удалось получить контакт автора '
                        'заявки для блокировки. Сообщение просто будет удалено')
                    await current_bot.send_message(
                        to_user, 
                        'Администратор проверил это сообщение: сообщения будут удалены.',
                                reply_to_message_id = orig_msg_id
                    )
            except:
                logging.error('Failed to notify about spam blocking:', exc_info=True)
        elif action == JUST_DEL_MSG:
            try:
                await callback.message.edit_text('Это сообщение будет удалено.')
                await current_bot.send_message(
                    to_user, 
                    'Администратор проверил это сообщение: сообщения будут удалены.',
                            reply_to_message_id = orig_msg_id
                )
            except:
                logging.error('Failed to notify about spam-message-deleting:', exc_info=True)
        await (await current_bot.get_session()).close()
        succesfully, unsuccesfully, total = await del_spam_message(relative_msg_id, category, (to_user, orig_msg_id))
        text = f'Всего: <b>{total}</b>\nУспешно: <b>{succesfully}</b>\n' \
            f'Не удалось удалить: <b>{unsuccesfully}</b>'
        try:
            await callback.message.edit_text(text, parse_mode='HTML')
        except:
            await dp.bot.send_message(admin_id, text, parse_mode='HTML')

    async def del_spam_message(relative_msg_id: int, category: int, not_delete: typing.Tuple[int, int])\
    -> typing.Tuple[int, int, int]:
        b = Bot(bot_tokens[category])
        try:
            data = message_deleting.get_sended_message_data(relative_msg_id, SENDER_BOT_ID + category)
            succesfully, unsuccesfully, total = await message_deleting.delete_sended_msg(b, data, not_delete)
            await (await b.get_session()).close()
            del data
        except:
            logging.critical(f'Failed to delete spam message by relative message id:', exc_info = True)
        message_deleting.delete_saved_message_data(relative_msg_id, SENDER_BOT_ID + category)
        return succesfully, unsuccesfully, total

    @dp.callback_query_handler(lambda callback: callback.data.startswith(DISCARD_SPAM), state = '*')
    async def cancel_setting_message_as_spam(callback: CallbackQuery, state: FSMContext):
        await state.finish()
        _, to_user, orig_msg_id, category = callback.data.split(CALLBACK_SEP)
        to_user, orig_msg_id, category = int(to_user), int(orig_msg_id), int(category)
        await callback.message.edit_text(f'Отмена операции.')
        current_bot = Bot(bot_tokens[category])
        await current_bot.send_message(to_user, 'Администратор не подтвердил, что это сообщение является спамом.', 
            reply_to_message_id = orig_msg_id)
        await (await current_bot.get_session()).close()