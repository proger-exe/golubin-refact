from . import config
from .config import TARGET, NOT_TARGET, SPAM, MESSAGE_VOTE, GET_VOTE_STATISTICS
from .users_votes import Vote
from .bot_votes_keyboards import generate_vote_keyboard, generate_vote_keyboard_for_forwarded_message,\
    message_vote_callback, set_main_bot_votes_statistics, check_if_client_is_allowed_to_get_vote_buttons, \
    get_spam_button, get_spam_button_for_forwarded_message

'''This package controlls users messages-votes'''