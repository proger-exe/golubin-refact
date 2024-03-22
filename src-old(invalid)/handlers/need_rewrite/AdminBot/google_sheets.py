import calendar
from time import sleep
from History.config import DATE_FORMAT
from typing import Union, Tuple
import Statistics
import user
from bot_config import THREE_WEEKS, all_possible_periods
from .admin_bot_config import *
from client import Client
from datetime import *
import httplib2, apiclient.discovery
import pandas as pd
import logging
from oauth2client.service_account import ServiceAccountCredentials
from decimal import Decimal
from Statistics.statistics import *
from aiogram import Bot
from History import *
from telebot import TeleBot

def get_gsheets_service():
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        CREDENTIAL_FILES, [GOOGLE_SHEETS_API_URL, GOOGLE_DRIVE_API_URL])
    httpAuth = credentials.authorize(httplib2.Http())
    service = apiclient.discovery.build('sheets','v4', http = httpAuth)
    return service

def generate_client_data_sheets() -> tuple:
    data_sheets = dict()
    trial_n = 0
    payed_subs_n = 0
    now = datetime.now()
    clients_ids = set() #clients who have paid subscribes 
    clients = Client.get_all_clients_from_db()
    subscribes_n = len(clients)
    data_sheets = pd.DataFrame(
        columns = [
            'id', 'ник', 'категория', 'дата последней оплаты', 'пробный период', 
            'осталось дней', 'платный', 'приостановлен', 'срок жизни', 'суммарный доход', 'источник'
        ]
    )
    for c in clients:
        trial_period_info = ''
        is_using_trial = c.is_using_trial
        has_paid_subscribes = c.has_paid_period
        if is_using_trial:
            trial_period_info = f'до {c.trial_period_end.strftime("%d.%m.%Y %H:%M")}'
            if not has_paid_subscribes: 
                trial_n += 1
        else:
            trial_period_info = 'отсутсвует'
        days_left = c.get_payment_days_left()
        if days_left:
            if isinstance(days_left, float) and days_left < 1:
                days_left = 'меньше 1'
            if has_paid_subscribes:
                payed_subs_n += 1
                clients_ids.add(c.id)
        else:
            days_left = 'отключён'
        referal_origin = user.get_origin_of(c.id)
        if not referal_origin:
            referal_origin = 'неизвестно'
        data_sheets.loc[len(data_sheets)] = [
            c.id, 
            '', message_category_names[c.sending_mode],
            c.last_payment_date.strftime("%d.%m.%Y %H:%M"), 
            trial_period_info, 
            days_left, 
            'да' if has_paid_subscribes else 'нет', 
            'да' if c.unpause_date and c.unpause_date > now else 'нет',
            0, 0, referal_origin 
        ]
    return data_sheets, subscribes_n, trial_n, payed_subs_n, len(clients_ids)

async def set_extra_info_for_clients(data_sheets: pd.DataFrame, bot: Bot):
    history = PaymentHistory.get()
    for i in range(len(data_sheets)):
        data_sheets['ник'][i] = await get_nickname_for_client(data_sheets.id[i], bot)
        data_sheets['срок жизни'][i], data_sheets['суммарный доход'][i] = \
            get_term_and_total_income_of_client(data_sheets.id[i], history)
        
async def get_nickname_for_client(id: int, bot: Bot) -> str:
    user = None
    try:
        user = await bot.get_chat_member(id, id)
        user = user.user
        if user.username:
            username = '@' + user.username 
        else:
            username = user.full_name
    except Exception as e:
        logging.error(f'can not get a username for statistics for {id}: '+str(e), exc_info = True)
        username = str(id)
    return username

def get_term_and_total_income_of_client(id: int) -> tuple:
    first_launch = user.get_user_launching_date(id)
    if not first_launch:
        first_launch = FAKE_LAUNCHING_DATES[0]
    term = ''
    is_old_user = first_launch.replace(microsecond = False) in FAKE_LAUNCHING_DATES
    if not is_old_user:
        term = (globals()['date'].today() - first_launch.date()).days
        months = term // 30
        days = term - months * 30
        if months:
            term = f'{months} м. {days} д.'
        else:
            term = f'{days} д.'
    else:
        term = 'неизвестно'
    income = 0
    for payment in PaymentHistory.findPaymentsBy(CLIENT_ID = id):
        income += payment.amount
    income = '{0:.2f}'.format(income).replace('.', ',')
    return term, income

def upload_client_data_into_gsh(data_sheets: pd.DataFrame):
    service = get_gsheets_service()
    make_sure_that_sheet_exists(service, GOOGLE_SPRSHT_ID, CLIENTS_SHEETS_NAME)
    service.spreadsheets().values().batchUpdate(
        spreadsheetId = GOOGLE_SPRSHT_ID, body = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"{CLIENTS_SHEETS_NAME}!A1:K{len(data_sheets)+1}",
                    "majorDimension": "ROWS",
                    "values": [list(data_sheets)] + [list(r) for r in  data_sheets.values]
                }
            ]
        }
    ).execute()
    client_terms = []
    for i in range(len(data_sheets)):
        if data_sheets['срок жизни'][i] != 'неизвестно' and data_sheets['платный'][i] == 'да':
            term = data_sheets['срок жизни'][i].split()
            days = 0
            if 'м.' in term:
                days += int(term[0]) * 30
            days += int(term[-2])
            client_terms.append(days)
    service.spreadsheets().values().batchUpdate(
        spreadsheetId = GOOGLE_SPRSHT_ID, body = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"{CLIENTS_SHEETS_NAME}!Z2:Z{len(data_sheets)+1}",
                    "majorDimension": "COLUMNS",
                    "values": [client_terms]
                } 
            ]
        } 
    ).execute()

