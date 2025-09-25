from .base_repository import BaseRepository


class TroopGiversRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    def init_table(self):
        self.db_connection.query('''
            CREATE TABLE IF NOT EXISTS `troop_givers` (
                `discord_user_id` varchar(20) NOT NULL,
                `can_ping` integer NOT NULL DEFAULT 0,
                PRIMARY KEY (`discord_user_id`)
            );
        ''')

    def insert_troop_giver(self, discord_user_id: str, can_ping: bool = False) -> None:
        self.db_connection.query(
            '''INSERT INTO `troop_givers` (`discord_user_id`, `can_ping`) VALUES (?, ?)
            ON CONFLICT DO UPDATE SET `can_ping` = EXCLUDED.`can_ping`''',
            (discord_user_id, can_ping)
        )

    def get_pingable_troop_givers(self) -> list[tuple[str, str]]:
        return self.db_connection.record_lookup(
            '''SELECT dcl.`discord_user_id`, dcl.`coc_player_tag`
            FROM `discord_coc_links` dcl INNER JOIN `troop_givers` tg
            ON dcl.`discord_user_id` = tg.`discord_user_id`
            WHERE `can_ping` = 1'''
        )
