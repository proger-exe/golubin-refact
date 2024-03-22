import typing
from src.data.modules.history import *
from src.apis.db import *
from datetime import date
from decimal import Decimal

class ReferalPayment:
    def __init__(self, date: date, client_id: int, amount: Decimal):
        self.date = date
        self.client_id = client_id
        self.amount = amount

class ReferalPaymentsHistory:

    @staticmethod
    def save(payment: ReferalPayment):
        connection, cursor = get_connection_and_cursor()
        cursor.execute(f'INSERT INTO {REFERAL_PAYMENTS_TABLE} VALUES ("{payment.date.strftime("%Y-%m-%d")}", '
            f'{payment.client_id}, {payment.amount})')
        commit_and_close_connection_and_cursor(connection, cursor)

    def clientHasPayments(id: int) -> bool:
        connection, cursor = get_connection_and_cursor()
        cursor.execute(f'SELECT COUNT({CLIENT_ID_COL}) FROM {REFERAL_PAYMENTS_TABLE} WHERE {CLIENT_ID_COL} = {id}')
        result = cursor.fetchall()
        close_connection_and_cursor(connection, cursor)
        return result[0][0]

    def __getitem__(self, date: date) -> typing.List[ReferalPayment]:
        connection, cursor = get_connection_and_cursor()
        str_date = date.strftime("%Y-%m-%d")
        cursor.execute(f'SELECT {CLIENT_ID_COL}, {REF_AMOUNT} FROM {REFERAL_PAYMENTS_TABLE} WHERE {DATE} = "{str_date}"')
        result = cursor.fetchall()
        close_connection_and_cursor(connection, cursor)
        if not result:
            return []
        temp = result
        result = []
        for p in temp:
            result.append(ReferalPayment(date, p[0], p[1]))
        return result
    
    @staticmethod
    def transfer_payments(from_id: int, to_id: int):
        connection, cursor = get_connection_and_cursor()
        cursor.execute(f'UPDATE {REFERAL_PAYMENTS_TABLE} SET {CLIENT_ID} = {to_id} WHERE {CLIENT_ID} = {from_id}')
        commit_and_close_connection_and_cursor(connection, cursor)