from aiogram.types import CallbackQuery
from aiogram import Dispatcher
from message_deleting import DELETE_MESSAGE, del_sended_message_by_callback_query


def init_callbacks(
    dp: Dispatcher, bot_id: int
):  # bot_id can be either PAYING_BOT_ID or SENDER_BOT_ID (+category id)
    bot = dp.bot

    @dp.callback_query_handler(lambda c: c.data.startswith(DELETE_MESSAGE))
    async def message_deleting_query_handler(call: CallbackQuery):
        await del_sended_message_by_callback_query(call, bot, bot_id)

