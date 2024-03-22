import datetime
import random
import typing

from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import *

from src.data import bot_config
from src.utils.client import Client
from src.apis.db.user import client_has_year_subscribe
from src.data import config
from src.data.bot_config import ACCOUNTS_BUTTON, CALLBACK_SEP, MIN_PERIOD_TO_GET_VOTE_BUTTONS
from src.markups.users import accounts, manage_account_keyboard
from src.apis.db.accounts import *
from src.utils.bot_get_nick import get_nick
from src.data.modules import accounts_manage



# dp.register_message_handler(text = ACCOUNTS_BUTTON, state = '*')
handle_manage_accounts_message_handler = lambda dp: dp.register_message_handler(manage_accounts_message_handler, text=ACCOUNTS_BUTTON, state="*")
async def manage_accounts_message_handler(message: Message, state: FSMContext):
    admin = get_admin_of_account(message.from_user.id)
    
    if admin:
        await message.answer('Вы не можете подключать аккаунты, '
            f'так как ваш аккаунт уже подключен к {await get_nick((await message.bot.get_chat_member(admin, admin)).user)}')
        return
    
    await manage_accounts(message.from_user.id, state, message = message)

handle_manage_accounts_callback = lambda dp: dp.register_callback_query_handler(manage_accounts_callback_handler, text=accounts_manage.GET_BACK_TO_ACCOUNTS_MANAGING)
async def manage_accounts_callback_handler(callback: CallbackQuery, state: FSMContext):
    await manage_accounts(callback.from_user.id, state, callback)


async def manage_accounts(client_id: int, state: FSMContext, call: CallbackQuery = None, message: Message = None 
):
    if not message and not call:
        raise ValueError('There is no whether message or callback setted in arguments')

    if message:
        answer = message.answer
        bot = message.bot 
    else:
        answer = call.message.answer
        bot = call.bot 
    
    await state.finish()
    text = ''
    has_year_sub = client_has_year_subscribe(client_id)
    
    if not has_year_sub:
        text = 'Для подключения дополнительных аккаунтов у вас должна быть оплачена годовая подписка'
        try:
            await answer(text)
        except (MessageNotModified, MessageCantBeEdited, MessageTextIsEmpty):
            return
    
    account_ids = {}
    current_max_number_of_accounts = 0
    num_of_accounts = 0

    for category in config.message_categories:
        accs = get_all_accounts_of(client_id, category)
        if accs:
            num_of_accounts += len(accs)
            account_ids[category] = accs
        if client_has_year_subscribe(client_id, category):
            current_max_number_of_accounts += accounts_manage.MAX_NUMBER_OF_ACCOUNTS
    
    if not account_ids:
        text += f'\nУ вас нет аккаунтов. Максимально допустимое количество аккаунтов: {accounts_manage.MAX_NUMBER_OF_ACCOUNTS} ' \
        'для каждой категории, по которой у вас оплачена годовая подписка'
            
    else:
        accounts = await get_clients_account_nick_text(account_ids, bot=bot)
        
        yet_allowed_number_of_accounts = str(current_max_number_of_accounts - num_of_accounts)
        
        ending = 'аккаунт'
        ending += 'а' if yet_allowed_number_of_accounts[-1] in ('2', '3', '4') else 'ов'
        # я знаю что это не сделало его читабельнее. Он хотябы выглядит как код.
        
        ending = f'{yet_allowed_number_of_accounts} {ending}'
        text += (
            f'\nВаши текущие аккаунты:{accounts}'
            '\nМаксимально допустимое количество аккаунтов для каждой '
            f'категории: {accounts_manage.MAX_NUMBER_OF_ACCOUNTS}. Вы можете подключить ещё {ending}'
        )
            
    try:
        await answer(text, reply_markup = manage_account_keyboard(account_ids, has_year_sub), parse_mode = 'HTML')   
    except (MessageNotModified, MessageCantBeEdited, MessageTextIsEmpty):
        return


async def get_clients_account_nick_text(accounts: typing.Dict[int, typing.List[int]] = None, add_ids: bool = False, bot = None
) -> str:
    out_text = ''
    for category in accounts:
        nicknames = []
        for acc in accounts[category]:
            try:
                nickname = await get_nick((await bot.get_chat_member(acc, acc)).user)
            except:
                nickname = str(acc)
                if add_ids:
                    nickname = f'<code>{nickname}</code>'
            else:
                if add_ids:
                    nickname = f'{nickname} (<code>{acc}</code>)'
            nicknames.append(nickname)
        nicknames = '\n\t'.join(nicknames)
        out_text += f'\n{config.message_category_names[category]}:\n\t{nicknames}'
    return out_text


