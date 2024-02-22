from aiogram import Dispatcher
from .inject import InjectMiddleware
from .throttling import ThrottlingMiddleware


def register_middlewares(dp: Dispatcher, db, config, queue, engine) -> None:
    dp.middleware.setup(InjectMiddleware(db=db, config=config, queue=queue, engine=engine))
    
    