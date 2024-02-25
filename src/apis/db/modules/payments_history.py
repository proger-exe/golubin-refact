from __future__ import annotations
from decimal import Decimal
from src.apis.db import *
import typing
from src.data.modules.history import *
from datetime import date, datetime, timedelta
from typing import Dict, List, Union

ID = 'id'

class Payment:
    def __init__(
        self,
        period: int, 
        amount: float, 
        referal_commission: float, 
        client_id: int, 
        comments: int = 0, 
        category: int = None,
        referal_link: str = ''
    ):
        self.period = period
        self.amount = Decimal(f'{amount}')
        self.referal_commission = referal_commission
        self.client_id = client_id
        self.comments = comments
        self.category = category
        self.__id: int = None
        self.time: datetime = None
        self.referal_link = referal_link

    @property
    def id(self) -> Union[int, None]:
        return self.__id

class PaymentHistory:
    
    def __init__(self, history: Dict[date, List[Payment]]):
        self.__history = history
        self.dates = tuple(self.__history.keys())

    def __getitem__(self, date: date):
        if not isinstance(date, globals()['date']):
            raise ValueError('Argument date must to be datetime.date, not '+str(type(date)))
        if not date in self.dates:
            raise KeyError(f'There is not date {date.strftime(DATE_FORMAT)} in history')
        return self.__history[date]

    @staticmethod
    def getForDate(date: date) -> List[Payment]:
        date = date.strftime('%Y-%m-%d')
        conn, cursor = get_connection_and_cursor()
        cursor.execute(f'SELECT {ID_COL}, {PERIOD}, {AMOUNT}, {REFERAL_COMMISION}, {CLIENT_ID}, {COMMENTS}, {CATEGORY}'
            f', {REFERAL_LINK} FROM {PAYMENTS_HISTORY} WHERE DATE({TIME}) = "{date}"')
        results = cursor.fetchall()
        close_connection_and_cursor(conn, cursor)
        payments = []
        for result in results:
            payment = Payment(*result[1:])
            payment._Payment__id = result[0]
            payment.time = date
            payments.append(payment)
        return payments

    @staticmethod
    def getForPeriod(start: date, end: date) -> PaymentHistory:
        history = {}
        conn, cursor = get_connection_and_cursor()
        cursor.execute(
            f'SELECT DATE({TIME}), {ID_COL}, {PERIOD}, {AMOUNT}, {REFERAL_COMMISION}, {CLIENT_ID}, {COMMENTS}, '
            f'{CATEGORY}, {REFERAL_LINK} FROM {PAYMENTS_HISTORY} WHERE "{start}" <= DATE({TIME}) '
            f'AND DATE({TIME}) <= "{end}"'
        )
        result = cursor.fetchall()
        close_connection_and_cursor(conn, cursor)
        current_d = start
        while current_d <= end:
            history[current_d] = []
            current_d += timedelta(days = 1)
        for payment in result:
            date_, id, period, amount, ref_com, client_id, comments, category, referal_link = payment
            payment = Payment(period, amount, ref_com, client_id, comments, category, referal_link)
            payment._Payment__id = id
            payment.time = date_
            history[date_].append(payment)
        return PaymentHistory(history)

    @staticmethod
    def get() -> PaymentHistory: # whole history
        conn, cursor = get_connection_and_cursor()
        cursor.execute(f'SELECT MIN(DATE({TIME})), MAX(DATE({TIME})) FROM {PAYMENTS_HISTORY}')
        result = cursor.fetchall()
        close_connection_and_cursor(conn, cursor)
        if not result:
            return PaymentHistory({})
        return PaymentHistory.getForPeriod(result[0][0], result[0][1])
    
    @staticmethod
    def savePaymentForDate(date: Union[datetime, date], payment: Payment):
        date = date.strftime(TIMESTAMP_FORMAT)
        referal_link = payment.referal_link.replace('\\', '\\\\').replace('"', '\\"')
        conn, cursor = get_connection_and_cursor()
        cursor.execute(
            f'INSERT INTO {PAYMENTS_HISTORY} VALUES (DEFAULT, "{date}", {payment.period}, {payment.amount}, '
            f'{payment.referal_commission}, {payment.client_id}, {payment.comments}, '
            f"{payment.category if payment.category != None else 'NULL'}, \"{referal_link}\")"
        )
        payment._Payment__id = cursor.lastrowid
        commit_and_close_connection_and_cursor(conn, cursor)
        payment.time = date

    @staticmethod
    def savePayment(payment: Payment):
        '''saves for today automatically'''
        PaymentHistory.savePaymentForDate(datetime.now(), payment)

    @staticmethod
    def findPaymentsBy(**kwargs) -> typing.List[Payment]:
        '''
        arguments:
            ID (int),
            TIME (datetime) - precise time of payment,
            DATE (date) - date of payment,
            DATE_PERIOD - (Tuple[date, date]) - period between which payment was made
            PERIOD (int),
            AMOUNT (decimal),
            REFERAL_COMMISION (decimal),
            CLIENT_ID (int),
            COMMENTS (int),
            CATEGORY (int),
            REFERAL_LINK (str),
            LIMIT (int) - maximum number of payments in result,
            ORDER (str) - desc or asc order of id
        '''
        payments = []
        values = list(kwargs.items())
        if not values:
            raise KeyError('There is no arguments to find payments')
        conditions = []
        order_by = f'ORDER BY {ID_COL} DESC'
        limit = ''
        for k, value in values:
            if k == 'ORDER':
                order_by = f'ORDER BY {ID_COL} {value}'
            elif k == 'LIMIT':
                limit = F'LIMIT {value}'
            elif k == 'DATE_PERIOD':
                date_format = TIMESTAMP_FORMAT.split()[0]
                conditions.append(
                    f'"{value[0].strftime(date_format)}" <= DATE({TIME}) AND '
                    f'DATE({TIME}) <= "{value[1].strftime(date_format)}"'
                )
            else:
                try:
                    if k == 'DATE': 
                        argument = f'DATE({TIME})' 
                    else:
                        argument = eval(k)
                except KeyError:
                    raise KeyError(f'There is no field {k} in payment object')
                if isinstance(value, str) and k != 'ORDER':
                    value = f'"{value}"'
                elif isinstance(value, date):
                    value = value.strftime(f'"{value.strftime(TIMESTAMP_FORMAT)}"')
                conditions.append(f'{argument} = {value}')
        conditions = '' if not conditions else 'WHERE ' + ' AND '.join(conditions)
        conn, cursor = get_connection_and_cursor()
        cursor.execute(
            f'SELECT {ID_COL}, {TIME}, {PERIOD}, {AMOUNT}, {REFERAL_COMMISION}, {CLIENT_ID}, {COMMENTS}, {CATEGORY}, '
            f'{REFERAL_LINK} FROM {PAYMENTS_HISTORY} {conditions} {order_by} {limit}'
        )
        result = cursor.fetchall()
        close_connection_and_cursor(conn, cursor)
        for payment_ in result:
            payment = Payment(*payment_[2:])
            payment._Payment__id = payment_[0]
            payment.time = payment_[1]
            payments.append(payment)
        return payments

    @staticmethod
    def deleteSavedPayment(payment: Payment):
        conn, cursor = get_connection_and_cursor()
        if payment.id != None:
            cursor.execute(f'DELETE FROM {PAYMENTS_HISTORY} WHERE {ID_COL} = {payment.id}')
        else:
            close_connection_and_cursor(conn, cursor)
            raise(ValueError('The payment has not been saved'))
        commit_and_close_connection_and_cursor(conn, cursor)

    @staticmethod
    def transferPayings(from_id: int , to_id: int):
        '''transfer all operations of one client_id to another'''
        conn, cursor = get_connection_and_cursor()
        cursor.execute(f'UPDATE {PAYMENTS_HISTORY} SET {CLIENT_ID} = {to_id} WHERE {CLIENT_ID} = {from_id}')
        commit_and_close_connection_and_cursor(conn, cursor)