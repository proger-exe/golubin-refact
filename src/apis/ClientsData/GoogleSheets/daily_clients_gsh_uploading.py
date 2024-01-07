from datetime import date, datetime
import json
import logging
from time import sleep
import pandas as pd
from src.apis.ClientsData import Accounts
from typing import List, Tuple
from Votes import Vote
from Votes.config import *
from src.keyboards.bot_votes_keyboards import check_if_client_is_allowed_to_get_vote_buttons
from .config import *
from .clients_google_sheets import *
from oauth2client.service_account import ServiceAccountCredentials
import httplib2, apiclient

credentials = ServiceAccountCredentials.from_json_keyfile_name(
        CREDENTIAL_FILES, [GOOGLE_SHEETS_API_URL, GOOGLE_DRIVE_API_URL])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets','v4', http = httpAuth)


def connect_to_gsh_and_get_sheet_id(spread_sheet_id: str) -> int:
    with open(GOOGLE_SHEET_CREATING_REQUESTS_FILE) as f:
        create_table_requests = json.load(f)
    try:
        service.spreadsheets().values().get(
            spreadsheetId = spread_sheet_id,
            range = 'A1:A1',
            majorDimension = 'COLUMNS'
        ).execute()
    except:
        return -1
    sheet_id, created = make_sure_that_bot_sheet_exists_and_get_id(spread_sheet_id, create_table_requests)
    try:
        if not created:
            fill_table = not check_if_header_in_table_are_fine(spread_sheet_id, 
                create_table_requests['set-columns']['data'][0]['values'])
        else:
            fill_table = True
        if fill_table:
            service.spreadsheets().values().batchUpdate(
                spreadsheetId = spread_sheet_id, body = create_table_requests['set-columns']
            ).execute()
            set_sheet_id_in_create_table_requests(create_table_requests, sheet_id)
            service.spreadsheets().batchUpdate(
                spreadsheetId = spread_sheet_id,
                body = create_table_requests['set-formatting']
            ).execute()
    except:
        logging.critical(f'FAILED TO MAKE NEW TABLE FOR CLIENT("{spread_sheet_id}", {sheet_id}):', exc_info = True)
    return sheet_id

def make_sure_that_bot_sheet_exists_and_get_id(spread_sheet_id: str, 
create_table_requests: dict = None) -> Tuple[int, bool]:
    '''
    returns id of sheet and bool-value of whether a sheet has been created
    '''
    if not create_table_requests:
        with open(GOOGLE_SHEET_CREATING_REQUESTS_FILE) as f:
            create_table_requests = json.load(f)
    try:
        service.spreadsheets().values().get(
            spreadsheetId = spread_sheet_id,
            range = f'{STANDART_BOT_SHEET_NAME}!A1:A1',
            majorDimension = 'COLUMNS'
        ).execute()
    except:
        return create_bot_table_and_get_id(spread_sheet_id, create_table_requests['create']), True
    else:
        return find_sheet_id(service, spread_sheet_id, STANDART_BOT_SHEET_NAME), False

def create_bot_table_and_get_id(spread_sheet_id: str, create_table_requests: dict) -> int:
    response = service.spreadsheets().batchUpdate(
        spreadsheetId = spread_sheet_id,
        body =  create_table_requests
    ).execute()
    return response['replies'][0]['addSheet']['properties']['sheetId']

def find_sheet_id(service, spread_sheet_id: int, sheet_title: str) -> int:
    sheets = service.spreadsheets().get(spreadsheetId = spread_sheet_id).execute()['sheets']
    for sheet in sheets:
        if sheet['properties']['title'] == sheet_title:
            return sheet['properties']['sheetId']
    return -1

def set_sheet_id_in_create_table_requests(requests: dict, sheet_id: int):
    for h in list(requests):
        if h == 'sheetId':
            requests[h] = sheet_id
        if isinstance(requests[h], dict):
            set_sheet_id_in_create_table_requests(requests[h], sheet_id)
        if isinstance(requests[h], list):
            for request in requests[h]:
                if isinstance(request, dict):
                    set_sheet_id_in_create_table_requests(request, sheet_id)

def check_if_header_in_table_are_fine(spread_sheet_id: str, standart_headers: List[List[str]]) -> bool:
    result = service.spreadsheets().values().get(
        spreadsheetId = spread_sheet_id,
        range = f'{STANDART_BOT_SHEET_NAME}!A1:C55',
        majorDimension = 'ROWS'
    ).execute()
    if not 'values' in result:
        return False
    return result['values'] == standart_headers

