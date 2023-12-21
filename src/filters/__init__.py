from aiogram import Dispatcher

from .admin import IsAdminFilter


def register_filters(dp: Dispatcher):
    dp.filters_factory.bind(IsAdminFilter)
