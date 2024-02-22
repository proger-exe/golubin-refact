from aiogram.dispatcher.filters import BoundFilter
from src.data.config import Config


class IsAdminFilter(BoundFilter):
    key = 'admin'

    def __init__(self, admin):
        self.admin = admin
        self.config = Config()

    async def check(self, event) -> bool:
        return event.from_user.id in self.config.admins_id