# the function checks if sheet with sheet_name exists in spread sheet with spread_sheet_id and 
# create new sheet with this name if the sheet does not exist and returns id of the table
def make_sure_that_sheet_exists(service, spread_sheet_id: int, sheet_name: str) -> int:
    try:
        service.spreadsheets().values().get(
            spreadsheetId = spread_sheet_id,
            range = sheet_name+'!A1:A1',
            majorDimension = 'COLUMNS'
        ).execute()
    except:
        response = service.spreadsheets().batchUpdate(
            spreadsheetId = spread_sheet_id,
            body =  {
                "requests": [{
                    "addSheet": {
                        "properties": {
                            "title": sheet_name,
                        }
                    }
                }]
            }
        ).execute()
        return response['replies'][0]['addSheet']['properties']['sheetId']
    else:
        return find_sheet_id(service, spread_sheet_id, sheet_name)

def find_sheet_id(service, spread_sheet_id: int, sheet_title: str) -> int:
    sheets = service.spreadsheets().get(spreadsheetId = spread_sheet_id).execute()['sheets']
    for sheet in sheets:
        if sheet['properties']['title'] == sheet_title:
            return sheet['properties']['sheetId']
    return -1

def upload_client_extra_info_into_gsh(data_sheets: pd.DataFrame):
    service = get_gsheets_service()
    for m in message_categories:
        service.spreadsheets().values().batchUpdate(
            spreadsheetId = GOOGLE_SPRSHT_ID, body = {
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {
                        "range": f"{sheet_name}!B2:B{len(data_sheets[m])+1}",
                        "majorDimension": "ROWS",
                        "values": [[nick] for nick in  data_sheets[m]['ник']]
                    } 
                ]
            } 
        ).execute()
        service.spreadsheets().values().batchUpdate(
            spreadsheetId = GOOGLE_SPRSHT_ID, body = {
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {
                        "range": f"{sheet_name}!H2:H{len(data_sheets[m])+1}",
                        "majorDimension": "ROWS",
                        "values": [[term] for term in  data_sheets[m]['срок жизни']]
                    } 
                ]
            } 
        ).execute()
        service.spreadsheets().values().batchUpdate(
            spreadsheetId = GOOGLE_SPRSHT_ID, body = {
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {
                        "range": f"{sheet_name}!I2:I{len(data_sheets[m])+1}",
                        "majorDimension": "ROWS",
                        "values": [[total] for total in  data_sheets[m]['суммарный доход']]
                    } 
                ]
            } 
        ).execute()

def upload_analytics_to_google_sheet_for_period(date1, date2):
    date1, date2
    date_format = '%d.%m.%Y'
    current_date = date1
    service = get_gsheets_service()
    clear_google_sheet(service)
    values = pd.DataFrame(columns = ['dates'] + [i for i in analytics_indices])
    j = 0
    while True:
        stat = get_statistics_by_date(current_date, 
            fields = STATISTICS_GOOGLE_SHEETS_FIELDS
        )
        values.loc[j] = [current_date.strftime(date_format), *[0] * ANALYTICS_INDICES_N]
        for i in analytics_indices:
            if stat[i] == None:
                values[i][j] = 0
            elif isinstance(stat[i], Decimal):
                values[i][j] = float(stat[i])
            else:
                values[i][j] = stat[i]
        if current_date == date2:
            break
        j += 1
        current_date += timedelta(days = 1)
    statistics_len = j + 1
    service.spreadsheets().values().batchUpdate(
        spreadsheetId = SERVICE_ANALYTICS_SPRSHT, body = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"{SRVS_STAT_SHEET_NAME}!A2:A{statistics_len+2}",
                        "majorDimension": "COLUMNS",
                        "values": [list(values.dates)]
                }
            ]
        }
    ).execute()
    for i in analytics_indices:
        push_statistics_into_google_sheets(values, i, service)
    set_formatting_google_sheet(service, statistics_len)
    conversions = ['{0:.2f}%'.format(i*100).replace('.', ',') for i in calculate_conversions()]
    service.spreadsheets().values().batchUpdate(
        spreadsheetId = SERVICE_ANALYTICS_SPRSHT, body = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"{SRVS_STAT_SHEET_NAME}!{range_of_conversions_columns}",
                        "majorDimension": "ROWS",
                        "values": [CONVERSIONS_COLUMNS, conversions]
                }
            ]
        }
    ).execute()

def clear_google_sheet(service):
    clear_request = {
        "requests":[
            {
                "updateCells": {
                    "range": {
                        "sheetId": SRVS_STAT_SHEET_ID,
                        "startRowIndex": 1
                    },
                    "fields": "*"
                }
            }
        ]
    }
    service.spreadsheets().batchUpdate(
        spreadsheetId = SERVICE_ANALYTICS_SPRSHT,
        body=clear_request
    ).execute()

