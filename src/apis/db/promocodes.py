from datetime import datetime
from decimal import Decimal
from src.apis.db import *
from src.utils.Promocodes.config import *
from typing import List, Tuple, Union
from mysql.connector.cursor import MySQLCursor as Cursor

def add_promocode(
	promocode: str, 
	category: Union[int, str], 
	trial_days: int = 0, 
	sale_size: float = 0.0, 
	for_period: Union[int, str] = 'NULL', 
	due_date: datetime = 'NULL', 
	from_refer: int = 0, 
	forever: bool = False
):
	if trial_days and sale_size:
		raise(ValueError('Promocodes are not allowd to be for trial days and sale at the one time'))
	if len(promocode) > PROMOCODE_MAX_LENGTH:
		raise(ValueError(f'Length of "{promocode}" is greater than max allowed: {PROMOCODE_MAX_LENGTH}'))
	if trial_days and forever:
		raise(ValueError('Promocodes with trial period can not be forever'))
	conn, cursor = get_connection_and_cursor()
	if promocode_is_in_db(promocode, cursor):
		raise(ValueError(f'The promocode "{promocode}" is already in database'))
	promocode = promocode.replace('"', '\\"')
	cursor.execute(
		f'INSERT INTO {PROMOCODES_TABLE} VALUES(DEFAULT, "{promocode}", {category}, {trial_days}, '
		f'{sale_size}, {for_period}, "{due_date.strftime(TIMESTAMP_FORMAT)}", {from_refer}, {forever})'
	)
	commit_and_close_connection_and_cursor(conn, cursor)

def promocode_is_in_db(promocode: str, cursor: Cursor = None) -> bool:
	conn = None
	if not cursor:
		conn, cursor = get_connection_and_cursor()
	cursor.execute(f'SELECT COUNT({PROMOCODE}) FROM {PROMOCODES_TABLE} WHERE {PROMOCODE} LIKE "{get_right_str(promocode)}"')
	result = cursor.fetchall()[0][0] != 0
	if conn:
		close_connection_and_cursor(conn, cursor)
	return result

def get_promocode_action(promocode: str) -> Tuple[int, int, Decimal, int, date]:
	conn, cursor = get_connection_and_cursor()
	promocode = promocode.replace('"', '\\"')
	cursor.execute(
		f'SELECT {ACTION_CATEGORY}, {TRIAL_DAYS}, {SALE} / 100, {FOR_PERIOD}, {DUE_TIME} FROM {PROMOCODES_TABLE} '
		f'WHERE {PROMOCODE} = "{promocode}"'
	)
	result = cursor.fetchall()
	if not result:
		raise(ValueError(f'There is no "{promocode}" in database'))
	close_connection_and_cursor(conn, cursor)
	return result[0]

def get_promocode_due_date(promocode: str) -> datetime:
	conn, cursor = get_connection_and_cursor()
	promocode = promocode.replace('"', '\\"')
	cursor.execute(f'SELECT {DUE_TIME} FROM {PROMOCODES_TABLE} WHERE {PROMOCODE} = "{promocode}"')
	result = cursor.fetchall()
	close_connection_and_cursor(conn, cursor)
	if not result:
		return None
	return result[0][0]

def get_promocode_refer(promocode: str) -> int:
	conn, cursor = get_connection_and_cursor()
	promocode = promocode.replace('"', '\\"')
	cursor.execute(f'SELECT {FROM_REFER} FROM {PROMOCODES_TABLE} WHERE {PROMOCODE} = "{promocode}"')
	result = cursor.fetchall()
	close_connection_and_cursor(conn, cursor)
	if not result:
		return None
	return result[0][0]

def delete_promocode(promocode: str):
	conn, cursor = get_connection_and_cursor()
	promocode = promocode.replace('"', '\\"')
	cursor.execute(f'DELETE FROM {PROMOCODES_TABLE} WHERE {PROMOCODE} = "{promocode}"')
	commit_and_close_connection_and_cursor(conn, cursor)

def client_used_promocode(client_id: int, promocode: str) -> bool:
	conn, cursor = get_connection_and_cursor()
	cursor.execute(
		f'SELECT COUNT({CLIENT_ID}) FROM {USED_PROMOCODES_TABLE} '
		f'WHERE {USED_PROMOCODES} LIKE "%;{get_right_str(promocode)};%" AND {CLIENT_ID} = {client_id}'
	)
	result = cursor.fetchall()
	close_connection_and_cursor(conn, cursor)
	return result[0][0] != 0

def get_all_promocodes() -> tuple:
	conn, cursor = get_connection_and_cursor()
	cursor.execute(f'SELECT * FROM {PROMOCODES_TABLE}')
	result = cursor.fetchall()
	close_connection_and_cursor(conn, cursor)
	return result

