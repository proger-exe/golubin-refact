from aiogram.types import Message, CallbackQuery
from bot_keyboards import *
from src.apis.ClientsData import GoogleSheets, StopWords
from src.apis.db import get_connection_and_cursor
from src.apis.db.modules import promocodes, user
from src.apis.db.modules.accounts import get_admin_of_account, transfer_accounts
from src.apis.db.modules.payments_history import Payment, PaymentHistory
from src.apis.db.modules.promocodes import client_used_promocode, get_id_of_promocode, get_promocode_action, get_promocode_refer, promocode_is_in_db, set_promocode_as_used_by_client
from shutil import move
from src.apis.db.modules.referal_payments_history import ReferalPayment, ReferalPaymentsHistory
from src.apis.db.modules.statistics import save_to_statistics
from src.apis.db.modules.users_votes import Vote
from src.data.bot_config import *
from src.data.modules.history import *
from src.data.modules.refs import *
from yoomoney import Client as ymClient
from aiogram.dispatcher.storage import FSMContext
from src.utils.bot_get_nick import get_nick
from os import listdir, mkdir, remove
from aiogram_calendar import SimpleCalendar, simple_cal_callback

import typing
import types

from temp.Referal.bot_referal import process_referal


# @dp.message_handler(text= PERSONAL_CABINET, state="*")
handle_personal_panel = lambda dp: dp.register_message_handler(get_personal_panel, text=PERSONAL_CABINET, state="*")
async def get_personal_panel(msg: Message, state: FSMContext):
    await state.finish()
    try:
        await msg.answer(
            PERSONAL_CABINET_TEXT,
            reply_markup=personal_cabinet_kb,
            parse_mode="HTML",
        )
    except BotBlocked:
        return

# @dp.message_handler(text= ADDITIONAL_OPTIONS, state="*")
handle_additional_optionals = lambda dp: dp.register_message_handler(get_additional_options_kb, text=ADDITIONAL_OPTIONS, state="*")
async def get_additional_options_kb(msg: Message, state: FSMContext):
    await state.finish()
    try:
        await msg.answer(
            ADDITIONAL_OPTIONS_TEXT,
            reply_markup=additional_options_kb,
            parse_mode="HTML",
        )
    except BotBlocked:
        return

# @dp.message_handler(text= MAIN_MENU, state="*")
handle_main_menu = lambda dp: dp.regiter_message_handler(text=MAIN_MENU, state="*")
async def get_main_menu(msg: Message, state: FSMContext):
    await state.finish()
    try:
        await msg.answer(
            MAIN_MENU_TEXT, reply_markup=main_kb, parse_mode="HTML"
        )
    except BotBlocked:
        return

# @dp.message_handler(text= NEW_ORDER, state="*")
handle_new_order = lambda dp: dp.register_message_handler(text=NEW_ORDER, state="*")
async def new_order(msg: Message, state: FSMContext):
    await state.finish()
    kb = get_kb_with_categories()
    try:
        await msg.reply(CHOOSE_PERIOD_TEXT, reply_markup=kb)
    except (BotBlocked, BadRequest):
        return
    else:
        user.set_date_of_trying_to_buy(msg.from_user.id, msg.date)

# @callback_query_handler(# lambda callback: callback.data == NEW_ORDER_BUTTON, state="*")
handle_new_order_callback = lambda dp: dp.register_callback_query(new_order_callback, text=NEW_ORDER_BUTTON, state="*")
async def new_order_callback(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    kb = get_kb_with_categories()
    try:
        await callback.message.edit_text(CHOOSE_PERIOD_TEXT, reply_markup=kb)
    except:
        pass

# @callback_query_handler(text_startswith=(CHOOSE_CATEGORY), state="*")
handle_choose_order_category = lambda dp: dp.register_callback_query(choose_order_category, text_startswith=CHOOSE_CATEGORY)
async def choose_order_category(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    text = "Использовать промокод?"
    if callback.message.text == text:
        return
    category = callback.data.split(CALLBACK_SEP)[1]
    eternal_pcd = promocodes.get_last_activated_endless_promocode(
        callback.from_user.id, int(category)
    )
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton(
            "Да",
            callback_data=CALLBACK_SEP.join([USE_PROMOCODE_BUTTON, category, ""]),
        ),
        InlineKeyboardButton(
            "Нет",
            callback_data=CALLBACK_SEP.join(
                [NEW_ORDER_WITHOUT_PROMOCODE, category]
                if not eternal_pcd
                else [USE_PROMOCODE_BUTTON, category, eternal_pcd]
            ),
        ),
    )
    kb.add(InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data=NEW_ORDER_BUTTON))
    if eternal_pcd:
        text = (
            f"\n{text}\n\n(Ваш текущий действующй промокод: <i>{eternal_pcd}</i>)"
        )
    try:
        await callback.bot.edit_message_text(
            text,
            callback.from_user.id,
            callback.message.message_id,
            reply_markup=kb,
            parse_mode="HTML",
        )
    except:
        pass