def push_statistics_into_google_sheets(statistics: pd.DataFrame, column_index: int, service):
    statistics_len = len(statistics)
    column_letter = chr(ord('B') + column_index)
    service.spreadsheets().values().batchUpdate(
        spreadsheetId = SERVICE_ANALYTICS_SPRSHT, body = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"{SRVS_STAT_SHEET_NAME}!"\
                        f"{column_letter}2:"\
                        f"{column_letter}{statistics_len+2}",
                        "majorDimension": "COLUMNS",
                        "values": [
                            list(statistics[column_index])
                        ]
                }
            ]
        }
    ).execute()

def set_formatting_google_sheet(service, statistics_len: int):
    outside_borders_width = 2
    response = service.spreadsheets().batchUpdate(
        spreadsheetId = SERVICE_ANALYTICS_SPRSHT,
        body = {
            "requests": [
                set_borders(
                    SRVS_STAT_SHEET_ID, 0, statistics_len + 1, 0, STAT_COLUMN_INDICES_NUM + 1, outside_borders_width)
            ] + \
            [
                {
                    "repeatCell": 
                    {
                        "range": 
                        {
                            "sheetId": SRVS_STAT_SHEET_ID,
                            "startRowIndex": 0 if is_top else statistics_len+1,
                            "endRowIndex": 1 if is_top else statistics_len+2,
                            "startColumnIndex": 0,
                            "endColumnIndex": STAT_COLUMN_INDICES_NUM+1
                        },
                        "cell": 
                        {
                            "userEnteredFormat": 
                            {
                                "textFormat":
                                {
                                    "bold": True
                                }
                            }
                        },
                        "fields": "userEnteredFormat.textFormat" 
                    }
                } for is_top in (True, False)
            ] + \
            [
                set_currency_ruble(
                    SRVS_STAT_SHEET_ID, 0, statistics_len + 1, 
                    STAT_COLUMN_INDICES['payments_sum'] + 1, STAT_COLUMN_INDICES['payments_sum'] + 2
                )
                
            ]
        }
    ).execute()

def set_borders(
    sheet_id: int, 
    start_row_index: int,
    end_row_index: int,
    start_column_index: int,
    end_column_index: int,
    width: int = 1,
    style = "SOLID",
    with_inner_sides: bool = True
) -> dict:
    r = {
        'updateBorders': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': start_row_index,
                'endRowIndex': end_row_index,
                'startColumnIndex': start_column_index,
                'endColumnIndex': end_column_index
            },
            'bottom': {  
                'style': style,
                'width': width,  
                'color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 1}
            }, 
            'top': { 
                'style': style,
                'width': width,
                'color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 1}
            },
            'left': {
                'style': style,
                'width': width,
                'color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 1}
            },
            'right': { 
                'style': style,
                'width': width,
                'color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 1}
            }
        }
    }
    if with_inner_sides:
        r['updateBorders']['innerHorizontal'] = { 
            'style': style,
            'width': 1,
            'color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 1}
        }
        r['updateBorders']['innerVertical'] = { 
            'style': style,
            'width': 1,
            'color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 1}
        }
    return r

def set_centralize(
    sheet_id: int, start_row_index: int, end_row_index: int, start_column_index: int, 
    end_column_index: int, vertical: bool = False
) -> dict:
    result = {
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": start_row_index,
                "endRowIndex": end_row_index,
                "startColumnIndex": start_column_index,
                "endColumnIndex": end_column_index
            },
            "cell": {
                "userEnteredFormat": {
                    "horizontalAlignment": 'CENTER',
                }
            },
            "fields": "userEnteredFormat.horizontalAlignment"
        }
    }
    if vertical:
        result["repeatCell"]['cell']['userEnteredFormat']['verticalAlignment'] = 'MIDDLE'
    return result

def set_currency_ruble(
    sheet_id: int, 
    start_row_index: int,
    end_row_index: int,
    start_column_index: int,
    end_column_index: int
) -> dict:
    return {
        "repeatCell": 
        {
            "range": 
            {
                "sheetId": sheet_id,
                "startRowIndex": start_row_index,
                "endRowIndex": end_row_index,
                "startColumnIndex": start_column_index,
                "endColumnIndex": end_column_index
            },
            "cell": 
            {
                "userEnteredFormat": 
                {
                    "numberFormat": {
                        "type": "CURRENCY",
                        "pattern": "[$₽-411]#,##0.00"
                    }
                }
            },
            "fields": "userEnteredFormat.numberFormat"
        }
    }

