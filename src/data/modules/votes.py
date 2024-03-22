VOTES_TABLE = 'users_votes'
VOTE_ID = 'id'
DATE = 'date'
USER_ID = 'user_id'
CATEGORY = 'category'
MESSAGE_ID = 'message_id'
VOTE_TYPE = 'vote_type'

#vote types
TARGET = 1
NOT_TARGET = 0
SPAM = -1
SPAM_ONLY_FOR_CLIENT = -2
vote_type_names = {
    TARGET: 'целевое',
    NOT_TARGET: 'не целевое',
    SPAM : 'спам',
    SPAM_ONLY_FOR_CLIENT: 'заблокировать'
}

MESSAGE_VOTE = 'msg_vote'
CONFIRM_SPAM = 'this_is_spam'
THROW_MSG_TO_SPAM = 's'
JUST_DEL_MSG = 'd'
DISCARD_SPAM = 'this_is_not_spam'
GET_VOTE_STATISTICS = '📊 Статистика'