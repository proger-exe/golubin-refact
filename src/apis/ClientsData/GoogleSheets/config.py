from src.data.config import TESTING

CLIENTS_SPREAD_SHEETS = 'clients_google_sheets'
CLIENT_ID = 'client_id'
SPREAD_SHEET_ID = 'spreadsheet_id'
SHEET_ID = 'sheet_id'
DUPLICATE_MYSQL_ENTRY_CODE = 1062

GOOGLE_SHEETS_BUTTON = '📋 Гугл таблицы'
ADD_GOOGLE_SHEET = 'add_gsh'
DEL_GOOGLE_SHEET = 'del_gsh'
GOOGLE_SHEET_URL_TEMPLATE = 'https://docs.google.com/spreadsheets/d/{0}/edit#gid={1}'
GOOGLE_SPREAD_SHEET_EXAMPLE = 'https://docs.google.com/spreadsheets/d/1jUeqNv5RqNominAXJ6vD6JCPq55pgNc98jyY5H3yZYM/edit?usp=sharing'
GOOGLE_SERVICE_EMAIL = 'golubin-bot@golubin-bot.iam.gserviceaccount.com'
photos_which_describes_how_to_pludge_google_sheets =  (
    'AgACAgIAAxkDAAEBgGxi1lfJvDpKkJ7zVM_7yScipAFh6gAC1LsxG2uLsErwUfYtWpo29wEAAwIAA3MAAykE',
    'AgACAgIAAxkDAAEBgG1i1lfqtq4b5IMUF3U9OD6lDRz2wgAC1bsxG2uLsEo9yCS43-JyqAEAAwIAA3MAAykE',
    'AgACAgIAAxkDAAEBgG5i1lgLIHVNN2RdMLo-WhWDmkz-PAAC1rsxG2uLsErDD8qObMAMMAEAAwIAA3MAAykE',
    'AgACAgIAAxkDAAEBgG9i1lgviTQpwstNhyw9nBG9YKGkVwAC17sxG2uLsEpnRS82UNW0OQEAAwIAA3MAAykE'
) if not TESTING else (
    'AgACAgIAAxkDAAIX72LWVNfXKTqizUij3dKoxSxJeaViAALPwDEb1smwSqR2zcQNfnmgAQADAgADcwADKQQ',
    'AgACAgIAAxkDAAIX8WLWVWDDfDFpXsIuUXe4p0-UDhagAALVwDEb1smwSnNU_PPPuV_rAQADAgADcwADKQQ',
    'AgACAgIAAxkDAAIX8mLWVaLjr-fwzjejiK_zQA9oFIorAALXwDEb1smwSvNw_Wo4HNgMAQADAgADcwADKQQ',
    'AgACAgIAAxkDAAIX82LWVc_lwnQbEXCnvH8dqJ0WCl55AALYwDEb1smwSmyJmVfI1QAB0gEAAwIAA3MAAykE'
)
GOOGLE_SHEET_CREATING_REQUESTS_FILE = 'ClientsData/GoogleSheets/create_google_sheet_table.json'
CREDENTIAL_FILES = 'ClientsData/GoogleSheets/keys.json'
STANDART_BOT_SHEET_NAME = 'Статистика Golubin Bot'
NUMBER_OF_ROW_FIELDS_IN_GOOGLE_SPRSHT = 5 # fields for each category stat: date, targets, untargets, total, %of targets
GOOGLE_SHEETS_API_URL = 'https://www.googleapis.com/auth/spreadsheets'
GOOGLE_DRIVE_API_URL = 'https://www.googleapis.com/auth/drive'