def upload_payments_history_for_period(first_date: date, second_date: date):
    logging.warning('uploading payments history')
    history = PaymentHistory.getForPeriod(first_date, second_date)
    logging.warning(f'{len(history[first_date])} payments for {first_date}')
    service = get_gsheets_service()
    values = service.spreadsheets().values().get(
        spreadsheetId = SERVICE_ANALYTICS_SPRSHT,
        range = PAYMENTS_HISTORY_SHEET_NAME+'!A2:E',
        majorDimension = 'COLUMNS'
    ).execute()
    str_first_date = first_date.strftime(DATE_FORMAT)
    last_unchangeable_row = get_last_unchangeable_row(str_first_date, values['values'])
    if not last_unchangeable_row:
        last_unchangeable_row = int(values['values'][0][-1]) # column № 0 contains payment ids
    current_row = int(last_unchangeable_row) + 1
    last_payment_index = last_unchangeable_row
    current_payment_index = last_payment_index + 1
    new_values, merge_cells_requests, end_row = get_statistics_values_and_merge_cells_requests_from_payments_history(
        history, current_row, current_payment_index)
    if not new_values:
        logging.warning("no values to upload to payments history")
        return
    service.spreadsheets().values().batchUpdate(
        spreadsheetId = SERVICE_ANALYTICS_SPRSHT, body = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"{PAYMENTS_HISTORY_SHEET_NAME}!A{last_unchangeable_row+2}:F{end_row+1}",
                    "majorDimension": "ROWS",
                    "values": new_values
                }
            ]
        }
    ).execute()
    logging.warning(f'uploaded payments: {tuple(payment.id for payment in  history[first_date])}')
    request = {
        "requests": [
            set_borders(PAYMENTS_HISTORY_SHEET_ID, last_unchangeable_row + 1, end_row + 1, 0, 5),
            set_currency_ruble(PAYMENTS_HISTORY_SHEET_ID, last_unchangeable_row + 1, end_row + 1, 2, 3)
        ]
    }
    service.spreadsheets().batchUpdate(spreadsheetId = SERVICE_ANALYTICS_SPRSHT, body = request).execute()
    if merge_cells_requests:
        service.spreadsheets().batchUpdate(
            spreadsheetId = SERVICE_ANALYTICS_SPRSHT,
            body = {
                "requests": merge_cells_requests
            }
        ).execute()
    splited_values = []
    for i in range(len(values['values'])):
        splited_values.append(
            values['values'][i][:last_unchangeable_row] + [new_values[j][i] for j in range(len(new_values))])
    del values
    del new_values
    upload_statistics_for_periods(service, splited_values)

def get_last_unchangeable_row(str_origin_date: str, values: list) -> Union[int, None]:
    for str_date in values[1][::-1]: # column № 1 contains dates
        if str_date and str_origin_date == str_date:
            return values[1].index(str_date)

def get_statistics_values_and_merge_cells_requests_from_payments_history(
    history: PaymentHistory, 
    start_row: int,
    start_payment_index: int
) -> tuple:
    values = []
    merge_cells_requests = []
    current_row = start_row
    for date in history.dates:
        payments= history[date]
        if not payments:
            continue
        start_date_row = current_row
        str_date = date.strftime(DATE_FORMAT)
        for payment in payments:
            comments = ''
            if payment.comments & IS_UPSALED:
                comments = 'Оплачен апсейл' 
            elif payment.comments & IS_ADDED_MANUALLY:
                comments = 'Добавлено вручную' 
            values.append([
                str(start_payment_index), str_date, str(payment.amount).replace('.', ','), 
                get_period_name(payment.period),
                '' if not payment.referal_commission else '{0:.2f}'.format(payment.referal_commission).replace('.',','),
                comments
            ])
            start_payment_index += 1
            current_row += 1
        if current_row - start_date_row > 1:
            merge_cells_requests.append(
                merge_cells(PAYMENTS_HISTORY_SHEET_ID, start_date_row, current_row, 1, 2)
            )
    return values, merge_cells_requests, current_row - 1

def get_period_name(period: int) -> str:
    period = str(period)
    return period + (' дней' if period != THREE_WEEKS else ' день')

def merge_cells(
    sheet_id: int, start_row_index: int, end_row_index: int, 
    start_column_index: int, end_column_index: int
) -> dict:
    return {
        "mergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": start_row_index,
                "endRowIndex": end_row_index,
                "startColumnIndex": start_column_index,
                "endColumnIndex": end_column_index
            },
            "mergeType": "MERGE_ALL"
        }
    }

def upload_statistics_for_periods(service, values: list):
    periods_statistics = pd.DataFrame(
        columns = ['Куплено', 'Принесено прибыли'],
        index = [get_period_name(p) for p in all_possible_periods]
    )
    for p in periods_statistics.index:
        periods_statistics['Куплено'][p] = 0
        periods_statistics['Принесено прибыли'][p] = 0
    for i, period in enumerate(values[3]): # column № 3 contains payment periods
        if period not in periods_statistics.index:
            continue
        periods_statistics['Куплено'][period] += 1
        cost = Decimal(values[2][i].replace('₽', '').replace(',', '.').replace('\xa0', ''))
        periods_statistics['Принесено прибыли'][period] += cost
    for p in periods_statistics.index:
        periods_statistics['Принесено прибыли'][p] = float(periods_statistics['Принесено прибыли'][p])
    values = [periods_statistics['Куплено'].tolist(), periods_statistics['Принесено прибыли'].tolist()]
    service.spreadsheets().values().batchUpdate(
        spreadsheetId = SERVICE_ANALYTICS_SPRSHT, body = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"{PAYMENTS_HISTORY_SHEET_NAME}!N2:O8",
                    "majorDimension": "COLUMNS",
                    "values": values
                }
            ]
        }
    ).execute()

def upload_month_income(for_year: int, for_month: int):
    last_day_of_month = calendar.monthrange(for_year, for_month)[1]
    period = (date(for_year, for_month, 1), date(for_year, for_month, last_day_of_month))
    history = PaymentHistory.getForPeriod(*period)
    total_income = Decimal(0)
    total_purchases = 0
    for date_ in history.dates:
        for payment in history[date_]:
            total_income += payment.amount
            total_purchases += 1
    service = get_gsheets_service()
    months = service.spreadsheets().values().get(
        spreadsheetId = SERVICE_ANALYTICS_SPRSHT,
        range = MONTHS_INCOMES_SHEET_NAME+'!A1:A',
        majorDimension = 'ROWS'
    ).execute()['values']
    row = None
    for i, (val,) in [(a,b) for a,b in enumerate(months) if b][::-1]:
        if val == month_names[for_month]:
            row = i + 1
            break
    if row == None:
        row = for_month+1
    for column, value in (('B', float(total_income)), ('F', total_purchases)):
        service.spreadsheets().values().batchUpdate(
            spreadsheetId = SERVICE_ANALYTICS_SPRSHT, body = {
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {
                        "range": f"{MONTHS_INCOMES_SHEET_NAME}!{column}{row}:{column}{row}",
                        "majorDimension": "ROWS",
                        "values": [[value]]
                    }
                ]
            }
        ).execute()