# @callback_query_handler(text_startswith=(NEW_ORDER_WITHOUT_PROMOCODE), state="*")
handle_send_new_order_wo_prcmd = lambda dp: dp.register_callback_query_handler(send_new_order_wo_prmcd, text_startswith=NEW_ORDER_WITHOUT_PROMOCODE, state="*")
async def send_new_order_wo_prmcd(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    category = int(callback.data.split(CALLBACK_SEP)[1])
    sales = {}
    with_sales_during_trial = False
    with_get_last_msgs_button = False
    text = TEXT_AFTER_CATEGORY_CHOOSE
    c = Client.get_clients_by_filter(category, callback.from_user.id)
    if c:
        c = c[0]
        if client_is_in_sale_period(c):
            with_sales_during_trial = True
    elif (
        category == TARGET_MODE
        and user.date_of_recieveing_latest_messages(callback.from_user.id) == None
    ):
        with_get_last_msgs_button = True
    ref_link = get_referal_link_of_client(callback.from_user.id)
    kb = get_period_choosing_keyboard(
        category,
        sales,
        with_sales_during_trial,
        from_client=callback.from_user.id,
        requested_from=CHOOSE_CATEGORY + CALLBACK_SEP + str(category),
        with_get_last_msgs_button=with_get_last_msgs_button,
        referal_link=ref_link,
    )
    await callback.bot.edit_message_text(
        text,
        callback.message.chat.id,
        callback.message.message_id,
        reply_markup=kb,
        parse_mode="HTML",
    )

def get_referal_link_of_client(client_id: int) -> str:
    refer = RefClient.get_client_by_id(client_id)
    if refer and refer.referal_id:
        return f"{REFERAL_ID}{refer.referal_id}"
    return ""

# @callback_query_handler(lambda s: s.data.startswith(CHOOSE_PERIOD_PREFIX), state="*")
handle_choosing_period = lambda dp: dp.register_callback_query_handler(choosing_period_handler, text_startswith=CHOOSE_PERIOD_PREFIX, state="*")
async def choosing_period_handler(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    admin = get_admin_of_account(callback.from_user.id)
    if admin:
        await callback.answer(
            "Вы не можете оплачивать подписки, "
            f"так как ваш аккаунт подключен к {await get_nick((await callback.bot.get_chat_member(admin, admin)).user)}"
        )
        return
    try:
        args = callback.data.split(CALLBACK_SEP)
        _, period, mode, sales, with_sale_during_trial, referal_link = args[:6]
        requested_from = CALLBACK_SEP.join(args[6:])
    except:
        logging.error(
            f"Error while recieveing period choosing (Callback data: {callback.data}; "
            f"msg date: {callback.message.date}",
            exc_info=True,
        )
        return
    sales = eval("{" + sales + "}")
    for i in sales:
        sales[i] = Decimal(str(sales[i]))
    mode = int(mode)
    with_sale_during_trial = int(with_sale_during_trial)
    sale = get_sale(sales, period)
    cost = get_period_cost(period, mode, sale)
    _, final_text, kb = generate_text_and_keboard_for_payment(
        mode,
        period,
        cost,
        sales,
        callback.from_user.id,
        with_sale_during_trial,
        requested_from,
        callback.message.message_id,
        referal_link,
    )
    if callback.message.text != final_text:
        try:
            await callback.message.edit_text(
                final_text, reply_markup=kb, parse_mode="HTML"
            )
        except:
            pass

# @callback_query_handler(# lambda callback: callback.data == ACTIVATE_TRIAL_WITHOUT_CATEGORY)
handle_select_category_to_trial = lambda dp: dp.register_callback_query_handler(select_category_to_trial, text=ACTIVATE_TRIAL_WITHOUT_CATEGORY)
async def select_category_to_trial(callback: CallbackQuery):
    await callback.message.answer(
        CHOOSE_CATEGORY_MESSAGE,
        reply_markup=get_kb_with_categories(
            ACTIVATE_TRIAL, requested_from=NEW_ORDER_BUTTON
        ),
    )

# @callback_query_handler(# lambda callback: callback.data.startswith(ACTIVATE_TRIAL), state="*")
handle_make_trial = lambda dp: dp.register_callback_query_handler(text_startswith=ACTIVATE_TRIAL)
async def make_trial(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    admin = get_admin_of_account(callback.from_user.id)
    if admin:
        callback.answer
        await callback.answer(
            "Вы не можете использовать пробный период, так как ваш аккаунт подключен к "
            f"{await get_nick((await callback.bot.get_chat_member(admin, admin)).user)}",
            show_alert=True,
        )
        return
    try:
        await callback.message.delete()
    except:
        pass
    _, mode, referal_link = callback.data.split(CALLBACK_SEP)
    mode = int(mode)
    client_id = callback.from_user.id
    cl_is_in_any_db, client = client_is_in_db(client_id, mode)
    if client:
        if client.is_using_trial or client.was_offered_sale:
            await callback.bot.send_message(
                callback.from_user.id,
                "Вы уже использовали пробный период по категории "
                f"{message_category_names[mode]}.",
            )
        else:
            await callback.bot.send_message(
                callback.from_user.id,
                "Вам больше не доступен пробный период по категории "
                f"{message_category_names[mode]}.",
            )
        return
    d_now = datetime.now()
    trial_p_end = d_now + timedelta(days=days_per_period[TRIAL_PERIOD])
    ref_info = RefClient.get_client_by_id(client_id)
    if ref_info and ref_info.referal_status == HAS_REFS and ref_info.refers_num:
        trial_p_end += timedelta(days=REFERAL_ADDITIONAL_TRIAL_DAYS)
    client = Client(client_id, d_now, trial_p_end, mode)
    con, cur = get_connection_and_cursor()
    client.add_to_db(con, cur)
    client.warning_status = NOT_WARNED
    client.has_paid_period = False
    client.set_trial_period(trial_p_end)
    save_to_statistics(
        new_users=int(not cl_is_in_any_db),
        activated_trial=1,
        ref_link=parse_referal_link(referal_link),
    )
    await callback.bot.send_message(
        client_id,
        f"Срок пробного периода истекает {client.payment_end.strftime(PAYMENT_END_DATE_FORMAT)}.\n\n"
        f"{TEXT_AFTER_FIRST_PAYMENT.format(bot_names[client.sending_mode])}\n\nДля того, "
        f'чтобы пользоваться пробным периодом, необходимо подписаться на {", ".join(get_channel_for_trial_period())}',
    )
    await send_article_if_it_is_promised(client_id, callback.bot)
    await callback.bot.send_message(client_id, "Главное меню", reply_markup=main_kb)
    user.set_user_as_offered_trial(client_id)
    date_of_recieveing_latest_messages = user.date_of_recieveing_latest_messages(
        client.id
    )
    if (
        not date_of_recieveing_latest_messages
        or (datetime.now() - date_of_recieveing_latest_messages).days >= 2
    ):
        await try_to_send_latest_messages(client)

def client_is_in_db(
    client_id: int, mode: int
) -> typing.Tuple[bool, Union[Client, None]]:
    """
    returns:
        1) client is in any clients category (target, smm, copyright etc)
        2) client`s subscribe from current `mode`s category if it`s there else None
    """
    clients = Client.get_client_by_id(id=client_id)
    client_is_in_db = True if clients else False
    for client in clients:
        if client.sending_mode == mode:
            return client_is_in_db, client
    return client_is_in_db, None

def get_channel_for_trial_period() -> str:
    with open(BOT_DATA_FILE) as f:
        return json.load(f)["channel-for-using-trial"]

def parse_referal_link(referal_link: str) -> str:
    if referal_link.startswith(REFERAL_ID):
        return f"t.me/{PAYING_BOT_NICK}?start=ref{referal_link[1:]}"
    if referal_link.startswith(PROMOCODE_ID):
        prm_id = int(referal_link[1:])
        try:
            return promocodes.get_promocode_by_id(prm_id)
        except ValueError:
            return ""
    return ""

async def send_article_if_it_is_promised(client_id: int, bot):
    # after offering trial client is promised to be recieved the special article
    if user.user_is_offered_trial(client_id):
        await bot.send_message(
            client_id,
            "Обещанный бонус для "
            "тебя. Чтобы тестовый период прошел "
            "с максимальной эффективностью, я "
            "подготовил статью с рекомендациями по "
            "продаже в Telegram. В ней я делюсь "
            "опытом, который наработал за 5 лет "
            "продаж таргета.\n\n"
            "<b>https://vk.com/@golandco-kak-ya-za-2000-rub-poluchil-klientov-po-targetu-na-summu-350</b>\n\n"
            "Переходи и читай - будет полезно!",
            parse_mode="HTML",
        )

# @callback_query_handler(lambda s: s.data.startswith(SELECT_PER_CHOOSE_KB), state="*")
handle_back_to_period_choosing = lambda dp: dp.register_callback_query_handler(back_to_period_choosing, text_startswith=SELECT_PER_CHOOSE_KB, state="*")
async def back_to_period_choosing(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    args = callback.data.split(CALLBACK_SEP)
    _, mode, sales, with_sales_during_trial, referal_link = args[:5]
    requested_from = CALLBACK_SEP.join(
        args[5:]
    )  # in case requested_from is callback string (contains separators)
    mode = int(mode)
    with_sales_during_trial = int(with_sales_during_trial)
    sales = eval("{" + sales + "}")
    for i in sales:
        sales[i] = Decimal(sales[i])
    text = TEXT_AFTER_CATEGORY_CHOOSE
    if sales:
        text += "\n\nТекущие скидки:\n"
        for p in days_per_period:
            if p == TRIAL_PERIOD:
                continue
            sale = get_sale(sales, p)
            if sale:
                text += (
                    p
                    + " дн. - "
                    + str(delete_float_point_if_is_not_fraction(sale * 100))
                    + "%\n"
                )
        text += "\n(Цены указаны с учётом скидки)"
    try:
        await callback.bot.edit_message_text(
            text=text,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=get_period_choosing_keyboard(
                mode,
                sales,
                with_sales_during_trial,
                requested_from=requested_from,
                from_client=callback.from_user.id,
                referal_link=referal_link,
            ),
            parse_mode="HTML",
        )
    except:
        pass

# @callback_query_handler(lambda s: s.data.startswith(PAY_FOR_PERIOD_PREFFIX + CALLBACK_SEP), state="*")
handle_pay = lambda dp: dp.register_callback_query_handler(text_startswith=PAY_FOR_PERIOD_PREFFIX + CALLBACK_SEP, state="*")
async def pay(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    args = callback.data.split(CALLBACK_SEP)
    (
        _,
        str_period,
        label,
        mode,
        with_sale_during_trial,
        referal_link,
        required_transfers_num,
    ) = args
    mode = int(mode)
    with_sale_during_trial = int(with_sale_during_trial)
    period = days_per_period[str_period]
    history = ym_client.operation_history(label=label)
    cost = 0
    if len(history.operations):
        operations_num = len(history.operations)
        if operations_num < int(required_transfers_num):
            await callback.bot.send_message(
                callback.from_user.id,
                f"Вам нужно выполнить перевод {required_transfers_num} раза, вы сделали только {operations_num}",
            )
            return
        cost = sum(
            [Decimal(str(operation.amount)) for operation in history.operations]
        )
    elif TESTING:
        cost = get_period_cost_without_sales(str_period, mode)
    else:
        await callback.bot.send_message(
            callback.from_user.id,
            "Оплата не была произведена, либо произошла ошибка.",
        )
        return
    if TEXT_ABOUT_REFERAL_WITHDRAWAL_FOR_PAYMENT in callback.message.text:
        referal_fee = Decimal(
            callback.message.text.split("\n")[-1].split()[0][1:].replace(",", ".")
        )
    else:
        referal_fee = Decimal(0)
    try:
        await process_payment(
            callback,
            cost,
            period,
            mode,
            with_sale_during_trial,
            label,
            referal_fee,
            referal_link,
        )
    except Exception as e:
        logging.error("Error in process_payment: " + str(e), exc_info=True)

async def process_payment(
    callback: CallbackQuery,
    cost: Decimal,
    period: int,
    category: int,
    with_sale_during_trial: bool,
    label: str = "",
    referal_fee: Decimal = Decimal(0),
    referal_link: str = "",
):
    chat_id, msg_id = callback.message.chat.id, callback.message.message_id
    if (chat_id, msg_id) in failed_to_delete:
        return
    client_id = callback.from_user.id
    try_to_edit = False
    try:
        await callback.message.delete()
    except Exception as e:
        try_to_edit = True
        failed_to_delete.append((chat_id, msg_id))
    if try_to_edit:
        try:
            await callback.message.edit_text("Спасибо за оплату.")
        except:
            logging.exception(
                f"Failed to delete msg ({chat_id}, {msg_id}) when process {period} days"
            )
            return
    commission = 0
    try:
        commission = await process_referal(client_id, cost, callback.bot)
    except Exception as e:
        logging.error(
            f"Process referal for {client_id} is failed: " + str(e), exc_info=True
        )
    clients = Client.get_client_by_id(id=client_id)
    client_id_is_in_db = bool(len(clients))
    current_client = None
    had_paid_period = False
    if client_id_is_in_db:
        current_client = [c for c in clients if c.sending_mode == category]
        current_client = current_client[0] if current_client else None
        had_paid_period = any([c.has_paid_period for c in clients])
    if with_sale_during_trial:
        if client_id_is_in_db:
            current_client.used_sale = True
        else:
            logging.warning(f"Client({client_id}) is not in database but used sale")
    try:
        payment = Payment(
            period,
            cost,
            commission,
            callback.from_user.id,
            category=category,
            referal_link=parse_referal_link(referal_link),
        )
        PaymentHistory.savePayment(payment)
    except Exception as e:
        logging.critical("Failed to save payment: ", exc_info=True)
    nick = await get_nick(callback.from_user)
    await notify_about_new_payment(
        callback, category, period, cost, nick, referal_fee
    )
    now = datetime.now()
    last_payment_end = datetime(1000, 1, 1, 1, 1)
    bonus_days = (
        BONUS_DAYS_AT_THE_END_OF_TRIAL
        if with_sale_during_trial
        and str(period) == PERIOD_WITH_BONUS_DAYS_AFTER_THE_END_OF_TRIAL
        else 0
    )
    try:
        if current_client:
            last_payment_end = current_client.payment_end
            if current_client.payment_end.date() >= datetime.now().date():
                current_client.payment_end += timedelta(days=period + bonus_days)
            else:
                current_client.payment_end = now + timedelta(
                    days=period + bonus_days
                )
            current_client.last_payment_date = now
        else:
            current_client = Client(
                client_id, now, now + timedelta(days=period + bonus_days), category
            )
        had_paid_period_for_current_category = current_client.has_paid_period
        con, cur = get_connection_and_cursor()
        current_client.add_to_db(con, cur)
        current_client.warning_status = NOT_WARNED
        current_client.has_paid_period = True
        current_client.max_pause_days = pause_periods[str(period)]
        current_client.used_pause_days = 0
    except Exception as e:
        error_message = "Failed to add a client into database after paying: "
        logging.critical(error_message + str(e), exc_info=True)
        await callback.bot.send_message(
            DEVELOPER_ID,
            error_message
            + f" {label}, {msg_categories[category]}, {period} days, {nick}, {callback.from_user.id}",
            parse_mode="HTML",
        )
    text = (
        "Успешно оплачено! Срок вашей подписки истекает "
        f"{current_client.payment_end.strftime(PAYMENT_END_DATE_FORMAT)}.\n\n"
        f"{TEXT_AFTER_FIRST_PAYMENT.format(bot_names[current_client.sending_mode])}"
    )
    if referal_fee:
        text += f"\n{delete_float_point_if_is_not_fraction(referal_fee)} руб. списано с вашего реферального счёта"
        ReferalPaymentsHistory.save(
            ReferalPayment(date.today(), callback.from_user.id, cost)
        )
        save_to_statistics(
            total_referal_commisions=referal_fee,
            total_referal_income=referal_fee,
            new_referal_buyers=not ReferalPaymentsHistory.clientHasPayments(
                callback.from_user.id
            ),
            ref_link=parse_referal_link(referal_link),
        )
    await callback.bot.send_message(callback.from_user.id, text)
    if not had_paid_period_for_current_category:
        try:
            surcharge_kb, surcharge_amount, new_period = (
                get_kb_to_surcharge_extra_days(
                    str(period), category, payment.id, referal_link
                )
            )
            if surcharge_kb:
                difference = get_period_cost_without_sales(
                    new_period, category
                ) - get_period_cost_without_sales(str(period), category)
                text = (
                    f"\n\n<b>{new_period}</b> дн. вместо {period}, "
                    f"доплатив всего <i>{surcharge_amount}</i> руб.! "
                    f"Так переплата бы составила <i>{difference}</i>. Доплату нужно совершить в течении часа."
                )
                text += generate_text_about_oportunity_of_paying_from_ref_bal(
                    callback.from_user.id, surcharge_amount
                )
                await callback.bot.send_message(
                    callback.from_user.id,
                    text,
                    reply_markup=surcharge_kb,
                    parse_mode="HTML",
                )
        except Exception as e:
            logging.error(
                "Failed to offer client surcharging: " + str(e), exc_info=True
            )
    else:
        await callback.bot.send_message(
            current_client.id, "Главное меню", reply_markup=main_kb
        )
    save_to_statistics(
        new_clients=int(not had_paid_period),
        payments_sum=cost,
        new_payments=1,
        new_users=int(not client_id_is_in_db),
        repeated_payments=int(had_paid_period),
        conversions_to_client=int(not had_paid_period and client_id_is_in_db),
        ref_link=parse_referal_link(referal_link),
    )
    date_of_recieveing_latest_messages = user.date_of_recieveing_latest_messages(
        current_client.id
    )
    do_send_latest_messages = False
    if now > last_payment_end:
        if date_of_recieveing_latest_messages == None:
            do_send_latest_messages = True
        elif (now - date_of_recieveing_latest_messages).days >= 2:
            do_send_latest_messages = True
    if do_send_latest_messages:
        await try_to_send_latest_messages(current_client, now - last_payment_end)

async def notify_about_new_payment(
    callback: CallbackQuery,
    mode: int,
    period: int,
    cost: Decimal,
    nick: str,
    referal_fee: Decimal,
):
    await callback.bot.send_message(
        EUGENIY_ID if not TESTING else callback.from_user.id,
        f"{nick} оплатил период по категории {message_category_names[mode]} на {period} дн."
        + (
            f" за {delete_float_point_if_is_not_fraction(cost)} руб."
            if cost
            else ""
        )
        + (
            ""
            if not referal_fee
            else f" (<b>{delete_float_point_if_is_not_fraction(referal_fee)}</b> руб"
            "оплачено с реферального счёта)"
        ),
        parse_mode="HTML",
    )

def get_kb_to_surcharge_extra_days(
    current_period: str, mode: int, payment_id: int, ref_link: str
) -> tuple:
    """return keyboard, amount of excharge and new period"""
    periods = list(payment_period_costs.keys())
    if current_period == periods[0]:
        return None, Decimal(0), ""
    new_period = periods[periods.index(current_period) - 1]
    surcharge_amount = get_period_cost(new_period, mode) - get_period_cost(
        current_period, mode
    )
    surcharge_amount -= surcharge_amount * SALE_FOR_UPSALE
    days_to_expand = days_per_period[new_period] - days_per_period[current_period]
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            "Увеличить период",
            callback_data=CALLBACK_SEP.join(
                [
                    SURCHARGE,
                    str(surcharge_amount),
                    str(days_to_expand),
                    str(current_period),
                    str(mode),
                    str(payment_id),
                    ref_link,
                ]
            ),
        )
    )
    return kb, surcharge_amount, new_period

# @callback_query_handler(# lambda callback: callback.data.startswith(PAY_USING_REFERAL_BALANCE))
handle_pay_using_referal_balance = lambda dp: dp.register_callback_query_handler(pay_using_referal_balance, text_startswith=PAY_USING_REFERAL_BALANCE)
async def pay_using_referal_balance(callback: CallbackQuery, state: FSMContext):
    if not RefClient.has_client_id(callback.from_user.id):
        await callback.answer("У вас не открыт реферальный счёт")
        return
    args = callback.data.split(CALLBACK_SEP)
    _, period, category, cost, with_sale_during_trial, sales, referal_link = args[
        :7
    ]
    requested_from = CALLBACK_SEP.join(args[7:])
    cost = Decimal(cost)
    ref_client = RefClient.get_client_by_id(callback.from_user.id)
    if ref_client.balance == Decimal(0):
        await callback.answer("На вашем реферальном счёте нет средств")
        return
    category = int(category)
    with_sale_during_trial = int(with_sale_during_trial)
    # await States.get_sum_to_withdraw_from_referal_balance_for_payment.set()
    await state.set_state("get_sum_to_withdraw_from_referal_balance_for_payment")
    await callback.bot.send_message(
        callback.from_user.id,
        f"На вашем реферальном балансе {delete_float_point_if_is_not_fraction(ref_client.balance)} руб."
        "\nПришлите сумму, которую хотите выввести с баланса для оплаты подписки.",
    )
    
    await state.update_data(
        with_sale_during_trial=with_sale_during_trial,
        requested_from=requested_from,
        sales=eval("{" + sales + "}"),
        callback=callback,
        category=category,
        period=period,
        cost=cost,
        referal_link=referal_link,
    )

# @dp.message_handler(
#     state=States.get_sum_to_withdraw_from_referal_balance_for_payment
# )
handle_withdraw_ref_balance = lambda dp: dp.register_message_handler(withdraw_ref_balance, state="get_sum_to_withdraw_from_referal_balance_for_payment")
async def withdraw_ref_balance(msg: Message, state: FSMContext):
    try:
        sum = Decimal(msg.text.replace(",", "."))
    except:
        await msg.answer(
            "Введено некоректное значение, попробуйте снова, или отправьте /cancel"
        )
        return
    data = await state.get_data()
    if data["cost"] < sum:
        sum = data["cost"]
        str_sum = delete_float_point_if_is_not_fraction(sum)
        await msg.answer(
            f"Вы ввели большее значение, чем сумма оплаты, с вашего счёта будет списано {str_sum} руб."
        )
    ref_client = RefClient.get_client_by_id(msg.from_user.id)
    if not ref_client:
        await msg.answer("У вас нет реферального счёта")
        await state.finish()
        return
    if ref_client.balance < sum:
        str_balance = delete_float_point_if_is_not_fraction(ref_client.balance)
        await msg.answer(
            f"На вашем реферальном балансе только {str_balance} руб. Введите другую сумму, или /cancel"
        )
        return
    if sum == data["cost"]:
        await state.finish()
        ref_client.balance -= sum
        cur, conn = get_connection_and_cursor()
        ref_client.add_to_db(conn, cur)
        try:
            await process_payment(
                data["callback"],
                data["cost"],
                int(data["period"]),
                data["category"],
                False,
                referal_fee=sum,
            )
        except:
            period = data["period"]
            cost = data["cost"]
            logging.critical(
                f"Failed to save client`s ({ref_client.id}) {period} d. period which costs {cost} using "
                "referal balance:",
                exc_info=True,
            )
    else:
        con, cur = get_connection_and_cursor()
        ref_client.balance -= sum
        ref_client.add_to_db(con, cur)
        try:
            is_allowed_to_pay, text, kb = generate_text_and_keboard_for_payment(
                data["category"],
                data["period"],
                data["cost"] - sum,
                data["sales"],
                msg.from_user.id,
                data["with_sale_during_trial"],
                data["requested_from"],
                data["callback"].msg.message_id,
                data["referal_link"],
                False,
            )
        except:
            logging.critical(
                f"Failed to generate keyboard and text for referal-paying:",
                exc_info=True,
            )
        try:
            await data["callback"].msg.delete()
        except:
            try:
                await data["callback"].msg.edit_text(
                    "Оплатите через клавиатуру снизу"
                    if is_allowed_to_pay
                    else "..."
                )
            except (MessageNotModified, MessageCantBeEdited, MessageTextIsEmpty):
                pass  # it is not critical, because client will have oportunity just to pay without referal-sale
        if not is_allowed_to_pay:
            ref_client.balance += sum
            ref_client.add_to_db(con, cur)
        else:
            text = (
                f"{text}\n(<b>{delete_float_point_if_is_not_fraction(sum)}</b> "
                f"{TEXT_ABOUT_REFERAL_WITHDRAWAL_FOR_PAYMENT}"
            )
        await msg.answer(text, reply_markup=kb, parse_mode="HTML")

# @callback_query_handler(text_startswith=(USE_PROMOCODE_BUTTON), state="*")
handle_get_promocode = lambda dp: dp.register_callback_query_handler(get_promocode, text_startswith=USE_PROMOCODE_BUTTON, state="*")
async def get_promocode(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    admin = get_admin_of_account(callback.from_user.id)
    if admin:
        await callback.answer(
            "Вы не можете оплачивать подписки, "
            f"так как ваш аккаунт подключен к {await get_nick((await callback.bot.get_chat_member(admin, admin)).user)}"
        )
        return
    _, category, promocode = callback.data.split(CALLBACK_SEP)
    if not promocode:
        text = (
            f"Вы выбрали категорию {message_category_names[int(category)]}. "
            "Отправьте промокод (отправьте /cancel для отмены)",
        )
        if callback.message.text == text:
            return
        # await States.get_promocode.set()
        await state.set_state("get_promocode")
        # if promocode is for all categories callback.bot will use chosen category
        await state.update_data(chosen_category=int(category))
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton(
                BACK_BUTTON_TEXT,
                callback_data=CALLBACK_SEP.join([CHOOSE_CATEGORY, category]),
            )
        )
        await callback.bot.edit_message_text(
            text,
            callback.from_user.id,
            callback.message.message_id,
            reply_markup=kb,
        )
    else:
        await check_given_promocode(promocode, int(category), callback.from_user, callback.bot)

# @dp.message_handler(state=States.get_promocode)
handle_get_sent_promocode = lambda dp: dp.register_message_handler(get_sent_promocode, state="get_promocode")
async def get_sent_promocode(msg: Message, state: FSMContext):
    promocode = msg.text.lower()
    chosen_category = (await state.get_data())["chosen_category"]
    await state.finish()
    await check_given_promocode(promocode, chosen_category, msg.from_user, msg.bot)

async def check_given_promocode(
    promocode: str, chosen_category: int, from_user: User, bot
):
    if not promocode_is_in_db(promocode):
        await bot.send_message(
            from_user.id, f'Промокод "{promocode}" не существует'
        )
        return
    pcd_has_been_used = client_used_promocode(from_user.id, promocode)
    pcd_is_endless = promocodes.promocode_is_endless(promocode)
    if not pcd_is_endless and pcd_has_been_used:
        await bot.send_message(
            from_user.id, f'Вы уже использовали промокод "{promocode}"'
        )
        return
    category, trial_extra_days, sale, period, due_time = get_promocode_action(
        promocode
    )
    if category == None:  # all categories
        category = chosen_category
    elif category != chosen_category:
        await bot.send_message(
            from_user.id,
            f"Этот промокод действует на категорию <b>{message_category_names[category]}</b>, не на "
            f"<b>{message_category_names[chosen_category]}</b>.",
            parse_mode="HTML",
        )
        return
    if not period:
        period = "*"
    if not pcd_is_endless and due_time and datetime.now() >= due_time:
        await bot.send_message(from_user.id, "Время действия промокода истекло")
        return
    if not pcd_has_been_used:  # also if it is not endless
        try:
            set_promocode_as_used_by_client(from_user.id, promocode)
        except:
            logging.critical(
                f'Failed to set promocode "{promocode}" as used by {from_user.id}: ',
                exc_info=True,
            )
    promocode_id = get_id_of_promocode(promocode)
    try:
        if trial_extra_days:
            await process_using_trial_promocode(
                promocode, category, trial_extra_days, from_user.id, bot
            )
        elif sale:
            await process_payment_sale_promocode(
                promocode_id, category, sale, str(period), from_user.id, bot
            )
    except:
        logging.critical(
            f'Failed to process promocode "{promocode}" for {from_user.id}: ',
            exc_info=True,
        )
    try:
        process_referal_for_promocode(promocode, from_user.id)
    except Exception as e:
        logging.error(
            f'Failed to check refer of promocode "{promocode}" for {from_user.id}'
        )

async def process_using_trial_promocode(
    promocode: str,
    category: Union[int, None],
    trial_extra_days: int,
    client_id: int,
    bot
):
    client = Client.get_clients_by_filter(id=client_id, category=category)
    now = datetime.now()
    if not client:
        client = Client(
            client_id, now, now + timedelta(days=trial_extra_days), category
        )
        con, cur = get_connection_and_cursor()
        client.add_to_db(con, cur)
    else:
        await bot.send_message(client_id, "Вам больше не доступен пробный период")
        return
    trial_end = now + timedelta(days=trial_extra_days)
    client.set_trial_period(trial_end)
    await bot.send_message(
        client_id,
        f"Вам добавлено <b>{trial_extra_days}</b> дней пробного периода по категории "
        f"<b>{message_category_names[category]}</b>",
        parse_mode="HTML",
    )
    if not Client.did_activate_bot(client):
        await bot.send_message(
            client.id,
            f"Не забудьте активировать бота @{bot_names[client.sending_mode]}",
        )
    save_to_statistics(
        new_users=1, activated_trial=1, trial_activations=1, ref_link=promocode
    )
    user.set_user_as_offered_trial(client_id)
    date_of_recieveing_latest_messages = user.date_of_recieveing_latest_messages(
        client.id
    )
    if (
        not date_of_recieveing_latest_messages
        or (datetime.now() - date_of_recieveing_latest_messages).days >= 2
    ):
        await try_to_send_latest_messages(client)

async def process_payment_sale_promocode(
    promocode_id: int,
    category: int,
    sale: Union[Decimal, float],
    period: str,
    client_id: int,
    bot
):
    sales = {period: sale}
    tariff = (
        f"на тариф <b>{period}</b> дн.\n" if period != "*" else "на все тарифы\n"
    )
    await bot.send_message(
        client_id,
        f"Вы получили <b>{delete_float_point_if_is_not_fraction(sale*100)}%-ю</b> "
        f"скидку по категории <b>{message_category_names[category]}</b> "
        + tariff
        + "(Цены указаны с учётом скидки)",
        reply_markup=get_period_choosing_keyboard(
            category,
            sales=sales,
            from_client=client_id,
            referal_link=f"{PROMOCODE_ID}{promocode_id}",
        ),
        parse_mode="HTML",
    )

def process_referal_for_promocode(promocode: str, user: int):
    refer = get_promocode_refer(promocode)
    if not refer:
        return
    if refer == user:
        return
    if RefClient.has_client_id(user):
        return
    
    con, cur = get_connection_and_cursor()
    referal = RefClient(user, HASNT_REFS, Decimal("0"), refer)
    referal.add_to_db(con, cur)
    refer = RefClient.get_client_by_id(refer)
    if not refer:
        return 
    refer.referal_status = HAS_REFS
    refer.add_to_db(con, cur)

# @dp.message_handler(text= SUBSRIBES_BUTTON, state="*")
handle_get_subscribes_msg = lambda dp: dp.register_message_handler(get_subscribes_msg, text=SUBSRIBES_BUTTON)
async def get_subscribes_msg(msg: Message, state: FSMContext):
    await state.finish()
    text, keyboard = await generate_message_for_subscribes_tab(msg.from_user)
    await msg.reply(
        text,
        reply_markup=keyboard if keyboard.inline_keyboard else None,
        parse_mode="HTML",
    )

async def generate_message_for_subscribes_tab(user: User):
    client = Client.get_client_by_id(user.id)
    text = ""
    now = datetime.now()
    categories = []
    has_paid_periods = False
    for sub in client:
        if sub.payment_end <= now:
            continue
        categories.append(sub.sending_mode)
        mode_name = message_category_names[sub.sending_mode]
        text += f"\t\t{mode_name}: "
        if now.year == sub.last_payment_date.year == sub.payment_end.year:
            text += (
                f'с <b>{sub.last_payment_date.strftime("%d.%m %H:%M")}</b> '
                f'по <b>{sub.payment_end.strftime("%d.%m %H:%M")}</b> '
            )
        else:
            text += (
                f'с <b>{sub.last_payment_date.strftime("%d.%m.%Y %H:%M")}</b> '
                f'по <b>{sub.payment_end.strftime("%d.%m.%Y %H:%M")}</b> '
            )
        is_paid = sub.has_paid_period
        if is_paid:
            has_paid_periods = True
        if not is_paid and sub.is_using_trial:
            text += "(тестовый)"
        unpause_date = sub.unpause_date
        if unpause_date and unpause_date > now:
            text += f'(приостановлено до {unpause_date.strftime("%H:%M %d.%m")}'
            if unpause_date.year != now.year:
                text += f".{unpause_date.year}"
            text += ")"
        text += "\n"
    if not categories:
        text = "У вас нет активных подписок"
    else:
        text = "Ваши подписки:\n" + text
    kb = InlineKeyboardMarkup()
    if len(categories) > 1:
        kb.add(
            InlineKeyboardButton(
                "⏳ Приостановить подписку", callback_data=CHOOSE_SUB_CAT_TO_PAUSE
            )
        )
    elif categories:
        kb.add(
            InlineKeyboardButton(
                "⏳ Приостановить подписку",
                callback_data=CALLBACK_SEP.join(
                    [PAUSE_PERIOD, str(categories[0]), SUBSCRIBES_CALLBACK]
                ),
            )
        )
    if has_paid_periods:
        kb.add(
            InlineKeyboardButton(
                "Перенести клиент на другой акк.", callback_data=TRANSFER_ACCOUNT
            )
        )
    return text, kb

# @callback_query_handler(# lambda callback: callback.data == SUBSCRIBES_CALLBACK, state="*")
handle_get_subscribes = lambda dp: dp.register_callback_query_handler(get_subscribes, text=SUBSCRIBES_CALLBACK, state="*")
async def get_subscribes(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    text, keyboard = await generate_message_for_subscribes_tab(callback.from_user)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

# @callback_query_handler(# lambda callback: callback.data.startswith(CHOOSE_SUB_CAT_TO_PAUSE), state="*")
handle_get_category_to_pause_subscribe = lambda dp: dp.register_callback_query_handler(get_category_to_pause_subscribe, text_startswith=CHOOSE_SUB_CAT_TO_PAUSE, state="*")
async def get_category_to_pause_subscribe(
    callback: CallbackQuery, state: FSMContext
):
    await state.finish()
    now = datetime.now()
    kb = InlineKeyboardMarkup()

    subscriptions = Client.get_client_by_id(callback.from_user.id)
    for sub in subscriptions:
        if sub.payment_end <= now:
            continue

        kb.add(
            InlineKeyboardButton(
                message_category_names[int(sub.sending_mode)],
                callback_data=CALLBACK_SEP.join(
                    [PAUSE_PERIOD, str(sub.sending_mode), callback.data]
                ),
            )
        )
    kb.add(
        InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data=SUBSCRIBES_CALLBACK)
    )
    await callback.message.edit_text(
        text_about_subscribe_pauses + "\n\nВыберите подписку: ", reply_markup=kb
    )

# @callback_query_handler(# lambda callback: callback.data.startswith(PAUSE_PERIOD), state="*")
handle_get_days_to_pause_period = lambda dp: dp.register_callback_query(get_days_to_pause_period, text_startswith=PAUSE_PERIOD, state="*")
async def get_days_to_pause_period(callback: CallbackQuery, state: FSMContext):
    category = int(callback.data.split(CALLBACK_SEP)[1])
    back_button_callback = CALLBACK_SEP.join(callback.data.split(CALLBACK_SEP)[2:])
    client = Client.get_clients_by_filter(
        id=callback.from_user.id, category=category, is_using_trial=False
    )
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data=back_button_callback)
    )
    text = text_about_subscribe_pauses
    if not client or not client[0].has_paid_period:
        text += (
            f"\n\nУ вас нет подписок по категории {message_category_names[category]}, "
            "которые можно поставить на паузу"
        )
        if callback.message.text != text:
            await callback.message.edit_text(text, reply_markup=kb)
        return
    client = client[0]
    current_available_pause_days = client.max_pause_days - client.used_pause_days
    if current_available_pause_days <= 0:
        text += "\n\nВы уже израсходовали максимальное количество дней паузы для текущей подписки"
        if callback.message.text != text:
            await callback.message.edit_text(text, reply_markup=kb)
        return
    
    # await States.get_days_to_set_paused.set()
    await state.set_state("get_days_to_set_paused")
    await state.update_data(category=category)
    text += (
        "\n\nОтправьте количество дней, на которое хотите приостановить "
        f"подписку по категории {message_category_names[category]}. \n"
        f"Сейчас вы можете использовать не более {current_available_pause_days} дн. паузы.\n"
        "(Для отмены операции нажмите /cancel)"
    )
    await callback.message.edit_text(text, reply_markup=kb)

# @dp.message_handler(state=States.get_days_to_set_paused)
handle_pause_period = lambda dp: dp.register_message_handler(pause_period, state="get_days_to_set_paused")
async def pause_period(msg: Message, state: FSMContext):
    if not msg.text.isdigit() or "-" in msg.text:
        await msg.bot.send_message(
            msg.from_user.id, "Не корректное значение, попробуйте ещё раз"
        )
        return
    data = await state.get_data()
    category = data["category"]
    await state.finish()
    client = Client.get_clients_by_filter(
        id=msg.from_user.id, category=category
    )[0]
    day_number = int(msg.text)
    if client.used_pause_days + day_number > client.max_pause_days:
        # await States.get_days_to_set_paused.set()
        await state.set_state("get_days_to_set_paused")
        await state.update_data(category=category)
        await msg.bot.send_message(
            client.id,
            f"Введёное значение слишком большое. Отправьте другое значение, или /cancel",
        )
        return
    try:
        client.increase_used_pause_days(day_number)
        current_unpause_date = client.unpause_date
        if not current_unpause_date:
            current_unpause_date = datetime.now()
        client.unpause_date = current_unpause_date + timedelta(days=day_number)
        client.increase_period(day_number)
    except Exception as e:
        logging.critical(
            f"Failed to increase pause day for {client.id} by {day_number} d.: "
            + str(e),
            exc_info=True,
        )
    else:
        await msg.bot.send_message(
            client.id,
            f'Ваша подписка приостановлена до <b>{client.unpause_date.strftime("%H:%M %d.%m.%Y")}</b>',
            parse_mode="HTML",
        )

# @callback_query_handler(
    # lambda callback: callback.data == TRANSFER_ACCOUNT, state="*"
# )
handle_get_tg_id_to_transfer = lambda dp: dp.register_callback_query_handler(get_tg_id_to_transfer, text=TRANSFER_ACCOUNT, state="*")
async def get_tg_id_to_transfer(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data=SUBSCRIBES_CALLBACK)
    )
    admin = get_admin_of_account(callback.from_user.id)
    if admin:
        try:
            nick = await get_nick(await callback.bot.get_chat_member(admin, admin))
        except:
            nick = admin
        await callback.message.edit_text(
            f"Вы не можете совершить трансфер, так как ваш аккаунт подключен к {nick}",
            parse_mode="HTML",
            reply_markup=kb,
        )
        await state.finish()
        return
    await callback.message.edit_text(
        "Отправьте ID аккаунта, на который хотите выполнить трансфер.\n\n"
        "<u>ID аккаунта - это не ник</u>. Для получения ID-аккаунта нужно запустить @getmyid_bot, бот выдаст вам сообщение \n\n"
        f"ID текущего аккаунта: <b>{callback.from_user.id}</b>\n\n"
        "<b>Учтите</b>: во время этого процесса все ваши подписки и данные будут перенесены на него (но вы всегда "
        "можете откатить это действие)",
        parse_mode="HTML",
        reply_markup=kb,
    )
    # await States.get_tg_id_to_transfer_account.set()
    await state.set_state("get_tg_id_to_transfer_account")

