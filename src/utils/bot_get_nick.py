from aiogram.types import User


async def get_nick(user: User) -> str:
    if user.username:
        return '@' + user.username
    else:
        return f'<a href="tg://user?id={user.id}">{user.first_name} ' + \
            f'{user.last_name if user.last_name else ""}</a>'