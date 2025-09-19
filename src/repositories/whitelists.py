from typing import Optional, Literal
from .db_connection import DbConnection


class WhitelistsRepository:
    def __init__(self):
        self.db_connection = DbConnection()

    def init_table(self):
        self.db_connection.query('''
            CREATE TABLE IF NOT EXISTS `whitelists` (
                `object_id` varchar(20) NOT NULL,
                `object_type` varchar(7) NOT NULL,
                `is_whitelisted` integer NOT NULL DEFAULT 1,
                PRIMARY KEY (`object_id`)
            );
        ''')

    def insert_whitelist(self, object_id: str, object_type: Literal['CHANNEL', 'GUILD']) -> None:
        self.db_connection.query(
            '''INSERT INTO `whitelists` (`object_id`, `object_type`, `is_whitelisted`) VALUES (?, ?, 1)
            ON CONFLICT DO UPDATE SET `is_whitelisted` = 1''',
            (object_id, object_type)
        )

    def is_whitelisted(self, channel_id: str, guild_id: Optional[str] = None) -> bool:
        query = "SELECT `is_whitelisted` FROM `whitelists` WHERE `object_id` = ? AND `object_type` = 'CHANNEL'"
        params: tuple = (channel_id,)
        if guild_id is not None:
            params += (guild_id,)
            query += " OR `object_id` = ? AND `object_type` = 'GUILD'"
        return self.db_connection.quick_lookup(query, params) == 1