def upload_new_messages_number(for_date: date):
    service = get_gsheets_service()
    values = service.spreadsheets().values().get(
        spreadsheetId = GOOGLE_SPRSHT_ID,
        range = NEW_MESSAGES_NUMBER_TABLE+'!A1:A',
        majorDimension = 'ROWS'
    ).execute()
    last_letter = chr(ord('A') + 1 + len(message_category_names))
    first_unwritten_row = get_first_unwritten_row(values)
    if first_unwritten_row == 1: # there is not header
        first_unwritten_row = 2
        service.spreadsheets().values().batchUpdate(
                spreadsheetId = GOOGLE_SPRSHT_ID, body = {
                    "valueInputOption": "USER_ENTERED",
                    "data": [
                        {
                            "range": f"{NEW_MESSAGES_NUMBER_TABLE}!A1:{last_letter}1",
                            "majorDimension": "ROWS",
                            "values": [['Дата'] + [message_category_names[i] for i in message_category_names]]
                        }
                    ]
                }
            ).execute()
    values = [int(Statistics.get_new_messages_number(for_date, i)) for i in message_category_names]
    for_date = for_date.strftime("%d.%m.%Y")
    service.spreadsheets().values().batchUpdate(
        spreadsheetId = GOOGLE_SPRSHT_ID, body = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"{NEW_MESSAGES_NUMBER_TABLE}!A{first_unwritten_row}:{last_letter}{first_unwritten_row}",
                    "majorDimension": "ROWS",
                    "values": [[for_date] + values]
                }
            ]
        }
    ).execute()

def update_new_messages_number_per_hour():
    table_height = 26
    first_column = 'C'
    last_column = chr(ord(first_column) + len(message_category_names))
    current_row = 2
    for weekday in range(7):
        values = []
        for hour in range(24):
            category_numbers = []
            # server which bot works on is in the utc+0 timezone, so we need to decrease our number to 3
            for category in message_category_names:    
                value = Statistics.get_average_messages_number(
                    (hour - 3) % 24, PERIOD_FOR_CALCULATING_AVERAGE_MESSAGE_NUMBER, weekday, category)
                category_numbers.append('{0:.1f}'.format(value).replace('.', ','))
            values.append(category_numbers)
        last_row = current_row + len(values)
        service = get_gsheets_service()
        service.spreadsheets().values().batchUpdate(
            spreadsheetId = ANALYTICS_SPREAD_SHEET_ID, body = {
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {
                        "range": f"{MESSAGES_NUMBER_PER_EACH_HOUR_TABLE}!"
                            f"{first_column}{current_row}:{last_column}{last_row}",
                        "majorDimension": "ROWS",
                        "values": values
                    }
                ]
            }
        ).execute()
        sleep(5)
        current_row += table_height

def get_first_unwritten_row(values: dict) -> int:
    if 'values' not in values:
        return 1
    else:
        return len(values['values']) + 1 #first row is header

def upload_funnel_statistics(for_date: date):
    service = get_gsheets_service()
    values = service.spreadsheets().values().get(
        spreadsheetId = GOOGLE_SPRSHT_ID,
        range = FUNNEL_STAT_TABLE+'!A1:A',
        majorDimension = 'ROWS'
    ).execute()
    first_unwritten_row = get_first_unwritten_row(values)
    if first_unwritten_row == 1:
        service.spreadsheets().values().batchUpdate(
            spreadsheetId = GOOGLE_SPRSHT_ID, body = {
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {
                        "range": f"{FUNNEL_STAT_TABLE}!A1:C1",
                        "majorDimension": "ROWS",
                        "values": [['Дата', 'Активировали пробный период', 'Получили последние сообщения']]
                    }
                ]
            }
        ).execute()
        first_unwritten_row = 2
    values = list(
        Statistics.get_statistics_by_date(
            for_date, fields = [Statistics.ACTIVATED_TRIAL, Statistics.WERE_GOT_LAST_MESSAGES])
    )
    for_date = for_date.strftime("%d.%m.%Y")
    service.spreadsheets().values().batchUpdate(
        spreadsheetId = GOOGLE_SPRSHT_ID, body = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"{FUNNEL_STAT_TABLE}!A{first_unwritten_row}:C{first_unwritten_row}",
                    "majorDimension": "ROWS",
                    "values": [[for_date] + values]
                }
            ]
        }
    ).execute()

