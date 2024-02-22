from typing import Iterable, List, Tuple, Union
from src.data.config import *
from mysql.connector.connection import MySQLConnection as Connection
from mysql.connector.cursor import MySQLCursor as Cursor
from datetime import datetime
from decimal import Decimal
from src.apis.db import *
from src.data.modules.statistic import *


def save_to_statistics(
    new_clients: int = 0,  # a client is a person who paid at least one subscribe
    payments_sum: Decimal = Decimal("0.0"),
    new_payments: int = 0,
    new_users: int = 0,  # an user is a person  without any subscribes
    repeated_payments: int = 0,
    conversions_to_client: int = 0,  # when a person used to have a trial period but then has bought a subscribe
    activated_trial: int = 0,  # the distinct persons that activated trial
    were_got_last_messages: int = 0,
    new_refererals: int = 0,
    new_referal_buyers: int = 0,
    total_referal_income: Decimal = 0,
    total_referal_commisions: Decimal = 0,
    bot_activates: int = 0,  # the activations of main bot: @golubin_bot
    trial_activations: int = 0,  # the activations that can be made even from one person
    ref_link: Union[
        str, None
    ] = None,  # if there ref_link is not null, the current statistics
    # will be uploaded for the referal or promocode as well
):
    conn, cursor = get_connection_and_cursor()
    today = datetime.now().strftime(DATE_FORMAT)
    cursor.execute(
        f'SELECT COUNT({NEW_CLIENTS}) FROM {STATISTICS_TABLE} WHERE {DATE} = "{today}"'
    )
    if not cursor.fetchall()[0][0]:
        cursor.execute(
            f'INSERT INTO {STATISTICS_TABLE} VALUES ("{today}", {new_clients}, '
            f"{payments_sum}, {new_payments}, {new_users}, {repeated_payments}, {conversions_to_client}, "
            f"{activated_trial}, {were_got_last_messages}, {new_refererals}, {new_referal_buyers}, "
            f"{total_referal_income}, {total_referal_commisions}, {bot_activates}, {trial_activations})"
        )
        conn.commit()
    else:
        cursor.execute(
            f"UPDATE {STATISTICS_TABLE} SET "
            f"{NEW_CLIENTS} = {NEW_CLIENTS} + {new_clients}, "
            f"{TOTAL_PAYMENT_SUM} = {TOTAL_PAYMENT_SUM} + {payments_sum}, "
            f"{PAYMENT_NUMBER} = {PAYMENT_NUMBER} + {new_payments}, "
            f"{NEW_USERS} = {NEW_USERS} + {new_users}, "
            f"{REPEATED_PAYMENTS} = {REPEATED_PAYMENTS} + {repeated_payments}, "
            f"{CONVERSIONS_TO_CLIENT} = {CONVERSIONS_TO_CLIENT} + {conversions_to_client}, "
            f"{ACTIVATED_TRIAL} = {ACTIVATED_TRIAL} + {activated_trial}, "
            f"{WERE_GOT_LAST_MESSAGES} = {WERE_GOT_LAST_MESSAGES} + {were_got_last_messages}, "
            f"{NEW_REFERERALS_NUMBER} = {NEW_REFERERALS_NUMBER} + {new_refererals}, "
            f"{REF_BUYER_NUMBER} = {REF_BUYER_NUMBER} + {new_referal_buyers}, "
            f"{TOTAL_REF_INCOME} = {TOTAL_REF_INCOME} + {total_referal_income}, "
            f"{TOTAL_REF_COMMISSIONS} = {TOTAL_REF_COMMISSIONS} + {total_referal_commisions}, "
            f"{BOT_ACTIVATES} = {BOT_ACTIVATES} + {bot_activates}, "
            f"{TRIAL_ACTIVATIONS} = {TRIAL_ACTIVATIONS} + {trial_activations} "
            f'WHERE {DATE} = "{today}"'
        )
        conn.commit()
    if ref_link:
        _save_referal_stats(
            conn,
            cursor,
            today,
            ref_link,
            bot_activates,
            new_users,
            new_clients,
            new_payments,
            payments_sum,
            total_referal_commisions,
            repeated_payments,
            conversions_to_client,
        )
    close_connection_and_cursor(conn, cursor)


