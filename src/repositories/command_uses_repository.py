from typing import Optional
from .base_repository import BaseRepository


class CommandUsesRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    def init_table(self):
        self.db_connection.query('''
            CREATE TABLE IF NOT EXISTS `command_uses` (
                `id` integer NOT NULL,
                `discord_user_id` varchar(20) NOT NULL,
                `command` varchar(20) NOT NULL,
                `used_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (`id`)
            );
        ''')

    def insert_command_use(self, discord_user_id: str, command: str) -> None:
        self.db_connection.query(
            'INSERT INTO `command_uses` (`discord_user_id`, `command`) VALUES (?, ?)',
            (discord_user_id, command)
        )

    def get_last_command_use_time(self, discord_user_id: str) -> Optional[str]:
        return self.db_connection.quick_lookup(
            'SELECT `used_at` FROM `command_uses` WHERE `discord_user_id` = ?',
            (discord_user_id,)
        )