# @dp.message_handler(state=States.get_tg_id_to_transfer_account)
handle_get_confirmation_to_transfer = lambda dp: dp.register_message_handler(get_confirmation_to_transfer, state="get_tg_id_to_transfer_account")
async def get_confirmation_to_transfer(msg: Message, state: FSMContext):
    try:
        new_id = int(msg.text)
    except:
        new_id = -1
    if new_id < 0 or not new_id:
        await msg.answer("Введенно некорректное значение")
        return
    if new_id == msg.from_user.id:
        await msg.answer("Вы ввели свой же ID")
        return
    await state.finish()
    try:
        nick = await get_nick((await msg.bot.get_chat_member(new_id, new_id)).user)
    except:
        nick = new_id
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            "Подтвердить", callback_data=f"{SEND_TRANSFER_CONFIRMATION};{new_id}"
        )
    )
    kb.add(InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data=TRANSFER_ACCOUNT))
    await msg.answer(
        f"Вы хотите перенести все данные на {nick}?"
        + (
            ""
            if isinstance(nick, str)
            else " (не удаётся получить имя аккаунта. Возможно аккаунта с таким "
            "ID не существует, либо на нём не запущен этот бот)"
        ),
        parse_mode="HTML",
        reply_markup=kb,
    )

# @callback_query_handler(
    # lambda callback: callback.data.startswith(SEND_TRANSFER_CONFIRMATION), state="*"