def upload_statistics_for_all_clients(date: date):
    clients = get_all_clients_with_google_sheets()
    for i, client in enumerate(clients):
        upload_statistics_of_client(client, date)
        if i < len(clients) - 1:
            sleep(59) # it is necessary to prevent quotes overexceeding

def upload_statistics_of_client(client: int, date: date):
    statistics = {}
    if not check_if_client_is_allowed_to_get_vote_buttons(client):
        return
    accounts = [client] + Accounts.get_all_accounts_of(client)
    for account in accounts:
        votes = Vote.findByFilter(date = date, user_id = account)
        for vote in votes:
            if not vote.category in statistics:
                statistics[vote.category] = {
                    TARGET: 0,
                    NOT_TARGET: 0,
                    'total': 0
                }
            statistics[vote.category]['total'] += 1
            if vote.vote_type != SPAM:
                statistics[vote.category][vote.vote_type] += 1
    spread_sheet_id, sheet_id = get_google_sheet_of_client(client)
    for category in statistics:
        export_to_gsh(
            spread_sheet_id, sheet_id, category, date, statistics[category][TARGET], statistics[category][NOT_TARGET],
            statistics[category]['total'], (statistics[category][TARGET] / statistics[category]['total']) * 100
        )
        sleep(1)

def export_to_gsh(spreadsheet_id: str, sheet_id: int, category: int, date: date, 
targets: int, untargets: int, total: int, tar_percent: float):
    start_row = category * NUMBER_OF_ROW_FIELDS_IN_GOOGLE_SPRSHT + 1 # first row is head and rows 
    values = service.spreadsheets().values().get(
        spreadsheetId = spreadsheet_id,
        range = f'{STANDART_BOT_SHEET_NAME}!A{start_row}:AK{start_row + NUMBER_OF_ROW_FIELDS_IN_GOOGLE_SPRSHT - 1}',
        majorDimension = 'ROWS',
        valueRenderOption = 'FORMULA'
    ).execute()
    sleep(1)
    columns = ['A']
    for i in range(len(values['values'][0])-1):
        columns.append(get_next_column(columns[-1]))
    start_df_index = 1
    df = pd.DataFrame(values['values'], 
        columns = columns,
        index = range(1, len(values['values']) + 1)
    )
    first_column = ''
    first_date = ''
    if 'D' in df:
        first_date = df.D[1]
    if first_date: # not empty cell
        first_date = datetime.strptime(first_date, '%d.%m.%Y').date()
        first_column = sum_column('D', (date - first_date).days)
        while True:
            if first_column not in df:
                break
            if df[first_column][start_df_index] == 'Итог':
                break
            if df[first_column][start_df_index] == 'нед':
                first_column = get_next_column(first_column)
                continue
            current_date = datetime.strptime(df[first_column][start_df_index], '%d.%m.%Y')
            if current_date.date() == date:
                break
            first_column = get_next_column(first_column)
    else:
        first_column = 'D'
    total_column = find_total_column(df)
    total_column_existed = True
    if not total_column:
        total_column_existed  = False
        total_column = gen_column_with_total_info('Итог', first_column, start_row)
    values = [date.strftime('%d.%m.%Y'), targets, untargets, total, '{0:.1f}'.format(tar_percent).replace('.', ',')]
    service.spreadsheets().batchUpdate(
        spreadsheetId = spreadsheet_id,
        body = {
            'requests': [
                {
                    "appendDimension": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "length": 5
                    }
                },
                {
                    "repeatCell": {
                        'range': {
                            'sheetId': sheet_id,
                            "startRowIndex": start_row-1,
                            "endRowIndex": start_row,
                            "startColumnIndex": get_index_of_column(first_column),
                            "endColumnIndex": get_index_of_column(first_column) + 1
                        },
                        'cell': {
                            "userEnteredFormat": {
                                "numberFormat": {
                                    "type": "TEXT"
                                }
                            }
                        },
                        "fields": "userEnteredFormat.numberFormat"
                    }
                },
                {
                    "repeatCell": {
                        'range': {
                            'sheetId': sheet_id,
                            "startRowIndex": start_row+3,
                            "endRowIndex": start_row+4,
                            "startColumnIndex": get_index_of_column(first_column),
                            "endColumnIndex": get_index_of_column(first_column) + 1
                        },
                        'cell': {
                            "userEnteredFormat": {
                                "numberFormat": {
                                    "type": "NUMBER"
                                }
                            }
                        },
                        "fields": "userEnteredFormat.numberFormat"
                    }
                }
            ]
        }
    ).execute()
    sleep(1)
    _range = f"{STANDART_BOT_SHEET_NAME}!{first_column}{start_row}:" \
        f'{first_column}{start_row+NUMBER_OF_ROW_FIELDS_IN_GOOGLE_SPRSHT-1}'
    service.spreadsheets().values().batchUpdate(
        spreadsheetId = spreadsheet_id, 
        body = {
            "valueInputOption": "USER_ENTERED", 
            "data": [{
                "range": _range,
                "majorDimension": "COLUMNS",
                "values": [values]
            }]
    }).execute()
    sleep(1)
    attached_week_total = False
    if date.weekday() == 6: # sunday
        suggested_week_column = get_next_column(first_column)
        if suggested_week_column not in df or df[suggested_week_column][start_df_index] != 'нед': 
            attached_week_total = True
            values = gen_column_with_total_info('нед', first_column, start_row)
            first_column = suggested_week_column
            service.spreadsheets().values().batchUpdate(
                spreadsheetId = spreadsheet_id, 
                    body = {
                        "valueInputOption": "USER_ENTERED", 
                        "data": [{
                            "range": f"{STANDART_BOT_SHEET_NAME}!{first_column}{start_row}:"
                                f'{first_column}{start_row + NUMBER_OF_ROW_FIELDS_IN_GOOGLE_SPRSHT - 1}',
                            "majorDimension": "COLUMNS",     
                            "values": [values]
                        }]
                    }
            ).execute()
            sleep(1)
    if not total_column_existed:
        last_daily_stat_column = first_column if not attached_week_total else get_last_column(first_column)
        for i in range(1, len(total_column)):
            # it is (for example) '=SUM(B7:B7)' now, it should be =SUM(B7) or =SUM(B7;C7)
            row = total_column[i][:total_column[i].index('(')+1] + last_daily_stat_column + str(start_row+i) + ')'
            total_column[i] = row
    else:
        last_daily_stat_column = first_column if not attached_week_total else get_last_column(first_column)
        for i in range(1, len(total_column)):
            row = total_column[i][:total_column[i].index(')')] + ';' + last_daily_stat_column + str(start_row+i) + ')'
            total_column[i] = row
    first_column = get_next_column(first_column)
    service.spreadsheets().values().batchUpdate(
        spreadsheetId = spreadsheet_id, 
            body = {
                "valueInputOption": "USER_ENTERED", 
                "data": [{
                    "range": f"{STANDART_BOT_SHEET_NAME}!{first_column}{start_row}:"
                        f'{first_column}{start_row+NUMBER_OF_ROW_FIELDS_IN_GOOGLE_SPRSHT-1}',
                    "majorDimension": "COLUMNS",     
                    "values": [total_column]
                }]
            }
    ).execute()
    sleep(1)