def get_last_activated_endless_promocode(client_id: int, for_category: int = None, for_period: int = None
) -> Union[str, None]:
	'''returns promocode name, it's category, sale size, period and id of referer which it is from'''
	conn, cursor = get_connection_and_cursor()
	category_filter = '= NULL' if for_category is None else f'IN (NULL, {for_category})'
	period_filter = '' if for_period is None else f'AND {FOR_PERIOD} IN (NULL, {for_period})'
	cursor.execute(f'SELECT {PROMOCODE} FROM {PROMOCODES_TABLE} AS pcd'
		f' WHERE {FOREVER} AND {CATEGORY} {category_filter}   {period_filter} AND '
			f'(SELECT {CLIENT_ID} FROM {USED_PROMOCODES_TABLE} WHERE {USED_PROMOCODES} LIKE CONCAT('
				f'"%;", pcd.{PROMOCODE}, ";%") AND {CLIENT_ID} = {client_id}'
			f')'
	)
	all_eternal_pcds = [i[0] for i in cursor.fetchall()]
	if not all_eternal_pcds:
		close_connection_and_cursor(conn, cursor)
		return None
	cursor.execute(f'SELECT {USED_PROMOCODES} FROM {USED_PROMOCODES_TABLE} WHERE {CLIENT_ID} = {client_id}')
	promocodes = [i for i in cursor.fetchall()[0][0].split(';')]
	for p in promocodes[::-1]:
		if p in all_eternal_pcds:
			close_connection_and_cursor(conn, cursor)
			return p
	close_connection_and_cursor(conn, cursor)
	return None
	
def set_promocode_as_used_by_client(client_id: int, promocode: str):
	conn, cursor = get_connection_and_cursor()
	cursor.execute(f'SELECT COUNT({CLIENT_ID}) FROM {USED_PROMOCODES_TABLE} WHERE {CLIENT_ID} = {client_id}')
	promocode = promocode.replace('"', '\\"')
	if cursor.fetchall()[0][0]:
		cursor.execute(
			f'UPDATE {USED_PROMOCODES_TABLE} SET {USED_PROMOCODES} = CONCAT({USED_PROMOCODES}, "{promocode};") '
			f'WHERE {CLIENT_ID} = {client_id}'
		)
	else:
		cursor.execute(f'INSERT INTO {USED_PROMOCODES_TABLE} VALUES({client_id}, ";{promocode};")')
	commit_and_close_connection_and_cursor(conn, cursor)

def set_endless_sale_on_promocode(promocode: str):
	conn, cursor = get_connection_and_cursor()
	promocode = promocode.replace('"', '\\"').replace('\\', '\\\\')
	try:
		if not promocode_is_in_db(promocode, cursor):
			raise ValueError(f'There is not promocode "{promocode}" in database')
		cursor.execute(
			f'SELECT COUNT({FOREVER}) FROM {PROMOCODES_TABLE} WHERE {PROMOCODE} = "{promocode}" AND {TRIAL_DAYS}')
		if cursor.fetchall()[0][0]:
			raise ValueError(f'The promocode "{promocode}" is trial')
	except Exception as e:
		close_connection_and_cursor(conn, cursor)
		raise e
	cursor.execute(f'UPDATE {PROMOCODES_TABLE} SET {FOREVER} = 1 WHERE {PROMOCODE} = "{promocode}"')
	commit_and_close_connection_and_cursor(conn, cursor)

def promocode_is_endless(promocode: str) -> bool:
	conn, cursor = get_connection_and_cursor()
	promocode = promocode.replace('"', '\\"')
	if not promocode_is_in_db(promocode, cursor):
		raise ValueError(f'There is not promocode "{promocode}" in database')
	cursor.execute(f'SELECT {FOREVER} FROM {PROMOCODES_TABLE} WHERE {PROMOCODE} = "{get_right_str(promocode)}"')
	result = cursor.fetchall()
	close_connection_and_cursor(conn, cursor)
	return result[0][0]

def transfer_promocodes_info(from_id: int, to_id: int):
	conn, cursor = get_connection_and_cursor()
	cursor.execute(f'DELETE FROM {USED_PROMOCODES_TABLE} WHERE {CLIENT_ID} = {to_id}')
	cursor.execute(f'UPDATE {PROMOCODES_TABLE} SET {FROM_REFER} = {to_id} WHERE {FROM_REFER} = {from_id}')
	cursor.execute(f'UPDATE {USED_PROMOCODES_TABLE} SET {CLIENT_ID} = {to_id} WHERE {CLIENT_ID} = {from_id}')
	commit_and_close_connection_and_cursor(conn, cursor)

def get_id_of_promocode(promocode: str) -> int:
	conn, cursor = get_connection_and_cursor()
	promocode = promocode.replace('"', '\\"').replace('\\', '\\\\')
	cursor.execute(f'SELECT {ID_COL} FROM {PROMOCODES_TABLE} WHERE {PROMOCODE} = "{promocode}"')
	result = cursor.fetchall()
	close_connection_and_cursor(conn, cursor)
	if not result:
		raise ValueError(f'There is no promocode "{promocode}"')
	return result[0][0]

def get_promocode_by_id(id: int) -> str:
	conn, cursor = get_connection_and_cursor()
	cursor.execute(f'SELECT {PROMOCODE} FROM {PROMOCODES_TABLE} WHERE {ID_COL} = {id}')
	result = cursor.fetchall()
	close_connection_and_cursor(conn, cursor)
	if not result:
		raise ValueError(f'There is no promocode with id {id}')
	return result[0][0]

def get_all_active_promocodes_of_refer(refer_id: int) -> List[str]:
	conn, cursor = get_connection_and_cursor()
	cursor.execute(f'SELECT {PROMOCODE} FROM {PROMOCODES_TABLE} WHERE {FROM_REFER}={refer_id} AND {DUE_TIME} > NOW()')
	result = cursor.fetchall()
	close_connection_and_cursor(conn, cursor)
	return [i[0] for i in result]