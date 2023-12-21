from aiogram import Dispatcher, Bot, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from src.data.config import Config
from src.apis import DataBase 
from src import filters, middlewares #, handlers


def on_startup(dp: Dispatcher, db, config):
    middlewares.register_middlewares(dp, db, config)
    filters.register_filters(dp)


def run_app():
    config = Config()
    
    bot = Bot(config.bot_token, parse_mode='html', validate_token=True)
    dp = Dispatcher(bot, storage=MemoryStorage())
    
    db = DataBase()
    on_startup(dp, db, config)

    executor.start_polling(dp, skip_updates=True)
