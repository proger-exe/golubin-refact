from __future__ import annotations
from typing import Union

from src.data.modules.refs import *
from src.utils.client import Client 
from decimal import Decimal
from mysql.connector.connection import MySQLConnection as Connection
from mysql.connector.cursor import MySQLCursor as Cursor
from src.apis.db import *

class ReferalClient():

	def __init__(
		self, id: int, ref_status: int, balance: Decimal, invited_by: int, 
	    percent1: Decimal = DEFAUL_REFERAL_PAYMENT_PERCENT, 
		required_referal_number: int = DEFAULT_NUM_OF_ACTIVE_REFERALS_TO_GET_BIGGER_PERCENT,
		percent2: Decimal = DEFAULT_PAYMENT_PERCENT_FOR_REFERAL_WITH_BIG_AMOUNT_OF_REFERS,
		show_notifications: bool = True
	):
		self.__id = id
		self.__ref_status = ref_status
		self.__balance = balance
		self.__inviter_id = invited_by
		self.__percent1 = Decimal(str(percent1))
		self.__required_referal_number = required_referal_number
		self.__percent2 = Decimal(str(percent2))
		self.__show_notifications = show_notifications

	@staticmethod
	def has_client_id(id: int) -> bool:
		conn, cursor = get_connection_and_cursor()
		cursor.execute(f'SELECT COUNT({CLIENT_ID}) FROM {REFERAL_INFO_TABLE} WHERE {CLIENT_ID} = {id}')
		count = cursor.fetchall()[0][0]
		close_connection_and_cursor(conn, cursor)
		return count

	@staticmethod
	def get_client_by_id(id: int) -> Union[ReferalClient, None]:
		conn, cursor = get_connection_and_cursor()
		cursor.execute(f'SELECT * FROM {REFERAL_INFO_TABLE}'
			f' WHERE {CLIENT_ID} = {id}')
		result = cursor.fetchall()
		if not result:
			return None
		close_connection_and_cursor(conn, cursor)
		return ReferalClient(*result[0])

	@property
	def id(self) -> int:
		return self.__id
	
	@property
	def referal_status(self) -> int:
		return self.__ref_status
	@referal_status.setter
	def referal_status(self, val: int):
		self.__ref_status = val

	@property
	def balance(self) -> Decimal:
		return self.__balance
	@balance.setter
	def balance(self, val: Decimal):
		self.__balance = val

	@property
	def referal_id(self) -> int: 
		''' the id of the person who invited a client'''
		return self.__inviter_id

	@property
	def percent1(self) -> Decimal: 
		""" the percent of commission from payemnts which comes before a referal hits his 'required_referal_number'"""
		return self.__percent1
	@percent1.setter
	def percent1(self, val: Decimal):
		self.__percent1 = val

	@property
	def required_referal_number(self) -> int: 
		return self.__required_referal_number
	@required_referal_number.setter
	def required_referal_number(self, val: int):
		self.__required_referal_number = val

	@property
	def percent2(self) -> Decimal: 
		return self.__percent2
	@percent2.setter
	def percent2(self, val: Decimal):
		self.__percent2 = val

	@property
	@Client.database_working
	def refers_num(self, conn: Connection, cursor: Cursor) -> int:
		cursor.execute(f'SELECT COUNT({CLIENT_ID}) FROM {REFERAL_INFO_TABLE} WHERE {INVITED_BY} = {self.__id}')
		return cursor.fetchall()[0][0]
	
	@property
	def show_notifications(self) -> bool: 
		return self.__show_notifications
	@show_notifications.setter
	def show_notifications(self, val: bool):
		self.__show_notifications = val

	@Client.database_working
	def get_refer_ids(self, conn: Connection, cursor: Cursor) -> tuple:
		cursor.execute(f'SELECT {CLIENT_ID} FROM {REFERAL_INFO_TABLE} WHERE {INVITED_BY} = {self.__id}')
		return [i[0] for i in  cursor.fetchall()]

	@Client.database_working
	def add_to_db(self, conn: Connection, cursor: Cursor):
		cursor.execute(f'SELECT COUNT({CLIENT_ID}) FROM {REFERAL_INFO_TABLE} WHERE {CLIENT_ID} = {self.__id}')
		if cursor.fetchall()[0][0] != 0:
			cursor.execute(
				f'UPDATE {REFERAL_INFO_TABLE} SET '
				f'{REFERAL_STATUS} = {self.__ref_status}, {BALANCE} = {self.__balance}, '
				f'{INVITED_BY} = {self.__inviter_id}, {REF_PERCENT_FOR_LITTLE_AMOUNT_OF_REFERALS} = {self.__percent1}, '
				f'{REQUIRED_AMOUNT_OF_REFERALS_TO_GET_BIGGER_PERCENT} = {self.__required_referal_number}, '
				f'{REF_PERCENT_FOR_BIG_AMOUNT_OF_REFERALS} = {self.__percent2}, '
				f'{SHOW_NOTIFICATIONS} = {self.__show_notifications} '
				f'WHERE {CLIENT_ID} = {self.__id}'
			)
		else:
			cursor.execute(
				f'INSERT INTO {REFERAL_INFO_TABLE} VALUES({self.__id}, {self.__ref_status}, {self.__balance}, '
				f'{self.__inviter_id}, {self.__percent1}, {self.__required_referal_number}, {self.__percent2}, '
				f'{self.__show_notifications})'
			)
		commit_and_close_connection_and_cursor(conn, cursor)

	@staticmethod
	def transfer_ref_info(from_id: int, to_id: int):
		conn, cursor = get_connection_and_cursor()
		cursor.execute(f'DELETE FROM {REFERAL_INFO_TABLE} WHERE {CLIENT_ID} = {to_id}')
		cursor.execute(f'UPDATE {REFERAL_INFO_TABLE} SET {CLIENT_ID} = {to_id} WHERE {CLIENT_ID} = {from_id}')
		cursor.execute(f'UPDATE {REFERAL_INFO_TABLE} SET {INVITED_BY} = {to_id} WHERE {INVITED_BY} = {from_id}')
		commit_and_close_connection_and_cursor(conn, cursor)