from aiogram.utils.exceptions import *


class MessageInvalid(MessageNotModified, MessageCantBeEdited, MessageTextIsEmpty):
    ...