def _save_referal_stats(
    conn: Connection,
    cursor: Cursor,
    today: str,
    ref_link: str,
    bot_activates: int = 0,
    new_users: int = 0,
    new_clients: int = 0,
    new_payments: int = 0,
    payments_sum: Decimal = Decimal("0.0"),
    total_referal_commisions: Decimal = Decimal("0.0"),
    repeated_payments: int = 0,
    conversions_to_client: int = 0,
):
    ref_link = ref_link.replace("\\", "\\\\").replace('"', '\\"')
    cursor.execute(
        f'SELECT COUNT({DATE}) FROM {REFERAL_STATS_TABLE} WHERE  {REFERAL_LINK} = "{ref_link}" AND {DATE} = "{today}"'
    )
    if not cursor.fetchall()[0][0]:
        cursor.execute(
            f'INSERT INTO {REFERAL_STATS_TABLE} VALUES ("{ref_link}", "{today}", {bot_activates}, '
            f"{new_users}, {new_clients}, {new_payments}, {payments_sum}, {total_referal_commisions}, "
            f"{repeated_payments}, {conversions_to_client})"
        )
    else:
        cursor.execute(
            f"UPDATE {REFERAL_STATS_TABLE} SET "
            f"{BOT_ACTIVATES} = {BOT_ACTIVATES} + {bot_activates}, "
            f"{NEW_USERS} = {NEW_USERS} + {new_users}, "
            f"{NEW_CLIENTS} = {NEW_CLIENTS} + {new_clients}, "
            f"{PAYMENT_NUMBER} = {PAYMENT_NUMBER} + {new_payments}, "
            f"{TOTAL_PAYMENT_SUM} = {TOTAL_PAYMENT_SUM} + {payments_sum}, "
            f"{TOTAL_REF_COMMISSIONS} = {TOTAL_REF_COMMISSIONS} + {total_referal_commisions}, "
            f"{REPEATED_PAYMENTS} = {REPEATED_PAYMENTS} + {repeated_payments}, "
            f"{CONVERSIONS_TO_CLIENT} = {CONVERSIONS_TO_CLIENT} + {conversions_to_client} "
            f'WHERE {REFERAL_LINK} = "{ref_link}" AND {DATE} = "{today}"'
        )
    conn.commit()


def get_statistics_by_date(
    date: datetime,
    fields=(
        NEW_CLIENTS,
        TOTAL_PAYMENT_SUM,
        PAYMENT_NUMBER,
        NEW_USERS,
        REPEATED_PAYMENTS,
        CONVERSIONS_TO_CLIENT,
        ACTIVATED_TRIAL,
        WERE_GOT_LAST_MESSAGES,
    ),
) -> tuple:
    select_text = ", ".join(fields)
    conn, cursor = get_connection_and_cursor()
    # except date column
    cursor.execute(
        f"SELECT {select_text} FROM {STATISTICS_TABLE} "
        f'WHERE {DATE} = "{date.strftime(DATE_FORMAT)}"'
    )
    return _fetch_statistics_result_and_close(cursor, conn, len(fields))


def get_statistics_by_period(
    date1: datetime,
    date2: datetime,
    fields=(
        NEW_CLIENTS,
        TOTAL_PAYMENT_SUM,
        PAYMENT_NUMBER,
        NEW_USERS,
        REPEATED_PAYMENTS,
        CONVERSIONS_TO_CLIENT,
        ACTIVATED_TRIAL,
        WERE_GOT_LAST_MESSAGES,
    ),
) -> tuple:
    select_text = ", ".join([f"SUM({i})" for i in fields])
    conn, cursor = get_connection_and_cursor()
    cursor.execute(
        f"SELECT {select_text} "
        f"FROM {STATISTICS_TABLE} WHERE {DATE} BETWEEN "
        f'"{date1.strftime(DATE_FORMAT)}" AND "{date2.strftime(DATE_FORMAT)}"'
    )
    return _fetch_statistics_result_and_close(cursor, conn, len(fields))