def get_next_column(letter: str) -> str:
    if len(letter) == 1:
        if letter == 'Z':
            return 'AA'
        return chr(ord(letter) + 1)
    if letter[-1] == 'Z':
        return get_next_column(letter[:-1]) + 'A'
    letter = letter[:-1] + chr(ord(letter[-1]) + 1)
    return letter

def sum_column(letter: str, num: int) -> str:
    for _ in range(num):
        if num > 0:
            letter = get_next_column(letter)
        elif num < 0:
            letter = get_last_column(letter)
    return letter

def find_total_column(df):
    first_column = df.columns[-1]
    while df[first_column][1] != 'Итог':
        first_column = get_last_column(first_column)
        if first_column == 'D' or (len(first_column)==1 and ord(first_column) <= ord('D')):
            break
    if first_column not in df or df[first_column][1] != 'Итог':
        return []
    return list(df[first_column])

def gen_column_with_total_info(head, first_column, first_row):
    first_column_to_count_total = sum_column(first_column, -6)
    if len(first_column)==1 and ord(first_column) <= ord('D'):
        first_column = 'D'
    range = f'{first_column_to_count_total}'+'{0}:'+f'{first_column}'+'{0}'
    return [
        head, 
        f'=SUM(' + range.format(first_row+1) + ')',
        f'=SUM(' + range.format(first_row+2) + ')',
        f'=SUM(' + range.format(first_row+3) + ')',
        f'=AVERAGE(' + range.format(first_row+4) + ')',
    ]

def get_last_column(letter: str) -> str:
    if len(letter) == 1:
        if letter == 'A':
            return ''
        return chr(ord(letter) - 1)
    if letter[-1] == 'A':
        return get_last_column(letter[: -1]) + 'Z'
    letter = letter[:-1] + chr(ord(letter[-1]) - 1)
    return letter

def get_index_of_column(column: str) -> int:
    ord_A = ord('A')
    if len(column) == 1:
        return ord(column) - ord_A
    c = 'Z'
    n = 25
    while c != column:
        c = get_next_column(c)
        n += 1
    return n