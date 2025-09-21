from typing import Optional
from .base_repository import BaseRepository


class DiscordCocLinksRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    def init_table(self):
        self.db_connection.query('''
            CREATE TABLE IF NOT EXISTS `discord_coc_links` (
                `discord_user_id` varchar(20) NOT NULL,
                `coc_player_tag` varchar(20) NOT NULL,
                PRIMARY KEY (`discord_user_id`, `coc_player_tag`)
            );
        ''')

    def insert_discord_account_player_tag(self, discord_user_id: str, coc_player_tag: str) -> None:
        self.db_connection.query(
            '''INSERT INTO `discord_coc_links` (`discord_user_id`, `coc_player_tag`) VALUES (?, ?)
            ON CONFLICT DO NOTHING''',
            (discord_user_id, coc_player_tag)
        )

    def get_discord_id_from_player_tag(self, coc_player_tag: str) -> Optional[str]:
        return self.db_connection.quick_lookup(
            'SELECT `discord_user_id` FROM `discord_coc_links` WHERE `coc_player_tag` = ?',
            (coc_player_tag, )
        )

    def get_player_tags_from_discord_id(self, discord_id: str) -> list[str]:
        return [
            record[0] for record in self.db_connection.record_lookup(
                'SELECT `coc_player_tag` FROM `discord_coc_links` WHERE `discord_user_id` = ?',
                (discord_id, )
            )
        ]