def _fetch_statistics_result_and_close(
    cursor: Cursor, connection: Connection, fields_len: int
) -> tuple:
    result = cursor.fetchall()
    close_connection_and_cursor(connection, cursor)
    if not result:
        return [0] * fields_len
    else:
        return result[0]


def increase_new_messages_number(
    for_category: int, by_number: int = 1, for_time: datetime = None
):
    now = for_time if for_time else datetime.now()
    now = now.replace(minute=0, second=0, microsecond=0)
    now = now.strftime(TIMESTAMP_FORMAT)
    conn, cursor = get_connection_and_cursor()
    cursor.execute(
        f"SELECT COUNT({CATEGORY}) FROM {NEW_MESSAGES_NUMBER_TABLE} WHERE {CATEGORY} = {for_category} AND "
        f'{TIME} = "{now}"'
    )
    if cursor.fetchall()[0][0]:
        cursor.execute(
            f"UPDATE {NEW_MESSAGES_NUMBER_TABLE} SET {MSG_NUMBER} = {MSG_NUMBER} + {by_number} WHERE "
            f'{TIME} = "{now}" AND {CATEGORY} = {for_category}'
        )
    else:
        cursor.execute(
            f'INSERT INTO {NEW_MESSAGES_NUMBER_TABLE} VALUES ("{now}", {for_category}, {by_number})'
        )
    commit_and_close_connection_and_cursor(conn, cursor)


def get_new_messages_number(
    for_time: Union[date, datetime], for_category: int = None
) -> int:
    is_datetime = False
    if isinstance(for_time, datetime):
        is_datetime = True
        for_time = for_time.replace(minute=0, second=0, microsecond=0)
    str_time = for_time.strftime(TIMESTAMP_FORMAT)
    if not is_datetime:
        time_filter = (
            f'"{str_time}" <= {TIME}  AND {TIME} < "{str_time}" + INTERVAL 1 DAY'
        )
    else:
        time_filter = f'{TIME} = "{str_time}"'
    category_filter = ""
    if for_category != None:
        category_filter = f" AND {CATEGORY} = {for_category}"
    conn, cursor = get_connection_and_cursor()
    cursor.execute(
        f"SELECT SUM({MSG_NUMBER}) FROM {NEW_MESSAGES_NUMBER_TABLE} WHERE {time_filter}"
        + category_filter
    )
    result = cursor.fetchall()
    close_connection_and_cursor(conn, cursor)
    if not result or not result[0] or not result[0][0]:
        return 0
    else:
        return result[0][0]


def get_average_messages_number(
    hour: int, period: int = -1, week_day: int = None, category: int = None
) -> float:
    """
    period is offset of first date from current to count average values (first date = now() - period)

    returns average number of messages per current hour, weekday, category
    """
    time_filter = ""
    if period != -1:
        if period < 0:
            raise ValueError(f"Invalid value for period argument: {period}")
        time_filter = f" AND {TIME} >= NOW() - INTERVAL {period} DAY"
    week_filter = ""
    if week_day != None:
        week_filter = f" AND WEEKDAY({TIME}) = {week_day}"
    category_filter = ""
    if category != None:
        category_filter = f" AND {CATEGORY} = {category}"
    conn, cursor = get_connection_and_cursor()
    cursor.execute(
        f"SELECT SUM({MSG_NUMBER})/COUNT(DISTINCT({TIME})) FROM {NEW_MESSAGES_NUMBER_TABLE} "
        f"WHERE HOUR({TIME}) = {hour}{time_filter}{week_filter}{category_filter}"
    )
    result = cursor.fetchall()[0]
    close_connection_and_cursor(conn, cursor)
    if not result or (isinstance(result, Iterable) and not result[0]):
        return 0.0
    return float(result[0])