# )
handle_send_validation_to_transfer = lambda dp: dp.register_callback_query_handler(send_validation_to_transfer, text_startswith=SEND_TRANSFER_CONFIRMATION, state="*")
async def send_validation_to_transfer(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    new_id = int(callback.data.split(";")[1])
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            "Подтвердить",
            callback_data=f"{CONFIRM_TRANSFER_SUB};{callback.from_user.id}",
        )
    )
    nick = await get_nick(callback.from_user)
    try:
        msg = await callback.bot.send_message(
            new_id,
            f"{nick} хочет перенести свой клиент на ваш аккаунт.\n"
            "Если вы дадите согласие на трансфер, все ваши текущие подписки и информация об аккаунте "
            f"будут аннулированы и заменены на {nick}. В случае отказа проигнорируйте это сообщение.",
            parse_mode="HTML",
            reply_markup=kb,
        )
    except:
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data=TRANSFER_ACCOUNT)
        )
        await callback.message.edit_text(
            "Не удалось отправить подтверждение на этот аккаунт", reply_markup=kb
        )
        return
    await callback.message.edit_text(
        f"Подтверждение о переносе данных отправленно на {msg.chat.full_name}. "
        'Откройте его и нажмите "Подтвердить", чтобы завершить трансфер.'
    )

# @callback_query_handler(
    # lambda callback: callback.data.startswith(CONFIRM_TRANSFER_SUB), state="*"
# )
handle_transfer_account = lambda dp: dp.register_callback_query_handler(transfer_account, text_startswith=CONFIRM_TRANSFER_SUB, state="*")
async def transfer_account(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    old_id = int(callback.data.split(";")[1])
    new_id = callback.from_user.id
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data=SUBSCRIBES_CALLBACK)
    )
    try:
        nick = await get_nick((await callback.bot.get_chat_member(old_id, old_id)).user)
    except:
        nick = new_id
    await callback.message.edit_text(
        f"Все данные с {nick} полностью перенесенны",
        parse_mode="HTML",
        reply_markup=kb,
    )
    await callback.bot.send_message(
        old_id,
        f"Все данные перенесены на {await get_nick(callback.from_user)}",
        parse_mode="HTML",
    )
    subs = Client.get_client_by_id(old_id)
    for sub in subs:
        try:
            stop_words = StopWords.get_stop_words(sub)
            StopWords.clear_filter(sub)
            StopWords.add_stop_words(sub, stop_words)
        except:
            logging.error("FAILED TO TRANSFER STOP WORDS")
    try:
        Client.change_id_of_client(old_id, new_id)
    except:
        logging.fatal(f"FAILED TO TRANSFER CLIENT:", exc_info=True)
    try:
        transfer_accounts(old_id, new_id)
    except:
        logging.fatal(f"FAILED TO TRANSFER ACCOUNTS:", exc_info=True)
    try:
        PaymentHistory.transferPayings(old_id, new_id)
    except:
        logging.fatal(f"FAILED TO TRANSFER PAYMENTS:", exc_info=True)
    try:
        gsh = GoogleSheets.get_google_sheet_of_client(old_id)
        if gsh:
            GoogleSheets.delete_spread_sheet_of_client(old_id)
            GoogleSheets.delete_spread_sheet_of_client(new_id)
            GoogleSheets.save_google_sheet_to_client(new_id, *gsh)
    except:
        logging.fatal(f"FAILED TO TRANSFER GOOGLE SHEET:", exc_info=True)
    try:
        promocodes.transfer_promocodes_info(old_id, new_id)
    except:
        logging.fatal(f"FAILED TO TRANSFER PROMOCODES INFO:", exc_info=True)
    try:
        RefClient.transfer_ref_info(old_id, new_id)
    except:
        logging.fatal(f"FAILED TO TRANSFER REFERAL INFO:", exc_info=True)
    try:
        Vote.transferVotes(old_id, new_id)
    except:
        logging.error(f"FAILED TO TRANSFER VOTES:", exc_info=True)
    try:
        ReferalPaymentsHistory.transfer_payments(old_id, new_id)
    except:
        logging.error(f"FAILED TO TRANSFER REFERAL PAYMENTS:", exc_info=True)

# @dp.message_handler(
#    lambda msg: msg.text.endswith(TAB_HELPFUL_BUTTON_FOR_NEWBIE), state="*"
# )
handle_get_helpful_tab = lambda dp: dp.register_message_handle(get_helpful_tab, text_endswith=TAB_HELPFUL_BUTTON_FOR_NEWBIE, state="*")
async def get_helpful_tab(msg: Message, state: FSMContext):
    await state.finish()
    await msg.reply("Полезное:", reply_markup=get_kb_for_helpful_tab())

def get_kb_for_helpful_tab():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            "Статья по продажам через бота",
            url="https://vk.com/@golandco-kak-ya-za-2000-rub-poluchil-klientov-po-targetu-na-summu-350",
        )
    )
    kb.add(
        InlineKeyboardButton(
            "Статья с обзором бота",
            url="https://vk.com/@golubin_bot-obzor-servisa-golubin-callback.bot",
        )
    )
    kb.add(InlineKeyboardButton("Информация о боте", callback_data=BOT_INFO))
    return kb

# # @callback_query_handler(
#     lambda call: call.data == TAB_HELPFUL_CALLBACK, state="*"
# )
handle_helpful_tab_callback_handler = lambda dp: dp.register_callback_query_handler(helpful_tab_callback_handler, text=TAB_HELPFUL_CALLBACK, state="*")
async def helpful_tab_callback_handler(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    if callback.message.text == "Полезное:":
        return
    try:
        await callback.bot.edit_message_text(
            "Полезное:",
            callback.from_user.id,
            callback.message.message_id,
            reply_markup=get_kb_for_helpful_tab(),
        )
    except MessageToEditNotFound:
        pass

# @callback_query_handler(lambda call: call.data.startswith(BOT_INFO), state="*")
handler_get_bot_info = lambda dp: dp.register_callback_query_handler(get_bot_info, text_startswith=BOT_INFO, state="*")
async def get_bot_info(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    if callback.message.text == TEXT_ABOUT_BOT:
        return
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("Оформить подписку", callback_data=NEW_ORDER_BUTTON)
    )
    kb.add(
        InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data=TAB_HELPFUL_CALLBACK)
    )
    await callback.bot.edit_message_text(
        TEXT_ABOUT_BOT,
        callback.from_user.id,
        callback.message.message_id,
        reply_markup=kb,
    )

# @callback_query_handler(
    # lambda callback: callback.data.startswith(GET_INFO_ABOUT_BOT_FOR_NEWBIE),
    #        # state="*",
# )
handler_get_info_about_bot = lambda dp: dp.register_callback_query_handler(get_info_about_bot, text_startswith=GET_INFO_ABOUT_BOT_FOR_NEWBIE, state="*")
async def get_info_about_bot(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    if callback.message.text == TEXT_ABOUT_BOT:
        return
    _, requested_from = callback.data.split(CALLBACK_SEP)
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data=requested_from))
    await callback.bot.edit_message_text(
        TEXT_ABOUT_BOT,
        callback.from_user.id,
        callback.message.message_id,
        reply_markup=kb,
    )

# @callback_query_handler(
    # text_startswith=GET_LAST_MSGS_PER_DAY, state="*"
# )
handler_get_category_to_send_last_messages = lambda dp: dp.register_callback_query_handler(get_category_to_send_last_messages, text_startswith=GET_LAST_MSGS_PER_DAY, state="*")
async def get_category_to_send_last_messages(
    callback: CallbackQuery, state: FSMContext
):
    await state.finish()
    admin = get_admin_of_account(callback.from_user.id)
    if admin:
        await callback.answer(
            "Вы не можете выполнить это действие, "
            f"так как ваш аккаунт подключен к {await get_nick((await callback.bot.get_chat_member(admin, admin)).user)}"
        )
        return
    user_id = callback.from_user.id
    mode = int(callback.data.split(CALLBACK_SEP)[1])
    if user.date_of_recieveing_latest_messages(user_id):
        await callback.bot.send_message(user_id, "Вы уже получили заявки")
        return
    client = Client(user_id, None, None, mode)
    try:
        user.set_date_of_recieveing_messages(user_id, datetime.now())
        save_to_statistics(were_got_last_messages=1)
    except Exception as e:
        logging.critical(
            f"Error occured while sending latest  messages to user({user_id}):",
            exc_info=True,
        )
    try:
        await callback.message.delete()
    except:
        pass
    await try_to_send_latest_messages(client)

# @callback_query_handler(
    # lambda callback: callback.data.startswith(KEYBOARD_WITH_ANSWERS), state="*"
# )
handle_set_keybaord_with_answers_why_didnt_by = lambda dp: dp.register_callback_query_handler(set_keybaord_with_answers_why_didnt_by, text_startswith=KEYBOARD_WITH_ANSWERS, state="*")
async def set_keybaord_with_answers_why_didnt_by(
    callback: CallbackQuery, state: FSMContext
):
    await state.finish()
    category = int(callback.data.split(CALLBACK_SEP)[1])
    text = f"Твой тариф по категории {message_category_names[category]} закончился\nПочему не готов оплатить"
    if callback.message.text != text:
        await callback.message.edit_text(
            text,
            reply_markup=kb_with_answers_why_didnt_buy_period(
                category, InlineKeyboardMarkup, InlineKeyboardButton
            ),
        )

# @callback_query_handler(
    # lambda callback: callback.data.startswith(GET_ANSWER_WHY_DIDNT_BUY), state="*"