# # dpcallback_query_handler(lambda callback: callback.data == _ADD_ACCOUNT, state = '*')
async def get_id_to_add_new_account(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    year_subscribes = Client.get_clients_by_filter(
        id = callback.from_user.id, 
        payment_period = bot_config.days_per_period[MIN_PERIOD_TO_GET_VOTE_BUTTONS],
        payment_period_end = datetime.datetime.now(),
        greater = True # payment_period and payment_period_end must be greater (or equal)
    )
    if not year_subscribes:
        await callback.answer('У вас не оплачена никакая годовая подписка.')
        return
    if len(year_subscribes) > 1:
        choose_cat_to_add = accounts(year_subscribes, callback.from_user.id)
        await callback.message.edit_text('Выберите категорию подписки, к которой хотите добавить аккаунт:',
            reply_markup = choose_cat_to_add)


    else:
        sub = year_subscribes[0]
        if len(get_all_accounts_of(sub.id)) >= accounts_manage.MAX_NUMBER_OF_ACCOUNTS:
            try:
                await callback.message.edit_text('Вы уже достигли максимального количества '
                    f'аккаунтов по категории {config.message_category_names[sub.sending_mode]}')
            except (MessageNotModified, MessageCantBeEdited, MessageTextIsEmpty):
                return
            return
        await ask_to_send_id_of_account(sub.sending_mode, callback, state)

async def ask_to_send_id_of_account(for_category: int, callback: CallbackQuery, state: FSMContext):
    await state.set_state("get_id_of_account_to_add")
    await state.update_data(category = for_category)
    try:
        await callback.message.edit_text('Отправьте ID или перешлите сообщение от аккаунта, который вы '
            f'хотите подключить (категория {config.message_category_names[for_category]}).')
    except (MessageNotModified, MessageCantBeEdited, MessageTextIsEmpty):
        pass
    

handle_add_new_account = lambda dp: dp.register_message_handler(add_new_account, state="get_id_of_account_to_add")
# # dpmessage_handler(state = _States.get_id_of_account_to_add)
async def add_new_account(message: Message, state: FSMContext):
    if not message.is_forward():
        try:
            new_account = int(message.text)
            if new_account < 0:
                raise Exception()
        except:
            await message.answer(
                'Введено некорректное значение, попробуйте ещё раз (или отправьте /cancel для отмены).')
            return
    else:
        try:
            new_account = message.forward_from.id
        except:
            await message.answer('Не удалось получить пользователя, проверьте, активирован ли на нём этот бот.')
            await state.finish()
            return
    category = (await state.get_data())['category']
    all_acounts = get_all_accounts_of(message.from_user.id, category)
    if new_account in all_acounts:
        await message.answer(f'Вы уже подключали этот аккаунт к <i>{config.message_category_names[category]}</i> ранее',
            parse_mode='HTML')
        return
    if len(all_acounts) >= accounts_manage.MAX_NUMBER_OF_ACCOUNTS:
        await message.answer('Вы уже подключили максимальное количество аккаунтов для этой категории')
        return
    if new_account == message.from_user.id:
        await message.answer('Вы ввели ID аккаунта, которым пользуетесь прямо сейчас.')
        return
    if get_all_accounts_of(new_account):
        await message.answer('К этом аккаунту уже подключены другие. Нельзя подключать админа группы клиентов '
            'к своим аккаунтам.')
        return
    admin =  get_admin_of_account(new_account)
    if admin and admin != message.from_user.id:
        try:
            acc_nick = await get_nick((await message.bot.get_chat_member(new_account, new_account)).user)
        except:
            acc_nick = str(new_account)
        try:
            admin_nick = await get_nick((await message.bot.get_chat_member(admin, admin)).user)
        except:
            acc_nick = str(admin)
        await message.answer(f'Нельзя добавить аккаунт {acc_nick}, т.к. он уже подключен к {admin_nick}')
        return
    subscribes = Client.get_client_by_id(new_account)
    if subscribes:
        subscribes = ', '.join([config.message_category_names[sub.sending_mode] for sub in subscribes])
        await message.answer(
            f'<b>Внимание</b>! У аккаунта, который вы хотите подключить есть активные подписки по {subscribes}. '
            'Если вы не хотите добавлять его, нажмите /cancel', parse_mode = 'HTML'
        )
    code = random.randint(1000, 9999)
    try:
        await message.bot.send_message(
            new_account, 
            f'{await get_nick(message.from_user)} хочет подключить '
            f'ваш аккаунт к своей подписке по категории {config.message_category_names[category]}. '
            'Чтобы совершить эту операцию, перешлите ему (ей) этот код - '
            f'<code>{code}</code> для подтверждения, либо проигнорируйте это сообщение.', 
            parse_mode = 'HTML'
        )
    except:
        await message.answer('Не удалось отправить код подтверждения. Проверьте: запущен ли бот на том аккаунте, '
            'правилен ли ID, либо отправьте /cancel для отмены операции.')
        return
    await state.finish()
    await state.set_state("get_code_to_confirm_new_account")
    await state.update_data(confirmation_code = code, account_id = new_account, category = category)
    await message.answer(
        f'На {await get_nick((await message.bot.get_chat_member(new_account, new_account)).user)} отправлен '
        'код подтвреждения. Для подключения аккаунта, отправьте полученный код в этот чат.', parse_mode = 'HTML') 



# # dpmessage_handler(state = _States.get_code_to_confirm_new_account)
handle_check_confirmation_code = lambda dp: dp.register_message_handler(check_confirmation_code, state="get_code_to_confirm_new_account")
async def check_confirmation_code(message: Message, state: FSMContext):
    data = await state.get_data()
    try:
        considering_code = int(message.text)
    except:
        considering_code = None
    if considering_code != data['confirmation_code']:
        if 'fails_num' not in data:
            await message.answer('Неверный код, попробуйте ещё раз.')
            data['fails_num'] = 1
            await state.set_data(data)
        elif data['fails_num'] < 3:
            await message.answer('Неверный код, попробуйте ещё раз.')
            data['fails_num'] += 1
            await state.set_data(data)
        else:
            await message.answer('Неверный код, превшено максимальное количесто попыток.')
            await state.finish()
    else:
        category = data['category']
        add_account_to_client(message.from_user.id, data['account_id'], category)
        await state.finish()
        account_nick = await get_nick((await message.bot.get_chat_member(data['account_id'], data['account_id'])).user)
        await message.answer(
            'Аккаунт успешно подключён. Ему будет дан доступ к сообщениям и кнопкам для отметки сообщений '
            f'по категории {config.message_category_names[category]}. Так же теперь вы можете '
            f'просматривать статистику заявок. которые {account_nick} будет отмечать.', 
            parse_mode = 'HTML'
        )
        admin_nick = await get_nick(message.from_user)
        await message.bot.send_message(
            data['account_id'], 
            f'{admin_nick} добавил(а) ваш аккаунт в свой список. Теперь у вас есть доступ к его (её) подписке'
            f' по категории {config.message_category_names[category]} и кнопкам для отметки целевых (не целевых) '
            f'сообщений и спама. Также {admin_nick} сможет просматривать статистику отмеченных вами заявок.', 
            parse_mode = 'HTML'
        )


# # dpcallback_query_handler(lambda callback: callback.data == _DEL_ACCOUNT, state = '*')
handle_get_all_accounts_to_del = lambda dp: dp.register_callback_query_handler(get_all_acounts_to_del, text=accounts_manage.DEL_ACCOUNT, state="*")
async def get_all_acounts_to_del(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    account_ids = {}
    for cat in config.message_categories:
        accs =  get_all_accounts_of(callback.from_user.id, cat)
        if accs:
            account_ids[cat] = accs
    acounts_text = await get_clients_account_nick_text(account_ids, True)
    text = f'Ваши текущие аккаунты:\n\t{acounts_text}\nОтправьте ID аккаунта, который вы хотите удалить'
    try:
        await state.set_state("get_id_of_account_to_delete")
        await callback.message.edit_text(text, parse_mode = 'HTML')
    except (MessageNotModified, MessageCantBeEdited, MessageTextIsEmpty):
        return


# dpmessage_handler(state = _States.get_id_of_account_to_delete)
handle_ask_confirmation_to_delete_account = lambda dp: dp.register_message_handler(ask_confirmation_to_delete_account, state="get_id_of_account_to_delete")
async def ask_confirmation_to_delete_account(message: Message, state: FSMContext):
    try:
        account_id = int(message.text)
        if account_id < 0:
            raise ValueError()
    except:
        await message.answer('Введено некорректное значение.')
        return
    await state.finish()
    categories = accounts.get_all_categories_which_account_is_pludged_to(account_id)
    if not categories:
        await message.answer('Аккаунт уже отключен')
    if len(categories) == 1:
        await send_message_with_confirmation_to_delete_account(account_id, categories[0], message)
    else:
        kb = InlineKeyboardMarkup()
        for cat in categories:
            kb.add(
                InlineKeyboardButton(
                    config.message_category_names[cat], 
                    callback_data = CALLBACK_SEP.join([accounts_manage.CHOOSE_CATEGORY_TO_DEL_ACC, str(cat), str(account_id)]))
            )
        kb.add(
            InlineKeyboardButton(
                'Отключить все категории', 
                callback_data = CALLBACK_SEP.join(
                    [accounts_manage.CHOOSE_CATEGORY_TO_DEL_ACC, str(accounts_manage.ALL_CATEGORIES), str(account_id)])
            )
        )
        await message.answer('Выберите категорию, от которой хотите отключить аккаунт', reply_markup = kb)

async def send_message_with_confirmation_to_delete_account(account_id: int, category: int, message: Message = None,
callback: CallbackQuery = None):
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton('Подтвердить', 
            callback_data = CALLBACK_SEP.join([accounts_manage.CONFIRM_DELETE_ACCOUNT, str(category), str(account_id)])),
        InlineKeyboardButton('Отмена', callback_data = accounts_manage.DEL_ACCOUNT)
    )
    try:
        nick = await get_nick((await message.bot.get_chat_member(account_id, account_id)).user)
    except:
        nick = str(account_id)
    if message:
        await message.answer(
            f'Вы уверены, что хотите удалить {nick}?', reply_markup = kb, parse_mode = 'HTML')
        return
    try:
        await callback.message.edit_text(
            f'Вы уверены, что хотите удалить {nick}?', reply_markup = kb, parse_mode = 'HTML')
    except (MessageNotModified, MessageCantBeEdited, MessageTextIsEmpty):
        return

# dpcallback_query_handler(lambda callback: callback.data.startswith(_CHOOSE_CATEGORY_TO_DEL_ACC), state = '*')
handle_chs_cat_to_delete_acc = lambda dp: dp.callback_query_handler(chs_cat_to_delete_acc, text_startswith=accounts_manage.CHOOSE_CATEGORY_TO_DEL_ACC)
async def chs_cat_to_delete_acc(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    _, category, account_id = callback.data.split(CALLBACK_SEP)
    account_id = int(account_id)
    await send_message_with_confirmation_to_delete_account(account_id, category, callback = callback)

# dpcallback_query_handler(lambda callback: callback.data.startswith(_CONFIRM_DELETE_ACCOUNT), state = '*')
handle_delete_account = lambda dp: dp.register_callback_query_handler(_delete_account, text_startswith=accounts_manage.CONFIRM_DELETE_ACCOUNT, state="*")
async def _delete_account(callback: CallbackQuery, state: FSMContext): 
    await state.finish()
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(bot_config.BACK_BUTTON_TEXT, callback_data = accounts_manage.DEL_ACCOUNT))
    _, category, account_id = callback.data.split(CALLBACK_SEP)
    category = int(category)
    account_id = int(account_id)
    try:
        if category == accounts_manage.ALL_CATEGORIES:
            await callback.message.edit_text('Аккаунт удален.', reply_markup = kb)
        else:
            await callback.message.edit_text(f'Аккаунт отключен от категории {config.message_category_names[category]}', 
                reply_markup = kb)
    except (MessageNotModified, MessageCantBeEdited, MessageTextIsEmpty):
        return
    if category != accounts_manage.ALL_CATEGORIES:
        delete_account(callback.from_user.id, account_id, category)
    else:
        delete_account(callback.from_user.id, account_id)
        
def register_handlers(dp):
    handle_add_new_account(dp)
    handle_ask_confirmation_to_delete_account(dp)
    handle_check_confirmation_code(dp)
    handle_chs_cat_to_delete_acc(dp)
    handle_delete_account(dp)
    handle_get_all_accounts_to_del(dp)
    handle_manage_accounts_callback(dp)
    handle_manage_accounts_message_handler(dp)