def calculate_conversions() -> Tuple[float, float, float]:
    """
    returns:

            1) conversion of bot-activating to trial,

            2) conversion of bot-activate to client,

            3) conversion of trial-activating to client
    """
    conn, cursor = get_connection_and_cursor()
    cursor.execute(f"SELECT COUNT({ID_COL}) FROM {USERS_TABLE_NAME}")
    users_number = cursor.fetchall()[0][0]
    cursor.execute(f"SELECT COUNT(DISTINCT({ID_COL})) FROM {TRIAL_PERIOD_INFO_TABLE}")
    num_of_users_that_tried_trial = cursor.fetchall()[0][0]
    cursor.execute(
        f"SELECT COUNT(DISTINCT({ID_COL})) FROM {CLIENTS_SUBSCRIBES} AS client WHERE {IS_PAID} AND "
        f"NOT EXISTS (SELECT {ID_COL} FROM {TRIAL_PERIOD_INFO_TABLE} WHERE {ID_COL} = client.id)"
    )
    number_of_clear_clients = cursor.fetchall()[0][0]
    cursor.execute(
        f"SELECT COUNT(DISTINCT({ID_COL})) FROM {CLIENTS_SUBSCRIBES} AS client WHERE {IS_PAID} AND "
        f"EXISTS (SELECT {ID_COL} FROM {TRIAL_PERIOD_INFO_TABLE} WHERE {ID_COL} = client.id)"
    )
    number_of_funnel_clients = cursor.fetchall()[0][0]
    close_connection_and_cursor(conn, cursor)
    return (
        num_of_users_that_tried_trial / users_number,
        number_of_clear_clients / users_number,
        number_of_funnel_clients / users_number,
    )


def get_referal_statistics(
    referal_link: str, for_date: Union[date, None] = None
) -> Tuple[int, int, int, int, Decimal, Decimal, int, int]:
    """
    returns: 0) bot activations, 1) new users number, 2) new clients number, 3) payments number, 4) total payments sum,
    5) total referal commissions sum, 6) repeated payments number, 7) number of conversions from user to client
    """
    referal_link = referal_link.replace("\\", "\\\\").replace('"', '\\"')
    conn, cursor = get_connection_and_cursor()
    if for_date:
        cursor.execute(
            f"SELECT {BOT_ACTIVATES}, {NEW_USERS}, {NEW_CLIENTS}, {PAYMENT_NUMBER}, {TOTAL_PAYMENT_SUM}, "
            f"{TOTAL_REF_COMMISSIONS}, {REPEATED_PAYMENTS}, {CONVERSIONS_TO_CLIENT} FROM {REFERAL_STATS_TABLE} "
            f'WHERE {REFERAL_LINK} = "{referal_link}" AND {DATE} = "{for_date.strftime(DATE_FORMAT)}"'
        )
    else:
        cursor.execute(
            f"SELECT SUM({BOT_ACTIVATES}), SUM({NEW_USERS}), SUM({NEW_CLIENTS}), SUM({PAYMENT_NUMBER}), "
            f"SUM({TOTAL_PAYMENT_SUM}),SUM({TOTAL_REF_COMMISSIONS}),SUM({REPEATED_PAYMENTS}),SUM({CONVERSIONS_TO_CLIENT})"
            f'FROM {REFERAL_STATS_TABLE} WHERE {REFERAL_LINK} = "{referal_link}"'
        )
    result = cursor.fetchall()
    close_connection_and_cursor(conn, cursor)
    if not result or result[0] == (None,) * len(result[0]):
        return (0, 0, 0, 0, Decimal("0.0"), Decimal("0.0"), 0, 0)
    return result[0]


def get_all_referal_links() -> List[str]:
    conn, cursor = get_connection_and_cursor()
    cursor.execute(f"SELECT DISTINCT({REFERAL_LINK}) FROM {REFERAL_STATS_TABLE}")
    result = cursor.fetchall()
    close_connection_and_cursor(conn, cursor)
    return [i[0] for i in result]