# )
handle_get_answer_why_didnt_buy = lambda dp: dp.register_callback_query_handler(get_answer_why_didnt_buy, text_startswith=GET_ANSWER_WHY_DIDNT_BUY, state="*")
async def get_answer_why_didnt_buy(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    i, category = callback.data.split(CALLBACK_SEP)[1:]
    i = int(i)
    kb = InlineKeyboardMarkup()
    if i == ANSWER_WITH_ENROLL_IN_COURSE:
        kb.add(
            InlineKeyboardButton(
                "Записаться",
                callback_data=ENROLL_IN_COURSE + CALLBACK_SEP + category,
            )
        )
    elif i == ANSWER_WITH_GET_REPORT:
        kb.add(
            InlineKeyboardButton(
                "Отправить отчёт",
                callback_data=REPORT_ERROR_BUTTON + CALLBACK_SEP + "1",
            )
        )
    elif i == ANSWER_WITH_GET_MESSAGE_TO_DEVELOPER:
        kb.add(
            InlineKeyboardButton(
                "Отправить отчёт",
                callback_data=REPORT_ERROR_BUTTON + CALLBACK_SEP + "2",
            )
        )
    else:
        kb.add(
            InlineKeyboardButton(
                NEW_ORDER,
                callback_data=NEW_ORDER_BUTTON
                + CALLBACK_SEP
                + GET_ANSWER_WHY_DIDNT_BUY,
            )
        )
    answer = list(ANSWERS_WHY_DIDNT_BUY.keys())[i]
    kb.add(
        InlineKeyboardButton(
            BACK_BUTTON_TEXT,
            callback_data=KEYBOARD_WITH_ANSWERS + CALLBACK_SEP + category,
        )
    )
    try:
        await callback.message.edit_text(
            ANSWERS_WHY_DIDNT_BUY[answer], reply_markup=kb
        )
    except (
        MessageNotModified,
        MessageCantBeEdited,
        MessageTextIsEmpty,
        MessageToEditNotFound,
    ):
        pass

# @callback_query_handler(
    # lambda callback: callback.data.startswith(ENROLL_IN_COURSE), state="*"
# )
handle_enroll_client_in_course = lambda dp: dp.register_callback_query_handler(enroll_client_in_course, text_startswith=ENROLL_IN_COURSE, state="*")
async def enroll_client_in_course(callback: CallbackQuery, state: FSMContext):
    have_state = await state.get_state()
    category = callback.data.split(CALLBACK_SEP)[1]
    if have_state:
        try:
            await state.finish()
        except:
            pass
    kb = await SimpleCalendar().start_calendar()
    kb.add(
        InlineKeyboardButton(
            BACK_BUTTON_TEXT,
            callback_data=CALLBACK_SEP.join(
                [
                    GET_ANSWER_WHY_DIDNT_BUY,
                    str(ANSWER_WITH_ENROLL_IN_COURSE),
                    category,
                ]
            ),
        )
    )
    # await States.get_date_of_course.set()
    await state.set_state("get_date_of_course")
    await callback.message.edit_text(
        "Выберите желаемую дату консультации (/cancel для отмены):", reply_markup=kb
    )

# @callback_query_handler(
#     simple_cal_callback.filter(), state=States.get_date_of_course
# )
handle_get_date_of_course = lambda dp: dp.register_callback_query_handler(get_date_of_course, simple_cal_callback.filter(), state="get_date_of_course")
async def get_date_of_course(callback: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(
        callback, callback_data
    )
    if not selected:
        return

    await state.update_data(date=date)
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton(
            "Утро", callback_data=CHOOSE_CONSULTATION_TIME + CALLBACK_SEP + MORNING
        ),
        InlineKeyboardButton(
            "Обед",
            callback_data=CHOOSE_CONSULTATION_TIME + CALLBACK_SEP + HIGH_NOON,
        ),
        InlineKeyboardButton(
            "Вечер", callback_data=CHOOSE_CONSULTATION_TIME + CALLBACK_SEP + EVENING
        ),
    )
    kb.add(InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data=ENROLL_IN_COURSE))
    await callback.message.edit_text(
        "Выберите желаемое время консультации (/cancel для отмены):",
        reply_markup=kb,
    )

# @callback_query_handler(
    # lambda callback: callback.data.startswith(
#         CHOOSE_CONSULTATION_TIME + CALLBACK_SEP
#     ),
#     state=States.get_date_of_course,
# )
handle_choose_time = lambda dp: dp.register_callback_query_handler(choose_time, text_startswith=CHOOSE_CONSULTATION_TIME + CALLBACK_SEP, state="get_date_of_course")
async def choose_time(callback: CallbackQuery, state: FSMContext):
    _, time = callback.data.split(CALLBACK_SEP)
    date = (await state.get_data())["date"]
    await state.finish()
    ym_user = ym_client.account_info()
    label = blake2b(
        (str(datetime.now()) + " " + time + str(callback.from_user.id)).encode(
            "utf-8"
        ),
        digest_size=10,
    ).hexdigest()
    str_date = f'{time} {date.strftime("%d.%m.%Y")}'
    quickpay = Quickpay(
        receiver=ym_user.account,
        quickpay_form="shop",
        targets=f"Запись на консультацию ({str_date}, {consultation_time[time]})",
        paymentType="SB",
        sum=COURSE_PRICE,
        label=label,
    )
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("Оплатить", url=quickpay.redirected_url),
        InlineKeyboardButton(
            "Записаться ✅",
            callback_data=CALLBACK_SEP.join(
                [NOTFIY_ABOUT_NEW_COURSE, label, str_date]
            ),
        ),
    )
    kb.add(InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data=ENROLL_IN_COURSE))
    await callback.message.edit_text(
        f"Вы выбрали консультацию на {str_date}, {consultation_time[time]}",
        reply_markup=kb,
    )

# @callback_query_handler(
    # lambda callback: callback.data.startswith(
    #    NOTFIY_ABOUT_NEW_COURSE + CALLBACK_SEP
    # ),
    #        # state="*",
# )
handle_notify_about_new_consultation = lambda dp: dp.register_callback_query_handler(notify_about_new_consultation, text_startswith=NOTFIY_ABOUT_NEW_COURSE, state="*")
async def notify_about_new_consultation(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    _, label, date = callback.data.split(CALLBACK_SEP)
    history = ym_client.operation_history(label=label)
    if not len(history.operations) and not TESTING:
        await callback.bot.send_message(
            callback.from_user.id,
            "Оплата не была произведена, либо произошла ошибка",
        )
        return
    try:
        await callback.bot.send_message(
            EUGENIY_ID if not TESTING else callback.from_user.id,
            f"{await get_nick(callback.from_user)} оплатил консультацию на {date}.",
        )
    except Exception as e:
        logging.critical(
            f"Failed to notify about new consulation payment from {callback.from_user.id}: "
            + str(e),
            exc_info=True,
        )
    try:
        await callback.message.edit_text(
            f"Спасибо за оплату, в ближайшее время я свяжусь"
            " с тобой в личных сообщениях и мы договоримся о созвоне"
        )
    except Exception as e:
        logging.critical(
            f"Failed to answer new consultation payment: " + str(e), exc_info=True
        )

# @callback_query_handler(
    # lambda callback: callback.data.startswith(SURCHARGE), state="*"
# )
handle_get_surcharge = lambda dp: dp.register_callback_query_handler(get_surcharge, text_startswith=SURCHARGE, state="*")
async def get_surcharge(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    if callback.message.text.startswith("Чтобы расширить ваш период с <b>"):
        return
    if (datetime.now() - callback.message.date).seconds >= SURCHARGE_PERIOD:
        try:
            await callback.message.edit_text("Время доплаты вышло!")
        except (MessageNotModified, MessageToEditNotFound):
            pass
        return
    (
        _,
        surcharge_amount,
        days_to_expand,
        old_period,
        mode,
        payment_id,
        referal_link,
    ) = callback.data.split(CALLBACK_SEP)
    new_period = str(int(days_to_expand) + int(old_period))
    mode = int(mode)
    kb = InlineKeyboardMarkup()
    ym_user = ym_client.account_info()
    label = blake2b(
        (
            str(callback.from_user.id)
            + surcharge_amount
            + days_to_expand
            + str(datetime.now())
            + new_period
        ).encode("utf-8"),
        digest_size=10,
    ).hexdigest()
    quickpay = Quickpay(
        receiver=ym_user.account,
        quickpay_form="shop",
        targets=f"Доплата подписки на Golubin бота до {new_period} дн. по категории {message_category_names[mode]}",
        paymentType="SB",
        sum=float(surcharge_amount),
        label=label,
    )
    kb.row(
        InlineKeyboardButton("Оплатить", url=quickpay.redirected_url),
        InlineKeyboardButton(
            "Готово ✅",
            callback_data=CALLBACK_SEP.join(
                # surcharge amount
                [
                    EXPAND_PERIOD,
                    days_to_expand,
                    str(old_period),
                    label,
                    str(mode),
                    "",
                    "0",
                    payment_id,
                    referal_link,
                ]
            ),
        ),  # is paing_using_referal balance
    )
    kb.add(
        InlineKeyboardButton(
            "Оплатить с реферального счёта",
            callback_data=CALLBACK_SEP.join(
                [
                    EXPAND_PERIOD,
                    days_to_expand,
                    str(old_period),
                    "",
                    str(mode),
                    str(surcharge_amount),
                    "1",
                    payment_id,
                    referal_link,
                ]
            ),
        )
    )
    try:
        await callback.message.edit_text(
            f"Чтобы расширить ваш период с <b>{days_per_period[new_period]-int(days_to_expand)}</b>"
            f" дн. до <b>{new_period}</b>, "
            f'оплатите по ссылке <b>{surcharge_amount}</b> руб., затем нажмите "<b>Готово</b> ✅" на клавиатуре снизу',
            reply_markup=kb,
            parse_mode="HTML",
        )
    except (MessageNotModified, MessageToEditNotFound):
        pass

# @callback_query_handler(
    # lambda callback: callback.data.startswith(EXPAND_PERIOD + CALLBACK_SEP),
    # state="*",
# )
handle_expand_period = lambda dp: dp.register_callback_query_handle(expand_period, text_startswith=EXPAND_PERIOD + CALLBACK_SEP, state="*")
async def expand_period(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    (
        _,
        days_to_expand,
        old_period,
        label,
        category,
        surcharge_amount,
        is_paying_using_ref_balance,
        payment_id,
        ref_link,
    ) = callback.data.split(CALLBACK_SEP)
    is_paying_using_ref_balance = int(is_paying_using_ref_balance)
    days_to_expand = int(days_to_expand)
    new_period = int(old_period) + days_to_expand
    payment_id = int(payment_id)
    if is_paying_using_ref_balance:
        surcharge_amount = Decimal(surcharge_amount)
        if not RefClient.has_client_id(callback.from_user.id):
            await callback.answer("У вас нет реферального счёта")
            return
        ref_client = RefClient.get_client_by_id(callback.from_user.id)
        if ref_client.balance < surcharge_amount:
            await callback.answer("На вашем реферальном счёте недостаточно средств")
            return
    else:
        history = ym_client.operation_history(label=label)
        if not len(history.operations) and not TESTING:
            await callback.bot.send_message(
                callback.from_user.id,
                "Оплата не была произведена, либо произошла ошибка",
            )
            return
        if TESTING:
            surcharge_amount = surcharges[str(new_period)]
        else:
            surcharge_amount = Decimal(str(history.operations[0].amount))
    category = int(category)
    client = await try_to_find_client_to_expand_period(
        callback.from_user, category, days_to_expand, callback.bot
    )
    if not client:
        try:
            await callback.message.edit_text(
                "Не найдена подписка, которую вы хотите расширить. "
                "Обратитесь в тех-поддержку."
            )
        except MessageNotModified:
            pass
        return
    if not await try_to_expand_client_period(
        client, days_to_expand, callback.from_user, callback.bot
    ):
        return
    
    con, cur  = get_connection_and_cursor()
    if is_paying_using_ref_balance:
        ref_client.balance -= surcharge_amount
        ref_client.add_to_db(con, cur)
        ReferalPaymentsHistory.save(
            ReferalPayment(date.today(), callback.from_user.id, surcharge_amount)
        )
        save_to_statistics(
            total_referal_income=surcharge_amount,
            total_referal_commisions=surcharge_amount,
            ref_link=parse_referal_link(ref_link),
        )
    try:
        await callback.message.edit_text(
            "Спасибо за доплату, теперь ваш период заканчивается "
            f'<b>{client.payment_end.strftime("%H:%M %d.%m.%Y")}</b>'
            + (
                ""
                if not is_paying_using_ref_balance
                else f"\n{delete_float_point_if_is_not_fraction(surcharge_amount)} руб. списано с вашего реферального счёта"
            ),
            parse_mode="HTML",
        )
    except MessageNotModified:
        return
    await callback.bot.send_message(
        EUGENIY_ID if not TESTING else callback.from_user.id,
        f"{await get_nick(callback.from_user)} доплатил {delete_float_point_if_is_not_fraction(surcharge_amount)} "
        f"руб., чтобы расширить период на {days_to_expand} дн. (До {new_period} дн.)"
        + (
            ""
            if not is_paying_using_ref_balance
            else "\n(Оплачено с реферального счёта)"
        ),
    )
    commission = 0
    try:
        commission = await process_referal(
            callback.from_user.id, surcharge_amount, callback.bot
        )
    except:
        logging.error(
            f"Process referal for {callback.from_user.id} is failed: ",
            exc_info=True,
        )
    try:
        save_payment_after_expanding_period(
            int(old_period),
            days_to_expand,
            client,
            surcharge_amount,
            payment_id,
            commission,
            ref_link,
        )
    except:
        logging.error(f"Failed to save payment:", exc_info=True)

async def try_to_find_client_to_expand_period(
    user: User, mode: int, days_to_expand: int, bot
) -> Client:
    try:
        client = Client.get_clients_by_filter(id=user.id, category=mode)[0]
    except Exception as e:
        logging.critical(
            f"Failed to find client({user.id}) after surcharging for {days_to_expand} d.: "
            + str(e),
            exc_info=True,
        )
        await bot.send_message(
            DEVELOPER_ID, f"Failed to find {await get_nick(user)} after surcharging"
        )
    return client

async def try_to_expand_client_period(
    client: Client, days_to_expand: int, user: User, bot
) -> bool:
    try:
        client.increase_period(days_to_expand)
    except Exception as e:
        logging.critical(
            f"Failed to expand client`s ({user.id}) period by {days_to_expand} days: "
            + str(e),
            exc_info=True,
        )
        await bot.send_message(
            DEVELOPER_ID,
            f"Failed to expand {await get_nick(user)}`s period by {days_to_expand} days",
        )
        return False
    return True

def save_payment_after_expanding_period(
    old_period: int,
    days_to_expand: int,
    client: Client,
    surcharge_amount: Decimal,
    payment_id: int,
    referal_commision: Decimal,
    referal_link: str,
):
    payment_amount = 0
    comments = IS_UPSALED
    payment = None
    try:
        payment = PaymentHistory.findPaymentsBy(ID=payment_id)
    except Exception as e:
        logging.critical(
            "EXPAND PAYMENT ERROR: failed to find payment while expanding:",
            exc_info=True,
        )
    try:
        if not payment:
            logging.warning(
                "EXPAND PAYMENT ERROR: Can not find payment after expanding period "
                f"(from {old_period} to {int(old_period) + days_to_expand}) for {client.id}"
            )
            payment_amount = {int(v): k for k, v in list(surcharges.items())}[
                int(surcharge_amount)
            ]
        else:
            payment_amount = payment[0].amount
            comments |= payment[0].comments
            try:
                PaymentHistory.deleteSavedPayment(payment[0])
            except Exception as e:
                logging.critical(
                    "EXPAND PAYMENT ERROR: failed to delete payment while expanding:",
                    exc_info=True,
                )
        PaymentHistory.savePayment(
            Payment(
                client.payment_period,
                payment_amount + surcharge_amount,
                payment[0].referal_commission + referal_commision,
                client.id,
                comments=comments,
                category=client.sending_mode,
                referal_link=payment[0].referal_link,
            )
        )
    except:
        logging.critical(
            f"Failed to save payment after expanding period {client.id, surcharge_amount, old_period + days_to_expand}:",
            exc_info=True,
        )
    save_to_statistics(
        payments_sum=surcharge_amount,
        new_payments=1,
        ref_link=parse_referal_link(referal_link),
        total_referal_commisions=referal_commision,
        total_referal_income=referal_commision,
    )

# @dp.message_handler(text= STOP_WORDS, state="*")
handle_stop_words_message = lambda dp: dp.register_message_handler(stop_words_message_handler, text=STOP_WORDS, state="*")
async def stop_words_message_handler(msg: Message, state: FSMContext):
    await state.finish()
    admin = get_admin_of_account(msg.from_user.id)
    if admin:
        await msg.answer(
            "Вы не можете использовать стоп слова, "
            f"так как ваш аккаунт подключен к {await get_nick((await msg.bot.get_chat_member(admin, admin)).user)}"
        )
        return
    kb = get_kb_with_categories(for_callback=GET_CATEGORY_FOR_FILTER)
    await msg.reply("Выберите направление:", reply_markup=kb)

# @callback_query_handler(
    # lambda callback: callback.data == STOP_WORDS_CALLBACK, state="*"
# )
handle_get_category_for_filter = lambda dp: dp.register_callback_query_handler(get_category_for_filter, text=STOP_WORDS_CALLBACK, state="*")
async def get_category_for_filter(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    kb = get_kb_with_categories(for_callback=GET_CATEGORY_FOR_FILTER)
    await callback.message.edit_text("Выберите направление:", reply_markup=kb)

# @callback_query_handler(
    # lambda callback: callback.data.startswith(GET_CATEGORY_FOR_FILTER), state="*"
# )
handle_stop_words = lambda dp: dp.register_callback_query_handler(stop_words, text_startswith=GET_CATEGORY_FOR_FILTER, state="*")
async def stop_words(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    category = callback.data.split(CALLBACK_SEP)[1]
    stop_words_about_text = (
        f"Вы перешли в меню настройки стоп-слов для категории "
        + f"{message_category_names[int(category)]}. Выберите действие:"
    )
    if callback.message.text == stop_words_about_text:
        return
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            "Текущий фильтр",
            callback_data=SHOW_STOP_WORDS + CALLBACK_SEP + category,
        )
    )
    kb.row(
        InlineKeyboardButton(
            "✅ Добавить", callback_data=ADD_STOP_WORDS + CALLBACK_SEP + category
        ),
        InlineKeyboardButton(
            "⛔️ Удалить", callback_data=DELETE_STOP_WORDS + CALLBACK_SEP + category
        ),
    )
    kb.add(
        InlineKeyboardButton(
            "❌ Очистить фильтр",
            callback_data=CLEAR_STOP_WORDS + CALLBACK_SEP + category,
        )
    )
    kb.add(
        InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data=STOP_WORDS_CALLBACK)
    )
    await callback.message.edit_text(stop_words_about_text, reply_markup=kb)

# @callback_query_handler(
    # lambda callback: callback.data.startswith(SHOW_STOP_WORDS), state="*"
# )
handle_show_all_stop_words = lambda dp: dp.register_callback_query_handler(show_all_stop_words, text_startswith=SHOW_STOP_WORDS, state="*")
async def show_all_stop_words(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    category = int(callback.data.split(CALLBACK_SEP)[1])
    client = Client(callback.from_user.id, None, None, category)
    stop_words = StopWords.get_stop_words(client)
    kb = InlineKeyboardMarkup()
    if not stop_words:
        kb.add(
            InlineKeyboardButton(
                "Создать",
                callback_data=ADD_STOP_WORDS + CALLBACK_SEP + str(category),
            )
        )
    kb.add(
        InlineKeyboardButton(
            BACK_BUTTON_TEXT,
            callback_data=GET_CATEGORY_FOR_FILTER + CALLBACK_SEP + str(category),
        )
    )
    if len(stop_words) > 50:
        await callback.bot.send_document(
            client.id, InputFile(StopWords.get_path_to_filter(client), "фильтр.txt")
        )
        await callback.message.edit_text(
            f"{len(stop_words)} слов всего:", reply_markup=kb
        )
        return
    if stop_words and stop_words != [""] and stop_words != [" "]:
        text = ""
        for w in stop_words:
            text += "\t" + w + "\n"
        await callback.message.edit_text(
            "Ваш текущий список стоп-слов: \n" + text, reply_markup=kb
        )
    else:
        await callback.message.edit_text(
            "У вас нет фильтра. Вы можете создать его:", reply_markup=kb
        )

# @callback_query_handler(
    # lambda callback: callback.data.startswith(ADD_STOP_WORDS), state="*"
# )
handle_add_stop_words = lambda dp: dp.register_callback_query_handler(add_stop_words, text_startswith=ADD_STOP_WORDS, state="*")
async def add_stop_words(callback: CallbackQuery, state: FSMContext):
    # await States.get_new_stop_word.set()
    await state.set_state("get_new_stop_word")
    category = int(callback.data.split(CALLBACK_SEP)[1])
    await state.update_data(category=category)
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            BACK_BUTTON_TEXT,
            callback_data=GET_CATEGORY_FOR_FILTER + CALLBACK_SEP + str(category),
        )
    )
    await callback.message.edit_text(
        "Отправьте слово.\n"
        "Если вы хотите добавить несколько слов сразу, то отправьте их одним сообщением,"
        ' разделяя пробелом. Для добавления целой фразы используйте кавычки ("")'
        '\n\nПример:\n\tначинающий помогу научу "только с кейсами"\n\n'
        "(Для отмены действия отправьте <b>/cancel</b>)",
        reply_markup=kb,
        parse_mode="HTML",
    )

# @dp.message_handler(state=States.get_new_stop_word)
handler_get_new_stop_word = lambda dp: dp.regiser_message_handler(get_new_stop_word, state="get_new_stop_word")
async def get_new_stop_word(msg: Message, state: FSMContext):
    category = (await state.get_data())["category"]
    await state.finish()
    client = Client(msg.from_user.id, None, None, category)
    words = get_words_from_text(msg.text)
    StopWords.add_stop_words(client, words)
    len_words = len(words)
    
    # пиздец
    await msg.bot.send_message(
        client.id,
        "Слов"
        + ("o" if len_words == 1 else "а")
        + " добавлен"
        + ("o" if len_words == 1 else "ы")
        + " в ваш фильтр "
        f"категории {message_category_names[category]}",
    )

def get_words_from_text(text: str) -> set:
    words_in_text = text.split()
    words = set()
    current_phraze = []
    for w in words_in_text:
        if w.startswith('"'):
            current_phraze.append(w[1:].lower())
            continue
        if w.endswith('"'):
            current_phraze.append(w[:-1].lower())
            phraze = " ".join(current_phraze)
            words.add(phraze)
            current_phraze = []
            continue
        if not current_phraze:
            words.add(w.lower())
        else:
            current_phraze.append(w.lower())
    return words

# @callback_query_handler(
    # lambda callback: callback.data.startswith(DELETE_STOP_WORDS), state="*"
# )
handle_delete_stop_words = lambda dp: dp.register_callback_query(delete_stop_words, text_startswith=DELETE_STOP_WORDS, state="*")
async def delete_stop_words(callback: CallbackQuery, state: FSMContext):
    # await States.get_stop_word_to_delete.set()
    await state.set_state("get_stop_word_to_delete")
    category = int(callback.data.split(CALLBACK_SEP)[1])
    await state.update_data(category=category)
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            BACK_BUTTON_TEXT,
            callback_data=GET_CATEGORY_FOR_FILTER + CALLBACK_SEP + str(category),
        )
    )
    await callback.message.edit_text(
        "Отправьте слово. Если вы хотите удалить несколько слов сразу, то отправьте их одним сообщением,"
        ' разделяя пробелом. Для удаления фраз отправьте их в кавычках ("")'
        '\n\nПример:\n\tначинающий помогу научу "только с кейсами"\n\n'
        "(Для отмены действия отправьте <b>/cancel</b>)",
        reply_markup=kb,
        parse_mode="HTML",
    )

