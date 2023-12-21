from __future__ import annotations
from typing import Union
import typing
from mysql.connector import cursor
from mysql.connector.connection import MySQLConnection
from mysql.connector.cursor import MySQLCursor
from src.data.config import *
from datetime import datetime, timedelta
from collections.abc import Iterable
from src.apis.db import *

class Client:
    '''Class of service clients'''

    __TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'

    #decorator
    def database_working(func):
        def decorator(self):
            conn,cursor = get_connection_and_cursor()
            result = func(self, conn, cursor)
            close_connection_and_cursor(conn, cursor)
            return result
        return decorator
    
    def database_static_working(func):
        def decorator():
            conn,cursor = get_connection_and_cursor()
            result = func(conn, cursor)
            close_connection_and_cursor(conn, cursor)
            return result
        return decorator

    def __init__(
        self, id: int, payment_date: datetime,
        payment_period_end: datetime, sending_mode: int
    ):
        self.__id = id
        self.__last_payment_date = payment_date
        self.__payment_period_end = payment_period_end
        self.__sending_mode = sending_mode
    
    def __str__(self) -> str:
        return f'{self.__id};{self.get_str_payment_date()};{self.get_str_payment_date_end()};'\
               f'{self.__sending_mode}'    
    def get_str_payment_date(self) -> str:
        return self.__last_payment_date.strftime(Client.__TIMESTAMP_FORMAT)
    def get_str_payment_date_end(self) -> str:
        return self.__payment_period_end.strftime(Client.__TIMESTAMP_FORMAT)    

    @property
    def id(self) -> int:
        return self.__id
    
    @property
    @database_working
    def has_paid_period(self, conn: MySQLConnection, cursor: MySQLCursor) -> bool:
        cursor.execute(f'SELECT {IS_PAID} FROM '
            f'{CLIENTS_SUBSCRIBES} WHERE {ID_COL} = {self.__id} AND {CATEGORY} = {self.__sending_mode}')
        result = cursor.fetchall()
        if not result:
            return False
        else:
            return result[0][0]

    @has_paid_period.setter
    def has_paid_period(self, val: bool):
        conn, cursor = get_connection_and_cursor()
        cursor.execute(f'UPDATE {CLIENTS_SUBSCRIBES} SET '
            f'{IS_PAID} = {val} WHERE {ID_COL} = {self.__id} AND {CATEGORY} = {self.__sending_mode}')
        commit_and_close_connection_and_cursor(conn, cursor)

    @property
    @database_working
    def warning_status(self, conn: MySQLConnection, cursor: MySQLCursor) -> int:
        cursor.execute(f'SELECT {PAYMENT_ENDING_WARNING_STATUS} FROM '
            f'{CLIENTS_SUBSCRIBES} WHERE {ID_COL} = {self.__id} AND {CATEGORY} = {self.__sending_mode}')
        result = cursor.fetchall()
        if not result:
            return False
        else:
            return result[0][0]
    
    @warning_status.setter
    def warning_status(self, w_stat):
        conn, cursor = get_connection_and_cursor()
        cursor.execute(f'UPDATE {CLIENTS_SUBSCRIBES} SET '
            f'{PAYMENT_ENDING_WARNING_STATUS} = {w_stat} WHERE {ID_COL} = {self.__id} AND {CATEGORY} = {self.__sending_mode}')
        commit_and_close_connection_and_cursor(conn, cursor)
    
    @property
    def last_payment_date(self) -> datetime:
        return self.__last_payment_date
    
    @last_payment_date.setter
    def last_payment_date(self, date: datetime):
        conn, cursor = get_connection_and_cursor()
        self.__last_payment_date = date
        cursor.execute(f'UPDATE {CLIENTS_SUBSCRIBES} SET '
            f'{LAST_PAYMENT} = "{self.get_str_payment_date()}" WHERE {ID_COL} = {self.__id} AND '\
            f'{CATEGORY} = {self.__sending_mode}'
        )
        commit_and_close_connection_and_cursor(conn, cursor)

    @property
    @database_working
    def trial_start(self, conn: MySQLConnection,
        cursor: MySQLCursor
    ) -> datetime:
        cursor.execute(f'SELECT {TRIAL_START} FROM {TRIAL_PERIOD_INFO_TABLE} '
            f'WHERE {ID_COL} = {self.__id}  AND {CATEGORY} = {self.__sending_mode}')
        result = cursor.fetchall()
        if not result:
            return None
        else:
            return result[0][0]
    
    @property
    @database_working
    def trial_period_end(self, conn: MySQLConnection,
        cursor: MySQLCursor
    ) -> datetime:
        cursor.execute(f'SELECT {TRIAL_PERIOD_END} FROM {TRIAL_PERIOD_INFO_TABLE} '
            f'WHERE {ID_COL} = {self.__id} AND {CATEGORY} = {self.__sending_mode}')
        result = cursor.fetchall()
        if not result:
            return None
        else:
            return result[0][0]
    
    @property
    @database_working
    def sale_offering_date(
        self, conn: MySQLConnection, cursor: MySQLCursor
    ) -> datetime:
        cursor.execute(
            f'SELECT {SALE_OFFERING_DATE} FROM {TRIAL_PERIOD_INFO_TABLE} '
            f'WHERE {ID_COL} = {self.__id} AND {CATEGORY} = {self.__sending_mode}'
        )
        result = cursor.fetchall()
        if not result:
            return None
        else:
            return result[0][0]

    @sale_offering_date.setter
    def sale_offering_date(self, val: datetime):
        conn, cursor = get_connection_and_cursor()
        cursor.execute(
            f'UPDATE {TRIAL_PERIOD_INFO_TABLE} '
            f'SET {SALE_OFFERING_DATE} = "{val.strftime(Client.__TIMESTAMP_FORMAT)}" '
            f'WHERE {ID_COL} = {self.__id} AND {CATEGORY} = {self.__sending_mode}'
        )
        commit_and_close_connection_and_cursor(conn, cursor)

    @property
    @database_working
    def used_sale(
        self, conn: MySQLConnection, cursor: MySQLCursor
    ) -> bool:
        cursor.execute(f'SELECT {USED_SALE} FROM {TRIAL_PERIOD_INFO_TABLE} '
            f'WHERE {ID_COL} = {self.__id} AND {CATEGORY} = {self.__sending_mode}')
        result = cursor.fetchall()
        if not result:
            return False
        else:
            return result[0][0]

    @used_sale.setter
    def used_sale(self, val: bool):
        conn, cursor = get_connection_and_cursor()
        cursor.execute(
            f'UPDATE {TRIAL_PERIOD_INFO_TABLE} '
            f'SET {USED_SALE} = {val} '
            f'WHERE {ID_COL} = {self.__id} AND {CATEGORY} = {self.__sending_mode}'
        )
        commit_and_close_connection_and_cursor(conn, cursor)

    @property
    @database_working
    def is_asked_why_didnt_pay(
        self, conn: MySQLConnection, cursor: MySQLCursor
    ) -> bool:
        cursor.execute(f'SELECT {IS_ASKED} FROM {TRIAL_PERIOD_INFO_TABLE} '
            f'WHERE {ID_COL} = {self.__id} AND {CATEGORY} = {self.__sending_mode}')
        result = cursor.fetchall()
        if not result:
            return False
        else:
            return result[0][0]

    @is_asked_why_didnt_pay.setter
    def is_asked_why_didnt_pay(self, val: bool):
        conn, cursor = get_connection_and_cursor()
        cursor.execute(
            f'UPDATE {TRIAL_PERIOD_INFO_TABLE} '
            f'SET {IS_ASKED} = {val} '
            f'WHERE {ID_COL} = {self.__id} AND {CATEGORY} = {self.__sending_mode}'
        )
        commit_and_close_connection_and_cursor(conn, cursor)

    @property
    @database_working
    def is_aware_about_referal(
        self, conn: MySQLConnection, cursor: MySQLCursor
    ) -> bool:
        cursor.execute(f'SELECT {IS_AWARE_ABOUT_REFERAL} FROM '
            f'{CLIENTS_SUBSCRIBES} '
            f'WHERE {ID_COL} = {self.__id} AND {CATEGORY} = {self.__sending_mode}')
        result = cursor.fetchall()
        if not result:
            return False
        else:
            return result[0][0]

    @is_aware_about_referal.setter
    def is_aware_about_referal(self, val: bool):
        conn, cursor = get_connection_and_cursor()
        cursor.execute(
            f'UPDATE {CLIENTS_SUBSCRIBES} '
            f'SET {IS_AWARE_ABOUT_REFERAL} = {val} '
            f'WHERE {ID_COL} = {self.__id} AND {CATEGORY} = {self.__sending_mode}'
        )
        commit_and_close_connection_and_cursor(conn, cursor)    

    @property
    @database_working
    def max_pause_days(
        self, conn: MySQLConnection, cursor: MySQLCursor
    ) -> int:
        self.create_pauses_info_if_doesnt_have(conn, cursor)
        cursor.execute(f'SELECT {MAX_PAUSE_DAYS} FROM {CLIENTS_PAUSES} '
            f'WHERE {CLIENT_ID} = {self.__id} AND {CATEGORY} = {self.__sending_mode}')
        result = cursor.fetchall()
        if not result:
            return False
        else:
            return result[0][0]

    def create_pauses_info_if_doesnt_have(self, conn: MySQLConnection, cursor: MySQLCursor):
        try:
            cursor.execute(f'SELECT COUNT({CLIENT_ID}) FROM {CLIENTS_PAUSES} WHERE {CLIENT_ID} = {self.__id} '
                f'AND {CATEGORY} = {self.__sending_mode}')        
            if not cursor.fetchall()[0][0]:
                cursor.execute(f'INSERT INTO {CLIENTS_PAUSES} VALUES ({self.__id}, {self.__sending_mode}, 0, 0, NULL)')
                conn.commit()
        except Exception as e:
            close_connection_and_cursor(conn, cursor)
            raise(e)

    @max_pause_days.setter
    def max_pause_days(self, val: int):
        conn, cursor = get_connection_and_cursor()
        self.create_pauses_info_if_doesnt_have(conn, cursor)
        cursor.execute(
            f'UPDATE {CLIENTS_PAUSES} '
            f'SET {MAX_PAUSE_DAYS} = {val} '
            f'WHERE {CLIENT_ID} = {self.__id} AND {CATEGORY} = {self.__sending_mode}'
        )
        commit_and_close_connection_and_cursor(conn, cursor)

    @property
    @database_working
    def used_pause_days(
        self, conn: MySQLConnection, cursor: MySQLCursor
    ) -> int:
        self.create_pauses_info_if_doesnt_have(conn, cursor)
        cursor.execute(f'SELECT {PAUSE_DAYS_USED} FROM {CLIENTS_PAUSES} '
            f'WHERE {CLIENT_ID} = {self.__id} AND {CATEGORY} = {self.__sending_mode}')
        result = cursor.fetchall()
        if not result:
            return False
        else:
            return result[0][0]

    @used_pause_days.setter
    def used_pause_days(self, val: int):
        conn, cursor = get_connection_and_cursor()
        self.create_pauses_info_if_doesnt_have(conn, cursor)
        cursor.execute(
            f'UPDATE {CLIENTS_PAUSES} '
            f'SET {PAUSE_DAYS_USED} = {val} '
            f'WHERE {CLIENT_ID} = {self.__id} AND {CATEGORY} = {self.__sending_mode}'
        )
        commit_and_close_connection_and_cursor(conn, cursor)

    def increase_used_pause_days(self, by_days: int):
        conn, cursor = get_connection_and_cursor()
        self.create_pauses_info_if_doesnt_have(conn, cursor)
        cursor.execute(
            f'UPDATE {CLIENTS_PAUSES} '
            f'SET {PAUSE_DAYS_USED} = {PAUSE_DAYS_USED} + {by_days} '
            f'WHERE {CLIENT_ID} = {self.__id} AND {CATEGORY} = {self.__sending_mode}'    
        )
        commit_and_close_connection_and_cursor(conn, cursor)

    @property
    @database_working
    def unpause_date(self, conn: MySQLConnection, cursor: MySQLCursor) -> datetime:
        self.create_pauses_info_if_doesnt_have(conn, cursor)
        cursor.execute(f'SELECT {UNPAUSE_DATE} FROM {CLIENTS_PAUSES} WHERE '
            f'{CLIENT_ID} = {self.__id} AND {CATEGORY} = {self.__sending_mode}')
        result = cursor.fetchall()
        if not result:
            return None
        return result[0][0]

    @unpause_date.setter
    def unpause_date(self, date: datetime):
        conn, cursor = get_connection_and_cursor()
        self.create_pauses_info_if_doesnt_have(conn, cursor)
        set_str = ''
        if date:
            set_str = f'SET {UNPAUSE_DATE} = "{date.strftime(Client.__TIMESTAMP_FORMAT)}" '
        else:
            set_str = f'SET {UNPAUSE_DATE} = NULL '
        cursor.execute(
            f'UPDATE {CLIENTS_PAUSES} ' + set_str + \
            f'WHERE {CLIENT_ID} = {self.__id} AND {CATEGORY} = {self.__sending_mode}'    
        )
        commit_and_close_connection_and_cursor(conn, cursor)

    @property
    @database_working
    def is_offered_sale_after_end_of_trial(self, conn: MySQLConnection, cursor: MySQLCursor) -> bool:
        cursor.execute(
            f'SELECT COUNT({ID_COL}) FROM {TRIAL_PERIOD_INFO_TABLE} '
            f'WHERE {ID_COL} = {self.__id} AND {MSG_ID_WITH_SALE_AFTER_TRIAL_END} != 0 AND '
            f'{CATEGORY} = {self.__sending_mode}'
        )
        return cursor.fetchall()[0][0]

    @property
    @database_working
    def id_of_message_with_sale_after_end_of_trial(
        self, conn: MySQLConnection, cursor: MySQLCursor
    ) -> Union[int, None]:
        cursor.execute(
            f'SELECT {MSG_ID_WITH_SALE_AFTER_TRIAL_END} FROM {TRIAL_PERIOD_INFO_TABLE} '
            f'WHERE {ID_COL} = {self.__id} AND {CATEGORY} = {self.__sending_mode}' 
        )
        result = cursor.fetchall()
        if not result:
            return None
        else:
            return result[0][0]

    @id_of_message_with_sale_after_end_of_trial.setter
    def id_of_message_with_sale_after_end_of_trial(self, msg_id: int):
        conn, cursor = get_connection_and_cursor()
        cursor.execute(f'UPDATE {TRIAL_PERIOD_INFO_TABLE} SET {MSG_ID_WITH_SALE_AFTER_TRIAL_END} = {msg_id} '
            f'WHERE {ID_COL} = {self.__id} AND {CATEGORY} = {self.__sending_mode}')
        commit_and_close_connection_and_cursor(conn, cursor)

    @property
    def payment_period(self) -> int:
        return (self.__payment_period_end - \
            self.__last_payment_date).days
    
    @property
    def payment_end(self) -> datetime:
        return self.__payment_period_end
        
    @payment_end.setter
    def payment_end(self, date: datetime):
        self.__payment_period_end = date
    
    @property
    def sending_mode(self) -> int:
        return self.__sending_mode
    
    @property
    @database_working
    def is_using_trial(self, conn: MySQLConnection,
    cursor: MySQLCursor) -> bool:
        now_str = datetime.now().strftime(Client.__TIMESTAMP_FORMAT)
        cursor.execute(
            f'SELECT COUNT({ID_COL}) FROM {TRIAL_PERIOD_INFO_TABLE} '
            f'WHERE {ID_COL} = {self.__id} AND {TRIAL_PERIOD_END} > \'{now_str}\' AND '
            f'{CATEGORY} = {self.__sending_mode}'
        )
        return cursor.fetchall()[0][0]
        
    def set_trial_period(self, trial_end: datetime):
        conn, cursor = get_connection_and_cursor()
        str_date = trial_end.strftime(Client.__TIMESTAMP_FORMAT)
        cursor.execute(f'SELECT COUNT({ID_COL}) FROM {TRIAL_PERIOD_INFO_TABLE} '
            f'WHERE {ID_COL} = {self.__id} AND {CATEGORY} = {self.__sending_mode}')
        if not cursor.fetchall()[0][0]:
            cursor.execute(f'INSERT INTO {TRIAL_PERIOD_INFO_TABLE} '
                f'VALUES({self.__id}, "{self.get_str_payment_date()}", "{str_date}", 0, '
                f'NULL, 0, 0, 0, {self.__sending_mode})'
            )
        else:
            cursor.execute(
                f'UPDATE {TRIAL_PERIOD_INFO_TABLE}'
                f' SET {TRIAL_PERIOD_END} = "{str_date}" '
                f'WHERE {ID_COL} = {self.__id} AND {CATEGORY} = {self.__sending_mode}'
            )
        commit_and_close_connection_and_cursor(conn, cursor)
    
    @property
    @database_working
    def was_offered_sale(self, conn: MySQLConnection, cursor: MySQLCursor) -> bool:
        cursor.execute(f'SELECT {WAS_OFFERED_SALE} FROM {TRIAL_PERIOD_INFO_TABLE} '
                       f'WHERE {ID_COL} = {self.__id} AND {CATEGORY} = {self.__sending_mode}')
        result = cursor.fetchall()
        if result:
            return result[0][0]
        else:
            return False
            
    @was_offered_sale.setter
    def was_offered_sale(self, val):
        conn, cursor = get_connection_and_cursor()
        cursor.execute(f'UPDATE {TRIAL_PERIOD_INFO_TABLE} SET '
            f'{WAS_OFFERED_SALE} = {val} WHERE {ID_COL} = {self.__id} AND {CATEGORY} = {self.__sending_mode}')
        commit_and_close_connection_and_cursor(conn, cursor)
    
    def __eq__(self, c) -> bool:
        if not isinstance(c, type(self)):
            return False
        return self.__id == c.__id and self.__sending_mode == c.__sending_mode
    
    #client_entity can be id or object
    def did_activate_bot(client_entity, category: int = None) -> bool: #client_entity: Union[int, Client]
        conn, cursor = get_connection_and_cursor()
        id, category = Client.__get_id_and_category_from_client_entity(client_entity, category)
        cursor.execute(f'SELECT COUNT(*) FROM {ACTIVATED_BOT_TABLE} WHERE {ID_COL} = {id} AND {CATEGORY} = {category}')
        result = cursor.fetchall()[0][0]
        close_connection_and_cursor(conn, cursor)
        return result
    
    def set_as_activated_bot(client_entity, category: int = None):
        conn, cursor = get_connection_and_cursor()
        id, category = Client.__get_id_and_category_from_client_entity(client_entity, category)
        if not Client.did_activate_bot(client_entity, category):
            cursor.execute(f'INSERT INTO {ACTIVATED_BOT_TABLE} VALUES({id}, {category})')
            conn.commit()
        close_connection_and_cursor(conn, cursor)
            
    @staticmethod
    def __get_id_and_category_from_client_entity(client_entity, category: int) -> typing.Tuple[int, int]:
        if isinstance(client_entity, int):
            if category == None:
                raise ValueError('Can not get category of bot-sender')
            return client_entity, category
        else: #self
            return client_entity.__id, client_entity.__sending_mode
        
    @staticmethod
    @database_static_working
    def get_all_clients_from_db(conn: MySQLConnection, cursor: MySQLCursor) -> typing.List[Client]:
        cursor.execute(f'SELECT * FROM {CLIENTS_SUBSCRIBES}')
        return Client.__fetch_clients(cursor)

    @staticmethod
    def __fetch_clients(cursor: cursor.MySQLCursor) -> typing.List[Client]:
        clients = cursor.fetchall()
        return [Client(*values[:4]) for values in clients]

    @staticmethod
    @database_static_working
    def get_all_paid_clients(connection: MySQLConnection, cursor: MySQLCursor) -> typing.List[Client]:
        str_now = datetime.now().strftime(Client.__TIMESTAMP_FORMAT)
        cursor.execute(f'SELECT * FROM {CLIENTS_SUBSCRIBES} WHERE '
                        f"{PAYMENT_PERIOD_END} > '{str_now}'")
        return Client.__fetch_clients(cursor)

    @staticmethod
    def get_clients_by_filter(
        category:             Union[int,Iterable]      = None, 
        id:                   Union[int, Iterable]     = 0, 
        payment_date:         Union[datetime,Iterable] = None, 
        payment_period_end:   Union[datetime,Iterable] = None,   
        choose_between_dates: bool                     = False, 
        greater:              bool                     = None, # this is using only for periods (actually means greater of equal)
        is_using_trial:       bool                     = None, 
        warning_status:       Union[int, Iterable]     = -1,
        is_paused:            bool                     = None,
        payment_period:       int                      = None,
        is_paid:              bool                     = None
    ) -> typing.List[Client]:
        clients = []
        after = []
        category_filter = ''
        if id:
            after.append(Client.__generate_ejecting_request_row(ID_COL, id))
        if payment_date != None:
            if not (payment_period_end != None and choose_between_dates):
                after.append(Client.__generate_ejecting_request_row_for_date(LAST_PAYMENT, payment_date, 
                    choose_between_dates, greater))
        if payment_period_end != None:
            if not (payment_date != None and choose_between_dates):
                after.append(Client.__generate_ejecting_request_row_for_date(PAYMENT_PERIOD_END, payment_period_end, 
                    choose_between_dates, greater))
        if payment_date != None and payment_period_end != None and choose_between_dates:
            after.append(Client.__generate_ejecting_request_row_for_date(LAST_PAYMENT, payment_date, 
                    choose_between_dates, greater = True))
            after.append(Client.__generate_ejecting_request_row_for_date(PAYMENT_PERIOD_END, payment_period_end, 
                    choose_between_dates, greater = False))
        if warning_status != -1:
            after.append(Client.__generate_ejecting_request_row(PAYMENT_ENDING_WARNING_STATUS, warning_status))
        if category != None:
            category_filter = Client.__generate_ejecting_request_row(CATEGORY, category)
            after.append(category_filter)
        if payment_period != None:
            sign = '='
            if greater != None:
                sign = '>=' if greater else '<='
            after.append(f'DATEDIFF({PAYMENT_PERIOD_END}, {LAST_PAYMENT}) {sign} {payment_period}')
        if is_paid != None:
            after.append(Client.__generate_ejecting_request_row(IS_PAID, is_paid))
        after = ' AND '.join(after)
        if after:
            after = ' WHERE ' + after
        beginning = f'SELECT * FROM {CLIENTS_SUBSCRIBES}'
        tail = ''
        if is_using_trial != None:
            trial_filter = ' {0} EXISTS (SELECT {1} FROM {2} WHERE {3} > NOW() {4} AND ({1}, {5}) = (client.{1}, client.{5}))'.format(
                '' if is_using_trial else 'NOT', ID_COL, TRIAL_PERIOD_INFO_TABLE, TRIAL_PERIOD_END, 
                ('AND ' + category_filter) if category_filter else '', CATEGORY
            )
            tail += trial_filter
        if is_paused != None:
            belonging = '' if is_paused else 'NOT'
            pause_filter = f' {belonging} EXISTS (SELECT {CLIENT_ID} FROM {CLIENTS_PAUSES} WHERE ({CLIENT_ID}, {CATEGORY}) = '\
                f'(client.{ID_COL}, client.{CATEGORY}) AND {UNPAUSE_DATE} > NOW())'
            if not tail:
                tail = pause_filter
            else:
                tail += ' AND' + pause_filter
        if tail:
            beginning += ' as client'
            if after:
                tail = ' AND' + tail
            else:
                tail = ' WHERE' + tail
        request = beginning + after + tail
        conn, cursor = get_connection_and_cursor()
        cursor.execute(request)
        clients = Client.__fetch_clients(cursor)
        close_connection_and_cursor(conn, cursor)
        return clients 
        
    @staticmethod
    def __generate_ejecting_request_row(column_name: str, value: Union[Iterable, object]) -> str:
        requst_row = ''
        if isinstance(value, str):
            requst_row = f'{column_name} = "{value}"'
        elif not isinstance(value, Iterable):
            requst_row = f'{column_name} = {value}'
        else:
            requst_row = f'{column_name} IN ('
            for i, val in enumerate(value):
                if isinstance(val, str):
                    requst_row += f'"{val}"'
                else:
                    requst_row += f'{val}'
                if i != len(value)-1:
                    requst_row += ', '
            requst_row += ')'
        return requst_row

    @staticmethod
    def __generate_ejecting_request_row_for_date(
    column_name: str, date: Union[Iterable, datetime], choose_between_dates: bool, greater: bool) -> str:
        request_row = ''
        if isinstance(date, Iterable):
            if choose_between_dates:
                request_row = f"({column_name} BETWEEN \'{date[0].strftime(Client.__TIMESTAMP_FORMAT)}\' "\
                    f"AND '{date[1].strftime(Client.__TIMESTAMP_FORMAT)}')"
            else:
                date = [i.strftime(Client.__TIMESTAMP_FORMAT) for i in date]
                request_row = Client.__generate_ejecting_request_row(column_name, date)
                
        else:
            str_date = date.strftime(Client.__TIMESTAMP_FORMAT)
            if greater != None:
                sign = '>=' if greater else '<='
                request_row = f"{column_name} {sign} '{str_date}'"
            else:
                request_row = Client.__generate_ejecting_request_row(column_name, str_date)
        return request_row

    @staticmethod
    def has_client_id(id: int) -> bool:
        connecton,cursor = get_connection_and_cursor()
        cursor.execute(f'SELECT COUNT({ID_COL}) FROM {CLIENTS_SUBSCRIBES} WHERE {ID_COL} = {id}')
        result = cursor.fetchall()[0][0]
        close_connection_and_cursor(connecton, cursor)
        return bool(result)

    @staticmethod
    def get_client_by_id(id: int) -> typing.List[Client]:
        if not Client.has_client_id(id):
            return []
        conn, cursor = get_connection_and_cursor()
        clients = []
        cursor.execute(f'SELECT * FROM {CLIENTS_SUBSCRIBES} WHERE {ID_COL} = {id}')
        clients += Client.__fetch_clients(cursor)
        close_connection_and_cursor(conn, cursor)
        return clients

    @database_working
    def add_to_db(self, conn: MySQLConnection, cursor: MySQLCursor):
        str_last_payment_date = self.get_str_payment_date()
        str_payment_period_end = self.get_str_payment_date_end()
        cursor.execute(f'SELECT COUNT({ID_COL}) FROM {CLIENTS_SUBSCRIBES} WHERE {ID_COL} = {self.__id} '
            f'AND {CATEGORY} = {self.__sending_mode}')
        if cursor.fetchall()[0][0] != 0:
            cursor.execute(
                f'UPDATE {CLIENTS_SUBSCRIBES} SET '
                f'{LAST_PAYMENT} = "{str_last_payment_date}", {PAYMENT_PERIOD_END} = "{str_payment_period_end}" '
                f'WHERE {ID_COL} = {self.__id} AND {CATEGORY} = {self.__sending_mode}'
            )
        else:
            cursor.execute(
                f'INSERT INTO {CLIENTS_SUBSCRIBES} VALUES({self.__id}, '
                f'"{str_last_payment_date}", "{str_payment_period_end}", {self.__sending_mode}, 0, 0, 0)'
            )
        conn.commit()

    def increase_period(self, days: int):
        conn, cursor = get_connection_and_cursor()
        self.__payment_period_end += timedelta(days = days)
        cursor.execute(
            f'UPDATE {CLIENTS_SUBSCRIBES} SET {PAYMENT_PERIOD_END} = '
            f'DATE_ADD({PAYMENT_PERIOD_END}, INTERVAL {days} DAY)'
            f'WHERE {ID_COL} = {self.__id} AND {CATEGORY} = {self.__sending_mode}'
        )
        commit_and_close_connection_and_cursor(conn, cursor)

    def get_payment_days_left(self, before_date: datetime = None) -> Union[int, float]:
        if before_date == None:
            before_date = datetime.now()
        if before_date >= self.__payment_period_end:
            return 0
        delta = self.__payment_period_end - before_date
        if delta.days > 0:
            return delta.days
        else:
            return delta.seconds / (24*60*60)
        
    def change_id_of_client(old_id: int, new_id: int):
        conn, cursor = get_connection_and_cursor()
        cursor.execute(f'DELETE FROM {CLIENTS_SUBSCRIBES} WHERE {ID_COL} = {new_id}')
        cursor.execute(f'DELETE FROM {TRIAL_PERIOD_INFO_TABLE} WHERE {ID_COL} = {new_id}')
        cursor.execute(f'DELETE FROM {CLIENTS_PAUSES} WHERE {CLIENT_ID} = {new_id}')
        cursor.execute(f'UPDATE {CLIENTS_SUBSCRIBES} SET {ID_COL} = {new_id} WHERE {ID_COL} = {old_id} ')
        cursor.execute(f'UPDATE {TRIAL_PERIOD_INFO_TABLE} SET {ID_COL} = {new_id} WHERE {ID_COL} = {old_id} ')
        cursor.execute(f'UPDATE {CLIENTS_PAUSES} SET {CLIENT_ID} = {new_id} WHERE {CLIENT_ID} = {old_id} ')
        commit_and_close_connection_and_cursor(conn, cursor)

    def is_awared_about(self, what: str) -> bool:
        '''Searches for table "awared_clients" for the line with "self.id" and "what"'''
        conn, cursor = get_connection_and_cursor()
        cursor.execute(f'SELECT * FROM {AWARED_CLIENTS} WHERE {ID_COL} = {self.__id} AND {WHAT_AWARED_ABOUT} = "{what}"')
        res =  cursor.fetchall()
        close_connection_and_cursor(conn, cursor)
        if not res:
            return False
        return True
    
    def set_as_awared_about(self, what: str):
        '''Adds values: (self.id, what) to  "awared_clients" table'''
        conn, cursor = get_connection_and_cursor()
        cursor.execute(f'SELECT * FROM {AWARED_CLIENTS} WHERE {ID_COL} = {self.__id} AND {WHAT_AWARED_ABOUT} = "{what}"')
        res =  cursor.fetchall()
        if not res:
            cursor.execute(f'INSERT INTO {AWARED_CLIENTS} VALUES ({self.__id}, "{what}")')
        commit_and_close_connection_and_cursor(conn, cursor)