def upload_referal_statistics(for_date: date):
    service = get_gsheets_service()
    stat = list(Statistics.get_statistics_by_date(
        for_date, 
        fields = (
            Statistics.NEW_REFERERALS_NUMBER, Statistics.REF_BUYER_NUMBER, 
            Statistics.TOTAL_REF_INCOME, Statistics.TOTAL_REF_COMMISSIONS 
        )
    ))
    for i in range(len(stat)):
        if isinstance(stat[i], Decimal):
            stat[i] = float(stat[i])
    values = service.spreadsheets().values().get(
        spreadsheetId = GOOGLE_SPRSHT_ID,
        range = REFERAL_STAT_TABLE+'!A1:A',
        majorDimension = 'ROWS'
    ).execute()
    first_unwritten_row = get_first_unwritten_row(values)
    last_letter = chr(ord('A') + 1 + len(stat))
    for_date = for_date.strftime(DATE_FORMAT)
    service.spreadsheets().values().batchUpdate(
        spreadsheetId = GOOGLE_SPRSHT_ID, body = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"{REFERAL_STAT_TABLE}!A{first_unwritten_row}:{last_letter}{first_unwritten_row}",
                    "majorDimension": "ROWS",
                    "values": [[for_date] + stat]
                }
            ]
        }
    ).execute()

def upload_number_of_active_users(date: date, active_n: int):
    date = date.strftime(DATE_FORMAT)
    service = get_gsheets_service()
    values = service.spreadsheets().values().get(
        spreadsheetId = SERVICE_ANALYTICS_SPRSHT,
        range = ACTIVE_USERS_TABLE+'!A1:A',
        majorDimension = 'ROWS'
    ).execute()
    first_unwritten_row = get_first_unwritten_row(values)
    service.spreadsheets().values().batchUpdate(
        spreadsheetId = SERVICE_ANALYTICS_SPRSHT, 
        body = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"{ACTIVE_USERS_TABLE}!A{first_unwritten_row}:B{first_unwritten_row}",
                    "majorDimension": "ROWS",
                    "values": [[date, active_n]]
                }
            ]
        }
    ).execute()
    request = {
        "requests": [
            set_borders(ACTIVE_USERS_SHEET_ID, first_unwritten_row-1, first_unwritten_row, 0, 2)
        ]
    }
    service.spreadsheets().batchUpdate(
        spreadsheetId = SERVICE_ANALYTICS_SPRSHT, 
        body = request
    ).execute()

def upload_new_referal_withdrawal(for_date: date, sum: Decimal):
    values = [[for_date.strftime('%d.%m.%Y'), '{0:.2f}'.format(sum).replace('.', ','), 'Выплата реф', 'Реф']]
    service = get_gsheets_service()
    temp = service.spreadsheets().values().get(
        spreadsheetId = SERVICE_ANALYTICS_SPRSHT,
        range = REFERAL_PAYMENTS_HISTORY_TABLE_NAME+'!A1:A',
        majorDimension = 'ROWS'
    ).execute()
    first_unwritten_row = get_first_unwritten_row(temp)
    del temp
    service.spreadsheets().values().batchUpdate(
        spreadsheetId = SERVICE_ANALYTICS_SPRSHT, 
        body = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"{REFERAL_PAYMENTS_HISTORY_TABLE_NAME}!A{first_unwritten_row}:D{first_unwritten_row}",
                    "majorDimension": "ROWS",
                    "values": values
                }
            ]
        }
    ).execute()

def upload_stat_about_each_category(year: int, month: int):
    service = get_gsheets_service()
    values = service.spreadsheets().values().get(
        spreadsheetId = SERVICE_ANALYTICS_SPRSHT,
        range = f'{METRICS_TABLE}!A1:F',
        majorDimension = 'ROWS'
    ).execute()
    first_row = get_first_unwritten_row(values)
    if first_row != 2:
        first_row += 1
    values = [['', f'{month_names[month]} {year}', '', '', '', '', '', '', '', '']]
    for i, c in enumerate(message_categories):
        i += 1 # first row is a month
        values.append([
            message_category_names[c], 
            *get_active_users_of_category(c, year, month),
            get_active_clients_of_category(c, year, month),
            *get_payments_num_and_sum(c, year, month),
            '', # Расходы
            f'=F{first_row+i}-G{first_row+i}', # Сальдо
            f'=F{first_row+i}/E{first_row+i}', # Средний чек,
            f'=H{first_row+i}/F{first_row+i}' # Рентабельность
        ])
    rows_range = (first_row + 1, first_row + i)
    avg_values = ['Ср Знач']
    total_values = ['Итог']
    for column in ('B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'):
        avg_values.append(f'=СРЗНАЧ({column}{rows_range[0]}:{column}{rows_range[1]})')
        total_values.append(f'=СУММ({column}{rows_range[0]}:{column}{rows_range[1]})')
    values.append(avg_values)
    values.append(total_values)
    service.spreadsheets().values().batchUpdate(
        spreadsheetId = SERVICE_ANALYTICS_SPRSHT, 
        body = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"{METRICS_TABLE}!A{first_row}:J{first_row+len(values)}",
                    "majorDimension": "ROWS",
                    "values": values
                }
            ]
        }
    ).execute()
    sheet_id = make_sure_that_sheet_exists(service, SERVICE_ANALYTICS_SPRSHT, METRICS_TABLE)
    set_formatting_for_metrics_table(service, sheet_id, first_row, first_row + len(values), 'J')