# @dp.message_handler(state=States.get_stop_word_to_delete)
handle_get_stop_words_to_delete = lambda dp: dp.register_message_handler(get_stop_words_to_delete, state="get_stop_word_to_delete")
async def get_stop_words_to_delete(msg: Message, state: FSMContext):
    category = (await state.get_data())["category"]
    await state.finish()
    words = set(msg.text.split())
    client = Client(msg.from_user.id, None, None, category)
    words = get_words_from_text(msg.text)
    not_deleted = []
    deleted_number = 0
    for w in words:
        try:
            StopWords.delete_stop_word(client, w)
        except ValueError:
            not_deleted.append(w)
        else:
            deleted_number += 1
    text = ""
    if len(words) > 1:
        text = f"{deleted_number} стоп-слов удалено из вашего списка категории {message_category_names[category]}"
        if not_deleted:
            text += "\n\nСлова:\n"
            for w in not_deleted:
                text += "\t" + w + "\n"
            text += "не были найдены в вашем списке."
    else:
        text = (
            f"Слово удалено из вашего списка категории {message_category_names[category]}"
            if not len(not_deleted)
            else "Слово не найдено в вашем списке"
        )
    await msg.bot.send_message(client.id, text)

# @callback_query_handler(
    # lambda callback: callback.data.startswith(CLEAR_STOP_WORDS), state="*"
# )
handle_clear_stop_words = lambda dp: dp.register_callback_query_handler(clear_stop_words, text_startswith=CLEAR_STOP_WORDS, state="*")
async def clear_stop_words(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    category = int(callback.data.split(CALLBACK_SEP)[1])
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            BACK_BUTTON_TEXT,
            callback_data=GET_CATEGORY_FOR_FILTER + CALLBACK_SEP + str(category),
        )
    )
    try:
        StopWords.clear_filter(Client(callback.from_user.id, None, None, category))
    except ValueError:
        await callback.message.edit_text(
            f"Ваш фильтр категории {message_category_names[category]} итак пуст.",
            reply_markup=kb,
        )
    else:
        await callback.message.edit_text(
            "Ваш фильтр категории {message_category_names[category]} очищен.",
            reply_markup=kb,
        )

# @callback_query_handler(
    # lambda callback: callback.data.startswith(WROTE_REVIEW), state="*"
# )
handle_notify_about_new_review = lambda dp: dp.register_callback_query_handler(notify_about_new_review, text_startswith=WROTE_REVIEW, state="*")
async def notify_about_new_review(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    print(callback.data)
    _, category = callback.data.split(CALLBACK_SEP)
    text = f"Ваш отзыв на рассмотрении, в скором времени вам добавят бонусные дни."
    if callback.message.text == text:
        return
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton(
            "1",
            callback_data=CALLBACK_SEP.join(
                [
                    SEND_BONUS_DAYS_FOR_REVIEW,
                    str(callback.from_user.id),
                    category,
                    "1",
                ]
            ),
        ),
        InlineKeyboardButton(
            "3",
            callback_data=CALLBACK_SEP.join(
                [
                    SEND_BONUS_DAYS_FOR_REVIEW,
                    str(callback.from_user.id),
                    category,
                    "3",
                ]
            ),
        ),
        InlineKeyboardButton(
            "7",
            callback_data=CALLBACK_SEP.join(
                [
                    SEND_BONUS_DAYS_FOR_REVIEW,
                    str(callback.from_user.id),
                    category,
                    "7",
                ]
            ),
        ),
    )
    kb.add(
        InlineKeyboardButton(
            f"Отзыв не найден",
            callback_data=CALLBACK_SEP.join(
                [str(MARK_REVIEW_AS_FAKE), str(callback.from_user.id), category]
            ),
        )
    )
    try:
        await callback.bot.send_message(
            EUGENIY_ID,
            f"{await get_nick(callback.from_user)} написал отзыв. Сколько выдать доп. дней?",
            reply_markup=kb,
            parse_mode="HTML",
        )
        await callback.message.edit_text(text)
    except (MessageNotModified, MessageToEditNotFound):
        pass
    except Exception as e:
        logging.error(
            f"Failed to notify about new review from {callback.from_user.id}: "
            + str(e),
            exc_info=True,
        )

# @callback_query_handler(
    # lambda callback: callback.data.startswith(SEND_BONUS_DAYS_FOR_REVIEW), state="*"
