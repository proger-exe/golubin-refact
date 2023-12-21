from __future__ import annotations
from typing import Union
from datetime import date
import typing
from mysql.connector.cursor import MySQLCursor
from .config import *
from database import *

class Vote:

    def __init__(self, date: date, user_id: int, category: int, message_id: int, vote_type: int):
        self.__id = None
        self.__date = date
        self.__user_id = user_id
        self.__category = category
        self.__message_id = message_id
        self.__vote_type = vote_type

    def save(self):
        connection, cursor = get_connection_and_cursor()
        if self.__id == None:
            cursor.execute(f'INSERT INTO {VOTES_TABLE} VALUES (DEFAULT, "{self.__date}", {self.__user_id}, '
                f'{self.__category}, {self.__message_id}, {self.__vote_type})')
            connection.commit()
            self.__setID(cursor)
        else:
            cursor.execute(
                f'UPDATE {VOTES_TABLE} SET {DATE} = "{self.__date}", {USER_ID} = {self.__user_id}, '
                f'{CATEGORY} = {self.__category}, {MESSAGE_ID} = {self.__message_id}, {VOTE_TYPE} = {self.__vote_type}'
                f' WHERE {VOTE_ID} = {self.__id}'
            )
            connection.commit()
        close_connection_and_cursor(connection, cursor)

    def __setID(self, cursor: MySQLCursor) -> int:
        cursor.execute(
            f'SELECT {VOTE_ID} FROM {VOTES_TABLE} WHERE {USER_ID} = {self.__user_id} AND '
            f'{DATE} = "{self.__date}" AND {CATEGORY} = {self.__category} AND {MESSAGE_ID} = {self.__message_id} AND '
            F'{VOTE_TYPE} = {self.__vote_type}'
        )
        result = cursor.fetchall()
        if result:
            self.__id = result[0][0]


    @property
    def date(self) -> date:
        return self.__date

    @date.setter
    def date(self, value: date):
        self.__date = value

    @property
    def id(self) -> typing.Union[int, None]:
        return self.__id

    @property
    def user_id(self) -> int:
        return self.__user_id

    @user_id.setter
    def user_id(self, id: int):
        self.__user_id = id

    @property
    def category(self) -> int:
        return self.__category

    @category.setter
    def category(self, value: int):
        self.__category = value

    @property
    def message_id(self) -> int:
        return self.__message_id

    @message_id.setter
    def message_id(self, value: int):
        self.__message_id = value

    @property
    def vote_type(self) -> int:
        return self.__vote_type

    @vote_type.setter
    def vote_type(self, value: int):
        self.__vote_type = value

    def __eq__(self, __o: Vote) -> bool:
        if self.__id != None and self.__id == __o.__id:
            return True
        return self.__user_id == __o.__user_id and self.__date == __o.__date and self.__category == __o.__category and \
            self.__message_id == __o.__message_id and self.__vote_type == __o.__vote_type

    @staticmethod
    def getAll() -> typing.List[Vote]:
        connection, cursor = get_connection_and_cursor()
        cursor.execute(f'SELECT * FROM {VOTES_TABLE}')
        votes = []
        for row in cursor.fetchall():
            v = Vote(*row[1:])
            v.__id = row[0]
            votes.append(v)
        close_connection_and_cursor(connection, cursor)
        return votes

    @staticmethod
    def findByFilter(
        date: date = None,
        period: typing.Tuple[date, date] = None,
        user_id: int = None,
        category: int = None,
        message_id : int = None,
        vote_type: int = None
    ) -> typing.List[Vote]:
        request = f'SELECT * FROM {VOTES_TABLE}'
        filter = []
        if date != None:
            filter.append(f'{DATE} = "{date}"')
        if period:
            filter.append(f'{DATE} BETWEEN "{period[0]}" AND "{period[1]}"')
        if user_id != None:
            filter.append(f'{USER_ID} = {user_id}')
        if category != None:
            filter.append(f'{CATEGORY} = {category}')
        if message_id != None:
            filter.append(f'{MESSAGE_ID} = {message_id}')
        if vote_type != None:
            filter.append(f'{VOTE_TYPE} = {vote_type}')
        if filter:
            filter = ' WHERE ' + ' AND '.join(filter)
            request += filter
        connection, cursor = get_connection_and_cursor()
        cursor.execute(request)
        result = cursor.fetchall()
        close_connection_and_cursor(connection, cursor)
        votes = []
        for row in result:
            v = Vote(*row[1:])
            v.__id = row[0]
            votes.append(v)
        return votes

    @staticmethod
    def getByID(vote_id: int) -> Union[Vote, None]:
        connection, cursor = get_connection_and_cursor()
        cursor.execute(f'SELECT * FROM {VOTES_TABLE} WHERE {VOTE_ID} = {vote_id}')
        result = cursor.fetchall()
        close_connection_and_cursor(connection, cursor)
        if not result:
            return None
        vote = Vote(*result[0][1:])
        vote.__id = result[0][0]
        return vote
    
    @staticmethod
    def transferVotes(from_id: int, to_id: int):
        conn, cursor = get_connection_and_cursor()
        cursor.execute(f'UPDATE {VOTES_TABLE} SET {USER_ID} = {to_id} WHERE {USER_ID} = {from_id}')
        commit_and_close_connection_and_cursor(conn, cursor)