def set_formatting_for_metrics_table(service, sheet_id: int, first_row: int, last_row: int, last_column: str):
    end_column = ord(last_column) - ord('A') + 1
    request = {
        "requests": [
            set_borders(sheet_id, first_row-1, last_row-1, 0, end_column),
            set_borders(sheet_id, first_row-1, first_row, 0, end_column, 2),
            set_borders(sheet_id, last_row-3, last_row-1, 0, end_column, 2, with_inner_sides=False),
            {
                "repeatCell": 
                {
                    "range": 
                    {
                        "sheetId": sheet_id,
                        "startRowIndex": first_row-1,
                        "endRowIndex": first_row,
                        "startColumnIndex": 1,
                        "endColumnIndex": 2
                    },
                    "cell": 
                    {
                        "userEnteredFormat": 
                        {
                            "textFormat":
                            {
                                "bold": True
                            }
                        }
                    },
                    "fields": "userEnteredFormat.textFormat" 
                }
            },
            {
                "repeatCell": 
                {
                    "range": 
                    {
                        "sheetId": sheet_id,
                        "startRowIndex": last_row-3,
                        "endRowIndex": last_row,
                        "startColumnIndex": 0,
                        "endColumnIndex": end_column
                    },
                    "cell": 
                    {
                        "userEnteredFormat": 
                        {
                            "textFormat":
                            {
                                "bold": True
                            }
                        }
                    },
                    "fields": "userEnteredFormat.textFormat" 
                }
            }
        ]
    }
    service.spreadsheets().batchUpdate(
        spreadsheetId = SERVICE_ANALYTICS_SPRSHT, 
        body = request
    ).execute()
    service.spreadsheets().batchUpdate(
        spreadsheetId = SERVICE_ANALYTICS_SPRSHT, 
        body = {
            "requests": [
                merge_cells(sheet_id, first_row-1, first_row, 1, end_column)
            ]
        }
    ).execute()
    service.spreadsheets().batchUpdate(
        spreadsheetId = SERVICE_ANALYTICS_SPRSHT, 
        body = {
            "requests": [
                set_centralize(sheet_id, first_row-1, last_row, 0, end_column)
            ]
        }
    ).execute()

def get_active_users_of_category(category: int, year: int, month: int) -> int:
    return len(
        Client.get_clients_by_filter(
            category=category, payment_date=get_range_of_dates_for_month(year, month), choose_between_dates=True)
    ),\
    len(
        Client.get_clients_by_filter(
            category=category, payment_period_end=get_range_of_dates_for_month(year, month), choose_between_dates=True)
    )

def get_range_of_dates_for_month(year: int, month: int) -> Tuple[datetime, datetime]:
    '''returns min and max time points of current month'''
    d1 = datetime(year, month, 1, 0, 0, 0)
    if month != 12:
        d2 = datetime(year, month + 1, 1, 0, 0, 0) - timedelta(seconds = 1)
    else:
        d2 = datetime(year, 12, 31, 23, 59, 59)
    return d1, d2

def get_active_clients_of_category(category: int, year: int, month: int) -> int:
    return len(Client.get_clients_by_filter(
        category = category, 
        payment_date = get_range_of_dates_for_month(year, month), 
        choose_between_dates = True, is_paid = True
    ))

def get_payments_num_and_sum(category: int, year: int, month: int) -> Tuple[int, str]:
    payments = PaymentHistory.findPaymentsBy(
        DATE_PERIOD = get_range_of_dates_for_month(year, month), CATEGORY = category)
    return len(payments), ('{0:.2f}'.format(sum([payment.amount for payment in payments]))).replace('.', ',')

def upload_new_chats(chat_urls: typing.List[str]):
    service = get_gsheets_service()
    values = service.spreadsheets().values().get(
        spreadsheetId = GOOGLE_SPRSHT_ID,
        range = f'{EXTERNAL_CHATS_TABLE_NAME}!A1:A',
        majorDimension = 'COLUMNS'
    ).execute()
    if 'values' not in values:
        n = 0
    else:
        n = len(values['values'][0])
    service.spreadsheets().values().batchUpdate(
        spreadsheetId = GOOGLE_SPRSHT_ID, 
        body = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"{EXTERNAL_CHATS_TABLE_NAME}!A{n+1}:A{n+len(chat_urls)}",
                    "majorDimension": "COLUMNS",
                    "values": [chat_urls]
                }
            ]
        }
    ).execute()

def upload_real_and_planned_income_for_the_day(date: date):
    payments = PaymentHistory.getForDate(date)
    service = get_gsheets_service()
    values = service.spreadsheets().values().get(
        spreadsheetId = ANALYTICS_SPREAD_SHEET_ID,
        range = f'{PAYMENT_FORECAST_TABLE}!A1:AG',
        majorDimension = 'ROWS'
    ).execute()['values']
    num_of_payments, sum_of_payments = len(payments), sum([p.amount + p.referal_commission for p in payments])
    todays_coordinates = _get_todays_coordinates(date, values)
    if not todays_coordinates:
        return
    _upload_real_income(service, todays_coordinates, num_of_payments, sum_of_payments)
    _upload_planned_income(service, date, payments, values)

def _upload_real_income(service, todays_coordinates:  typing.Tuple[str, int],
    number_of_payments: int, sum_of_payments: Decimal):
    _upload_real_or_planned_income(True, service, todays_coordinates, number_of_payments, sum_of_payments)

def _upload_planned_income(service, today: date, payments: typing.List[Payment], values: list):
    temp_payments = payments
    payments = {payment.period: [0, Decimal(0)] for payment in temp_payments}
    for p in temp_payments:
        payments[p.period][0] += 1
        payments[p.period][1] += p.amount + p.referal_commission
    for period in payments:
        cords = _find_end_of_the_period_in_table(today, period, values)
        _upload_real_or_planned_income(False, service, cords, payments[period][0], payments[period][1])

