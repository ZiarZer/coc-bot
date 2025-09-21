from abc import abstractmethod
from .db_connection import DbConnection


class BaseRepository:
    def __init__(self):
        self.db_connection = DbConnection()
        self.init_table()

    @abstractmethod
    def init_table(self) -> None:
        return