# )
handle_send_sale_for_review = lambda dp: dp.register_callback_query_handler(send_sale_for_review, text_startswith=SEND_BONUS_DAYS_FOR_REVIEW, state="*")
async def send_sale_for_review(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    _, user_id, category, bonus_days = callback.data.split(CALLBACK_SEP)
    user_id = int(user_id)
    category = int(category)
    bonus_days = int(bonus_days)
    client = Client.get_clients_by_filter(id=user_id, category=category)[0]
    now = datetime.now()
    trial_end = client.trial_period_end
    if trial_end and trial_end > now:
        trial_end += timedelta(days=bonus_days)
        client.set_trial_period(trial_end)
    if client.payment_end < now:
        client.payment_end = now + timedelta(days=bonus_days)
        con, cur = get_connection_and_cursor()
        client.add_to_db(con, cur)
    else:
        client.increase_period(bonus_days)
    str_payment_end = client.payment_end.strftime("<b>%d.%m.%Y</b>")
    await callback.bot.send_message(
        user_id,
        f"Ваш период по категории {message_category_names[category]} за отзыв расширен"
        f" на {bonus_days} дней (До {str_payment_end}).",
        parse_mode="HTML",
    )
    await callback.message.edit_text(f"Пробные {bonus_days} дн. отправлены")

# @callback_query_handler(
    # lambda callback: callback.data.startswith(MARK_REVIEW_AS_FAKE), state="*"
# )
handle_send_message_to_liar = lambda dp: dp.register_callback_query_handler(send_message_to_liar, text_startswith=MARK_REVIEW_AS_FAKE, state="*")
async def send_message_to_liar(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    _, user_id, category = callback.data.split(CALLBACK_SEP)
    user_id = int(user_id)
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            "Написал", callback_data=CALLBACK_SEP.join([WROTE_REVIEW, category])
        )
    )
    await callback.bot.send_message(
        user_id,
        "Мы не смогли найти ваш отзыв. Пожалуйста, оставьте свой ник в комментарии, "
        "чтобы мы смогли определить ваш аккаунт.\n\n" + URL_WITH_REVIEWS,
        reply_markup=kb,
    )
    await callback.message.edit_text(
        "Ссылка на отзыв повторно отправлена пользователю"
    )

# @dp.message_handler(text= POST_APPLICATION, state="*")
handle_get_category_of_application = lambda dp: dp.register_message_handler(get_category_of_application, text=POST_APPLICATION, state="*")
async def get_category_of_application(msg: Message, state: FSMContext):
    await state.finish()
    admin = get_admin_of_account(msg.from_user.id)
    if admin:
        await msg.answer(
            "Вы не можете выкладывать заявки, "
            f"так как ваш аккаунт подключен к {await get_nick((await msg.bot.get_chat_member(admin, admin)).user)}"
        )
        return
    str_user_id = str(msg.from_user.id)
    client_has_already_sent_app_to_check = await check_if_client_sended_application_sooner(
        str_user_id,
        lambda keyboard: msg.reply(
            "Дождитесь окончания проверки вашей прошлой заявки, прежде чем отправлять новую.",
            reply_markup=keyboard,
        ),
    )
    if not client_has_already_sent_app_to_check:
        kb = get_kb_with_categories(
            for_callback=GET_CATEGORY_OF_POST,
            text_for_back_button=POST_APPLICATION_CALLBACK,
        )
        await msg.reply("Выберите категорию вашей заявки:", reply_markup=kb)


async def check_if_client_sended_application_sooner(
    str_user_id: str,
    send_message_to_client_about_having_recent_app: types.FunctionType,
) -> Union[bool, str]:
    for category in listdir(APPLICATIONS_FROM_USERS_DIR):
        for file in listdir(APPLICATIONS_FROM_USERS_DIR + "/" + category):
            if file.startswith(str_user_id):
                msgc = {v: k for k, v in msg_categories.items()}
                kb = InlineKeyboardMarkup()
                kb.add(
                    InlineKeyboardButton(
                        "отменить проверку",
                        callback_data=CALLBACK_SEP.join(
                            [DENY_CHECK_APPLICATION, file, str(msgc[category])]
                        ),
                    )
                )
                try:
                    await send_message_to_client_about_having_recent_app(kb)
                except Exception as e:
                    logging.exception(
                        "Exception occured while answering to clinet that he has "
                        "already sent application to check:",
                        exc_info=True,
                    )
                return True
    return False

# @callback_query_handler(
    # lambda callback: callback.data == POST_APPLICATION_CALLBACK, state="*"
# )
handle_get_category_of_application_callback = lambda dp: dp.register_callback_query_handler(get_category_of_application_callback_handler, text=POST_APPLICATION_CALLBACK, state="*")
async def get_category_of_application_callback_handler(
    callback: CallbackQuery, state: FSMContext
):
    await state.finish()
    str_user_id = str(callback.from_user.id)
    client_has_already_sent_app_to_check = await check_if_client_sended_application_sooner(
        str_user_id,
        lambda keybaord: callback.message.edit_text(
            "Дождитесь окончания проверки вашей прошлой заявки, прежде чем отправлять новую.",
            reply_markup=keybaord,
        ),
    )
    if not client_has_already_sent_app_to_check:
        kb = get_kb_with_categories(
            for_callback=GET_CATEGORY_OF_POST,
            text_for_back_button=POST_APPLICATION_CALLBACK,
        )
        await callback.message.edit_text(
            "Выберите категорию вашей заявки:", reply_markup=kb
        )

# @callback_query_handler(
    # lambda callback: callback.data.startswith(GET_CATEGORY_OF_POST), state="*"
# ) 
handle_get_application_to_post = lambda dp: dp.register_callback_query_handler(get_application_to_post, text_startswith=GET_CATEGORY_OF_POST, state="*")
async def get_application_to_post(callback: CallbackQuery, state: FSMContext):
    category = int(callback.data.split(CALLBACK_SEP)[1])
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            BACK_BUTTON_TEXT, callback_data=POST_APPLICATION_CALLBACK
        )
    )
    # await States.get_application_to_post.set()
    await state.set_state("get_application_to_post")
    await state.update_data(category=category)
    try:
        await callback.message.edit_text(
            f"Вы выбрали категорию {message_category_names[category]}. Теперь пришлите вашу заявку, "
            "мы выложим её в нашем боте после проверки модераторами. "
            "<b>ВАЖНО!</b> Мы не публикуем рекламные посты про специалиста; если вы ищете клиентов, то активируйте "
            "бота и получайте заявки. Объявления по типу: <i>Я таргетолог</i>, "
            "<i>помогу настроить рекламу</i> и тому подобное не публикуются!"
            "\n(/cancel для отмены)",
            reply_markup=kb,
            parse_mode="HTML",
        )
    except:
        pass

# @dp.message_handler(state=States.get_application_to_post)
handle_send_new_application_to_admin = lambda dp: dp.register_message_handler(send_new_application_to_admin, state="get_application_to_post")
async def send_new_application_to_admin(msg: Message, state: FSMContext):
    category = int((await state.get_data())["category"])
    await state.finish()
    kb = InlineKeyboardMarkup()
    file_name = str(msg.from_user.id) + " " + str(msg.message_id)
    with open(
        APPLICATIONS_FROM_USERS_DIR
        + "/"
        + msg_categories[category]
        + "/"
        + file_name,
        "w",
    ) as file:
        file.write(msg.text + "\n 👉 " + (await get_nick(msg.from_user)))
    kb.row(
        InlineKeyboardButton(
            "Подтвердить",
            callback_data=CALLBACK_SEP.join(
                [CONFIRM_CHECK_APPLICATION, str(msg.message_id), str(category)]
            ),
        ),
        InlineKeyboardButton(
            "Отменить",
            callback_data=CALLBACK_SEP.join(
                [DENY_CHECK_APPLICATION, file_name, str(category)]
            ),
        ),
    )
    await msg.bot.send_message(
        msg.from_user.id,
        "Вы уверены, что хотите разместить эту заявку?",
        reply_markup=kb,
    )

# @callback_query_handler(
    # lambda callback: callback.data.startswith(DENY_CHECK_APPLICATION), state="*"
# )
handle_deny_send_application = lambda dp: dp.register_callback_handler(deny_send_application, text_startswith=DENY_CHECK_APPLICATION,state="*")
async def deny_send_application(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    cancel_check_text = "Размещение заявки отменено"
    if callback.message.text == cancel_check_text:
        return
    _, file_name, category = callback.data.split(CALLBACK_SEP)
    category = int(category)
    try:
        remove(
            APPLICATIONS_FROM_USERS_DIR
            + "/"
            + msg_categories[category]
            + "/"
            + file_name
        )
    except FileNotFoundError:
        return  # user already has deleted his own application
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            "Отправить другую заявку", callback_data=POST_APPLICATION_CALLBACK
        )
    )
    await callback.message.edit_text(cancel_check_text, reply_markup=kb)

# @callback_query_handler(
    # lambda callback: callback.data.startswith(CONFIRM_CHECK_APPLICATION), state="*"
# )
handle_check_new_application = lambda dp: dp.register_callback_query_handler(check_new_application, text_startswith=CONFIRM_CHECK_APPLICATION, state="*")
async def check_new_application(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    final_text = "Ваша заявка находится на рассмотрении."
    if callback.message.text == final_text:
        return
    _, message_id, category = callback.data.split(CALLBACK_SEP)
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton(
            "Да",
            callback_data=CALLBACK_SEP.join(
                [
                    ALLOW_APPLICATION,
                    str(callback.from_user.id),
                    message_id,
                    category,
                ]
            ),
        ),
        InlineKeyboardButton(
            "Нет",
            callback_data=CALLBACK_SEP.join(
                [
                    DECLINE_APPLICATION,
                    str(callback.from_user.id),
                    message_id,
                    category,
                ]
            ),
        ),
    )
    admin_id = callback.from_user.id if TESTING else EUGENIY_ID
    await callback.bot.send_message(
        admin_id,
        "Запрос на размещение заявки по категории "
        f"<b>{message_category_names[int(category)]}</b>:",
        parse_mode="HTML",
    )
    await callback.bot.forward_message(
        admin_id, callback.from_user.id, message_id, disable_notification=True
    )
    await callback.bot.send_message(
        admin_id, "Разместить заявку?", reply_markup=kb, disable_notification=True
    )
    try:
        await callback.message.edit_text(final_text)
    except:
        return

# @callback_query_handler(
    # lambda callback: callback.data.startswith(ALLOW_APPLICATION), state="*"
# )
handle_post_application = lambda dp: dp.register_callback_query_handler(post_application, text_startswith=ALLOW_APPLICATION, state="*")
async def post_application(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    final_text = "Заявка отправлена"
    if callback.message.text == final_text:
        return
    print("STARTED TO SEND APPLICATION FROM CLIENT")
    _, user_id, message_id, category = callback.data.split(CALLBACK_SEP)
    file_name = user_id + " " + message_id
    user_id = int(user_id)
    category = int(category)
    message_id = int(message_id)
    try:
        msg_path = (
            (NEW_MESSAGES_PATH if not TESTING else TEMP_MESSAGES_PATH)
            + "/"
            + msg_categories[category]
            + "/"
            + file_name
            + " "
            + datetime.now().strftime("%m_%d_$H_%M")
        )
        mkdir(msg_path)
        move(
            APPLICATIONS_FROM_USERS_DIR
            + "/"
            + msg_categories[category]
            + "/"
            + file_name,
            msg_path + "/" + TEXT_INFO,
        )
    except FileNotFoundError:
        await callback.message.edit_text("Заявка уже была отмененна пользователем")
    except Exception as e:
        text = (
            f'Failed to save to send application from {user_id}-"{file_name}": '
            + str(e)
        )
        logging.critical(text, exc_info=True)
        await callback.bot.send_message(DEVELOPER_ID, text)
        await callback.bot.forward_message(DEVELOPER_ID, user_id, message_id)
    else:
        await callback.bot.send_message(
            user_id,
            "Поздравляем, ваша заявка была одобрена администраторами!",
            reply_to_message_id=message_id,
        )
        await callback.message.edit_text(final_text)

# @callback_query_handler(
    # lambda callback: callback.data.startswith(DECLINE_APPLICATION), state="*"
# )
handle_ask_coment_about_application_refusal = lambda dp: dp.register_callback_query_handler(ask_coment_about_application_refusal, text_startswith=DECLINE_APPLICATION, state="*")
async def ask_coment_about_application_refusal(
    callback: CallbackQuery, state: FSMContext
):
    await state.finish()
    if callback.message.text == TEXT_AFTER_RFUSAL_OF_CLIENTS_APPLICATION:
        return
    _, user_id, message_id, category = callback.data.split(CALLBACK_SEP)
    file_name = user_id + " " + message_id
    user_id = int(user_id)
    category = int(category)
    source_message_id = int(message_id)
    try:
        remove(
            APPLICATIONS_FROM_USERS_DIR
            + "/"
            + msg_categories[category]
            + "/"
            + file_name
        )
    except Exception as e:
        text = f'Failed to remove application from {user_id}-"{file_name}": ' + str(
            e
        )
        logging.critical(text, exc_info=True)
    else:
        await generate_message_to_send_comment_about_refusal(
            callback, user_id, source_message_id
        )

async def generate_message_to_send_comment_about_refusal(
    callback: CallbackQuery, to_user: int, to_message_id: int
):
    kb = InlineKeyboardMarkup()
    for i in range(len(comments_about_refusal)):
        kb.add(
            InlineKeyboardButton(
                comments_about_refusal[i],
                callback_data=CALLBACK_SEP.join(
                    [
                        ATTACH_COMMENT_ABOUT_APP_REFUSAL,
                        str(i),
                        str(to_user),
                        str(to_message_id),
                    ]
                ),
            )
        )
    try:
        await callback.message.edit_text(
            TEXT_AFTER_RFUSAL_OF_CLIENTS_APPLICATION, reply_markup=kb
        )
    except (MessageNotModified, MessageCantBeEdited, MessageTextIsEmpty):
        pass

# @callback_query_handler(
    # lambda callback: callback.data.startswith(
    #    GET_BACK_TO_CHOOSING_COMMENT_ABOUT_REFUSAL
    # ),
    #        # state="*",
# )
handle_gen_msg_to_send_comment_again = lambda dp: dp.register_callback_query_handler(gen_msg_to_send_comment_again, text_startswith=GET_BACK_TO_CHOOSING_COMMENT_ABOUT_REFUSAL)
async def gen_msg_to_send_comment_again(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    _, to_user_id, to_message_id = callback.data.split(CALLBACK_SEP)
    await generate_message_to_send_comment_about_refusal(
        callback, int(to_user_id), int(to_message_id)
    )

# @callback_query_handler(
    # lambda call: call.data.startswith(ATTACH_COMMENT_ABOUT_APP_REFUSAL), state="*"
# )
handle_decline_application_from_client = lambda dp: dp.register_callback_query_handler(decline_application_from_client, text_startswith=ATTACH_COMMENT_ABOUT_APP_REFUSAL, state="*")
async def decline_application_from_client(
    callback: CallbackQuery, state: FSMContext
):
    await state.finish()
    _, comment_index, to_user, to_message_id = callback.data.split(CALLBACK_SEP)
    comment_index, to_user, to_message_id = [
        int(i) for i in (comment_index, to_user, to_message_id)
    ]
    # not the last variant of comment (where admin have to write it's own comment)
    if comment_index != len(comments_about_refusal) - 1:
        await callback.bot.send_message(
            to_user,
            f"Ваше объявление "
            "отклонено. Причина отклонения: "
            + comments_about_refusal[comment_index],
            reply_to_message_id=to_message_id,
        )
        try:
            await callback.message.edit_text(
                "Заявка удалена. сообщение об этом отправлено клиенту."
            )
        except (MessageNotModified, MessageCantBeEdited, MessageTextIsEmpty):
            pass
    else:
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton(
                BACK_BUTTON_TEXT,
                callback_data=CALLBACK_SEP.join(
                    [
                        GET_BACK_TO_CHOOSING_COMMENT_ABOUT_REFUSAL,
                        str(to_user),
                        str(to_message_id),
                    ]
                ),
            )
        )
        try:
            await callback.message.edit_text(
                "Отправьте комментарий, объясняющий причину отмены заявки: ",
                reply_markup=kb,
            )
        except (MessageNotModified, MessageCantBeEdited, MessageTextIsEmpty):
            pass
        else:
            # await States.get_comment_about_refusal.set()
            await state.set_state("get_comment_about_refusal")
            await state.update_data(to_user=to_user, to_message_id=to_message_id)

# @dp.message_handler(state=States.get_comment_about_refusal)
handle_ask_to_confirm_specifical_comment_about_refusal_of_application = lambda dp: dp.register_message_handler(ask_to_confirm_specifical_comment_about_refusal_of_application, )
async def ask_to_confirm_specifical_comment_about_refusal_of_application(
    msg: Message, state: FSMContext
):
    await state.update_data(msg=msg.text)
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton(
            "Да", callback_data=CONFIRM_SENDING_COMMENT_ABOUT_REFUSAL
        ),
        InlineKeyboardButton(
            "Нет", callback_data=DECLINE_SENDING_COMMENT_ABOUT_REFUSAL
        ),
    )
    await msg.bot.send_message(
        msg.from_user.id,
        "Вы уверены, что хотите отправить пользователю этот комментарий?",
        reply_markup=kb,
    )

