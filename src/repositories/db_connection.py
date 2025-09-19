import sqlite3 as sql
from typing import Any, Optional


class DbConnection:
    instance = None

    def __new__(cls):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
            cls.db_connection = sql.connect('.coc-bot.db')
        return cls.instance

    def quick_lookup(self, query: str, params) -> Optional[Any]:
        record = self.first_record_lookup(query, params)
        if record is None or len(record) == 0:
            return None
        return record[0]

    def first_record_lookup(self, query: str, params) -> Optional[tuple]:
        cursor = self.db_connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

    def record_lookup(self, query: str, params = None) -> list[tuple]:
        cursor = self.db_connection.cursor()
        if params is None:
            cursor.execute(query)
        else:
            cursor.execute(query, params)
        return cursor.fetchall()

    def query(self, query: str, params = None) -> None:
        cursor = self.db_connection.cursor()
        if params is None:
            cursor.execute(query)
        else:
            cursor.execute(query, params)
        self.db_connection.commit()
