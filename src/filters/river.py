from aiogram.dispatcher.filters import BoundFilter
from src.apis.db import DataBase


class IsManagerFilter(BoundFilter):
    key = 'manager'

    def __init__(self, manager):
        self.manager = manager

    async def check(self, event, db: DataBase) -> bool:
        return db.read_user(event.from_user.id)[5] == "manager"


class IsPersonalFilter(BoundFilter):
    key = 'personal'

    def __init__(self, personal):
        self.personal = personal

    async def check(self, event, db: DataBase) -> bool:
        return db.read_user(event.from_user.id)[5] == "personal"