def _upload_real_or_planned_income(
    real: bool, service, current_days_coordinates:  typing.Tuple[str, int],
    number_of_payments: int, sum_of_payments: Decimal
):
    offset = 2 if real else 1
    num_of_payments_cord = f"{current_days_coordinates[0]}{current_days_coordinates[1]+offset}"
    service.spreadsheets().values().batchUpdate( # upload real number of payments
        spreadsheetId = ANALYTICS_SPREAD_SHEET_ID, 
        body = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"{PAYMENT_FORECAST_TABLE}!{num_of_payments_cord}:{num_of_payments_cord}",
                    "majorDimension": "ROWS",
                    "values": [[number_of_payments]]
                }
            ]
        }
    ).execute()
    sum_of_payments_cord = f"{current_days_coordinates[0]}{current_days_coordinates[1]+offset+3}"
    service.spreadsheets().values().batchUpdate( # upload real sum of payments
        spreadsheetId = ANALYTICS_SPREAD_SHEET_ID, 
        body = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"{PAYMENT_FORECAST_TABLE}!{sum_of_payments_cord}:{sum_of_payments_cord}",
                    "majorDimension": "ROWS",
                    "values": [[f'{sum_of_payments}'.replace('.', ',')]]
                }
            ]
        }
    ).execute()

def _get_todays_coordinates(today: date, values: list) -> typing.Union[typing.Tuple[str, int], None]:
    str_month = f'{month_names[today.month]} {today.year - 2000}'
    height_of_month_table = 7
    i = 1 
    while values[i][0] != str_month:
        i += height_of_month_table
        if i >= len(values):
            return
    return _find_column_of_day(today.day), i + 1

def _find_column_of_day(day: int) -> str:
    '''
        Returns the column with a number of day which equals to :int: day in the PAYMENT_FORECAST_TABLE.
    '''
    column = 'B' # it stands before the first column with dates in the table
    for _ in range(day):
        column = _get_next_column(column)
    return column

def _get_next_column(letter):
    if len(letter) == 1:
        if letter == 'Z':
            return 'AA'
        return chr(ord(letter) + 1)
    if letter[-1] == 'Z':
        return _get_next_column(letter[:-1]) + 'A'
    letter = letter[:-1] + chr(ord(letter[-1]) + 1)
    return letter

def _find_end_of_the_period_in_table(today:date, period:str, values:list)->typing.Union[typing.Tuple[str, int], None]:
    new_date = today + timedelta(days=int(period))
    return _get_todays_coordinates(new_date, values)

def upload_referal_links_statistics_to_google_sheets(for_date: date, bot: TeleBot):
    service = get_gsheets_service()
    for ref_link in Statistics.get_all_referal_links():
        ref_stats = Statistics.get_referal_statistics(ref_link, for_date)
        if not any(ref_stats):
            continue
        if ref_link.startswith('t.me'):
            ref_id = int(ref_link.split('ref')[1])
            try:
                user = bot.get_chat_member(ref_id, ref_id).user
            except:
                ref_link = str(ref_id)
            else:
                ref_link = user.username if user.username else user.full_name
        make_sure_that_sheet_exists(service, REFERAL_STATS_SHEET_ID, ref_link)
        values = service.spreadsheets().values().get(
            spreadsheetId = REFERAL_STATS_SHEET_ID,
            range = f'{ref_link}!A1:A',
            majorDimension = 'ROWS'
        ).execute()
        first_row = 1
        row_of_statistics = first_row
        if 'values' not in values:
            values = [[
                'Дата', 'Активации бота', '% из активации в пробн', 'Активации пробного', 
                '% из пробно в продажи', 'Продажи', 'Сумма продаж', 'LTV', '% в повторные', 
                '% из активации бота в продажи', 'Ср доход'
            ]]
            row_of_statistics += 1
        else:
            row_of_statistics = first_row = len(values['values']) + 1
            values = []
        values.append([
            for_date.strftime(DATE_FORMAT),                                               # date 
            ref_stats[0],                                                                 # activations
            F'=D{row_of_statistics}/B{row_of_statistics}%',                               # % of activation -> trial
            ref_stats[1],                                                                 # trial activations
            '{0:.2f}'.format(ref_stats[7]/max(ref_stats[1], 1) * 100).replace('.', ','),  # % of trial -> paid sub
            ref_stats[3],                                                                 # payments number
            str(ref_stats[4]),                                                            # payments sum
            '',                                                                           # LTV
            '{0:.2f}'.format(ref_stats[6]/max(ref_stats[3], 1) * 100).replace('.', ','),  # % of repeated payments
            '{0:.2f}'.format(ref_stats[3]/max(ref_stats[0], 1) * 100).replace('.', ','),  # % of activation -> paid sub
            '{0:.2f}'.format(ref_stats[4] / max(ref_stats[2], 1)).replace('.', ','),      # average income (for a client)
        ])
        service.spreadsheets().values().batchUpdate( # upload real sum of payments
            spreadsheetId = REFERAL_STATS_SHEET_ID, 
            body = {
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {
                        "range": f"{ref_link}!A{first_row}:K{row_of_statistics}",
                        "majorDimension": "ROWS",
                        "values": values
                    }
                ]
            }
        ).execute()
        sleep(60)