# @callback_query_handler(
    # lambda callback: callback.data == DECLINE_SENDING_COMMENT_ABOUT_REFUSAL,
    # state=States.get_comment_about_refusal,
# )
handle_decline_to_send_comment_about_refusal_of_application = lambda dp: dp.register_callback_query_handler(decline_to_send_comment_about_refusal_of_application, text=DECLINE_SENDING_COMMENT_ABOUT_REFUSAL, state="get_comment_about_refusal")
async def decline_to_send_comment_about_refusal_of_application(
    callback: CallbackQuery,
):
    try:
        await callback.message.edit_text("Отправьте новый комментарий")
    except (MessageNotModified, MessageCantBeEdited, MessageTextIsEmpty):
        pass

# @callback_query_handler(
    # lambda callback: callback.data == CONFIRM_SENDING_COMMENT_ABOUT_REFUSAL,
    # state=States.get_comment_about_refusal,
# )
handle_send_specific_comment_about_application_refusal = lambda dp: dp.register_callback_query_handler(send_specific_comment_about_application_refusal, text=CONFIRM_SENDING_COMMENT_ABOUT_REFUSAL, state="get_comment_about_refusal")
async def send_specific_comment_about_application_refusal(
    callback: CallbackQuery, state: FSMContext
):
    data = await state.get_data()
    await state.finish()
    await callback.bot.send_message(
        data["to_user"],
        f"Ваше объявление " "отклонено. Причина отклонения: " + data["msg"],
        reply_to_message_id=data["to_message_id"],
    )
    try:
        await callback.message.edit_text("Сообщение об отмене заявки отправлено.")
    except (MessageNotModified, MessageCantBeEdited, MessageTextIsEmpty):
        pass

# @dp.message_handler(text= ADS, state="*")
handle_buy_ad = lambda dp: dp.register_message_handler(buy_ad, text=ADS, state="*") 
async def buy_ad(msg: Message, state: FSMContext):
    await state.finish()
    await msg.answer(
        "Вы можете узнать актуальные цены на рекламу в боте через https://t.me/+2Grf99Dpkf4zM2Zi"
    )

# @dp.message_handler(text= BUY_NEW_CATEGORY, state="*")
handle_buy_new_category = lambda dp: dp.register_message_handler(buy_new_category, text=BUY_NEW_CATEGORY, state="*")
async def buy_new_category(msg: Message, state: FSMContext):
    await state.finish()
    await msg.answer(
        'Если твоего направления нет в "Категории заявок", то можешь его заказать. '
        "Стоимость 5000 руб, это предоплата за 3 месяца работы бота. Запуск в течение недели. "
        "Если все устраивает пиши свое направление мне в лс @COJ_ZhIV"
    )

# @dp.message_handler(text= PARTNER_SHOWCASE, state="*")
handle_partner_showcase = lambda dp: dp.register_message_handler(partner_showcase, text=PARTNER_SHOWCASE, state="*")
async def partner_showcase(msg: Message, state: FSMContext):
    await state.finish()
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            "Vitamin",
            url="https://vitamin.tools/?ref2=542a6907-a190-4ab5-8dea-7726b6e8fc3e",
        )
    )
    await msg.answer(
        "Vitamin\n\n"
        "До 20% с рекламного бюджета. Начисляется сразу при переводе на рекламные "
        "кабинеты и независимо от объемов, сразу максимальная ставка",
        reply_markup=kb,
    )

# @dp.message_handler(text= REPORT_ERROR, state="*")
handle_report_error = lambda dp: dp.register_message_handler(report_error_handler, text=REPORT_ERROR, state="*")
async def report_error_handler(msg: Message, state: FSMContext):
    if msg.text in [
        NEW_ORDER,
        NEW_ORDER_FOR_NEWBIE,
        PERSONAL_CABINET,
        ADDITIONAL_OPTIONS,
        SUBSRIBES_BUTTON,
        TAB_HELPFUL_BUTTON,
        ADD_EXTERNAL_CHAT,
        BUY_NEW_CATEGORY,
        PARTNER_SHOWCASE,
        ADS,
        POST_APPLICATION,
    ]:
        await state.finish()
        try:
            await msg.bot.send_message(msg.from_user.id, "Операция отменена")
        except:
            pass
        # ай донт кноу как это решить иначе
        return

    await state.finish()
    await report_error(
        msg.from_user.id, 0,
        state, msg.bot
    )  # 0 is index in list with replies to reports

async def report_error(user_id: int, type: int, state, bot):
    # await States.get_report.set()
    await state.set_state("get_report")
    await state.update_data(report_type=type)
    await bot.send_message(
        user_id,
        "Опишите возникшую проблему одним сообщением (или отправьте /cancel для отмены)",
    )

# @callback_query_handler(
#    text_startswith=(REPORT_ERROR_BUTTON + CALLBACK_SEP), state="*"
#)
handle_report_error = lambda dp: dp.register_callback_query_handler(report_error_callback, text_startswith=REPORT_ERROR_BUTTON + CALLBACK_SEP, state="*")
async def report_error_callback(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    report_type = int(callback.data.split(CALLBACK_SEP)[1])
    await report_error(callback.from_user.id, report_type, state, callback.bot)

# @dp.message_handler(state=States.get_report)
handle_message_handler = lambda dp: dp.register_message_handler(message_handler, state="get_report")
async def message_handler(msg: Message, state: FSMContext):
    report_type = (await state.get_data())["report_type"]
    await state.finish()
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            "Ответить",
            callback_data=REPLY_TO_USER + CALLBACK_SEP + str(msg.from_user.id),
        )
    )
    await msg.bot.send_message(
        msg.from_user.id,
        "Спасибо за ваше сообщение, в ближайшее время мы вам ответим",
    )
    for id in (
        (DEVELOPER_ID, EUGENIY_ID) if not TESTING else (msg.from_user.id,)
    ):
        username = ""
        if msg.from_user.username:
            username = f"@{msg.from_user.username}"
        text = (
            (f"{username}\n" if username else "")
            + f"({msg.from_user.id}) "
            + DESCIPTIONS_ABOUT_REPORT[report_type]
        )
        await msg.bot.send_message(id, text)
        await msg.bot.forward_message(id, msg.chat.id, msg.message_id)
        await msg.bot.send_message(id, "_", reply_markup=kb)

# @callback_query_handler(
    # lambda callback: callback.data.startswith(REPLY_TO_USER), state="*"
# )
handle_reply_to_users_report = lambda dp: dp.register_callback_query_handler(reply_to_users_report, text_startswith=REPLY_TO_USER, state="*")
async def reply_to_users_report(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    user_id = int(callback.data.split(CALLBACK_SEP)[1])
    # await States.get_answer.set()
    await state.set_state("get_answer")
    await state.update_data(to_admin=False, to_user=user_id)
    kb = callback.message.reply_markup
    await callback.message.edit_text(
        (callback.message.text if callback.message.text else "")
        + "\nОтправьте ответ:",
        reply_markup=kb,
    )

# @dp.message_handler(state=States.get_answer)
handle_get_answer = lambda dp: dp.register_message_handler(get_answer, state="get_answer")
async def get_answer(msg: Message, state: FSMContext):
    data = await state.get_data()
    await state.finish()
    to_admin = data["to_admin"]
    user_id = data["to_user"]
    kb = InlineKeyboardMarkup()
    if to_admin:
        kb.add(
            InlineKeyboardButton(
                "Ответить",
                callback_data=REPLY_TO_USER + CALLBACK_SEP + str(user_id),
            )
        )
        for id in (
            (msg.from_user.id,) if TESTING else (DEVELOPER_ID, EUGENIY_ID)
        ):
            await msg.bot.forward_message(id, msg.from_user.id, msg.message_id)
            await msg.bot.send_message(id, "_", reply_markup=kb)
    else:
        kb.add(
            InlineKeyboardButton(
                "Ответить",
                callback_data=REPLY_TO_ADMIN + CALLBACK_SEP + str(user_id),
            )
        )
        try:
            await msg.bot.send_message(user_id, msg.text, reply_markup=kb)
        except:
            await msg.answer("Не удаётся отправить ответ пользователю")
            return
    await msg.answer("Ответ отправлен")

# @callback_query_handler(
    # lambda callback: callback.data.startswith(REPLY_TO_ADMIN), state="*"
# )
handle_reply_to_admin = lambda dp: dp.register_callback_query_handler(reply_to_admin, text_startswith=REPLY_TO_ADMIN, state="*")
async def reply_to_admin(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    admin_id = int(callback.data.split(CALLBACK_SEP)[1])
    await state.set_state("get_answer")
    # await States.get_answer.set()
    await state.update_data(to_admin=True, to_user=admin_id)
    kb = callback.message.reply_markup
    if callback.message.text is None:
        callback.message.text = ""
    await callback.message.edit_text(
        callback.message.text + "\nОтправьте ответ:", reply_markup=kb
    )


def register_handler(dp):
    handle_add_stop_words(dp)
    handle_additional_optionals(dp)
    handle_ask_coment_about_application_refusal(dp)
    handle_ask_to_confirm_specifical_comment_about_refusal_of_application(dp)
    handle_back_to_period_choosing(dp)
    handle_buy_ad(dp)
    handle_buy_new_category(dp)
    handle_check_new_application(dp)
    handle_choose_order_category(dp)
    handle_choose_time(dp)
    handle_clear_stop_words(dp)
    handle_decline_application_from_client(dp)
    handle_decline_to_send_comment_about_refusal_of_application(dp)
    handle_delete_stop_words(dp)
    handle_expand_period(dp)
    handle_deny_send_application(dp)
    handle_enroll_client_in_course(dp)
    handle_expand_period(dp)
    handle_gen_msg_to_send_comment_again(dp)
    handle_get_answer(dp)
    handle_get_answer_why_didnt_buy(dp)
    handle_get_application_to_post(dp)
    handle_get_category_for_filter(dp)
    handle_get_category_of_application(dp)
    handle_get_category_of_application_callback(dp)
    handle_get_category_to_pause_subscribe(dp)
    handle_get_confirmation_to_transfer(dp)
    handle_get_date_of_course(dp)
    handle_get_days_to_pause_period(dp)
    handle_get_helpful_tab(dp)
    handle_get_promocode(dp)
    handle_get_sent_promocode(dp)
    handle_get_stop_words_to_delete(dp)
    handle_get_subscribes(dp)
    handle_get_subscribes_msg(dp)
    handle_get_subscribes(dp)
    handle_get_tg_id_to_transfer(dp)
    handle_helpful_tab_callback_handler(dp)
    handle_main_menu(dp)
    handle_make_trial(dp)
    handle_message_handler(dp)
    handle_new_order_callback(dp)
    handle_new_order(dp)
    handle_notify_about_new_consultation(dp)
    handle_notify_about_new_review(dp)
    handle_partner_showcase(dp)
    handle_pause_period(dp)
    handle_pay(dp)
    handle_pay_using_referal_balance(dp)
    handle_personal_panel(dp)
    handle_post_application(dp)
    handle_reply_to_admin(dp)
    handle_reply_to_users_report(dp)
    handle_report_error(dp)
    handle_select_category_to_trial(dp)
    handle_send_message_to_liar(dp)
    handle_send_new_application_to_admin(dp)
    handle_send_new_order_wo_prcmd(dp)
    handle_send_sale_for_review(dp)
    handle_send_specific_comment_about_application_refusal(dp)
    handle_send_validation_to_transfer(dp)
    handle_set_keybaord_with_answers_why_didnt_by(dp)
    handle_show_all_stop_words(dp)
    handle_stop_words(dp)
    handle_stop_words_message(dp)
    handle_transfer_account(dp)
    handle_withdraw_ref_balance(dp)
    handler_get_bot_info(dp)
    handler_get_category_to_send_last_messages(dp)
    handler_get_info_about_bot(dp)
    handler_get_new_stop_word(dp)