from time import time
from typing import Optional, Callable

from models.clash_of_clans import ClanMember
from clients import ClashOfClansApiClient, DiscordApiClient
from utils import log, LogLevel


CLAN_MAIN_CHANNEL_ID = '1327513254473236481'
CLAN_MEMBERS_WARNING_THRESHOLD = 49


class ClanMembersService:
    def __init__(self, clan_tag: str, coc_api_client: ClashOfClansApiClient, discord_api_client: DiscordApiClient):
        self.clan_tag = clan_tag
        self.coc_api_client = coc_api_client
        self.discord_api_client = discord_api_client
        self.clan_members: list[ClanMember] = []
        self.members_last_fetched_at: Optional[float] = None

    async def get_clan_members(
        self,
        custom_ping_filter: Optional[Callable[[ClanMember], bool]] = None,
        force_fetch = False
    ) -> list[ClanMember]:
        must_refresh = self.members_last_fetched_at is None or time() - self.members_last_fetched_at > 28800
        if force_fetch or len(self.clan_members) == 0 or must_refresh:  # 8 hours
            clan_members = await self.coc_api_client.get_clan_members(self.clan_tag)
            members_count = len(clan_members)
            if members_count > 0:
                if 0 < len(self.clan_members) < members_count and members_count >= CLAN_MEMBERS_WARNING_THRESHOLD:
                    warning_message = f'Le Clan est {"bientôt" if members_count < 50 else ""} rempli'
                    await self.discord_api_client.send_message(
                        CLAN_MAIN_CHANNEL_ID,
                        f'**:warning: {warning_message} ({members_count}/50)**'
                    )
                self.clan_members = clan_members
                self.members_last_fetched_at = time()
                log('Succesfully fetched clan members', LogLevel.INFO)
        if custom_ping_filter is None:
            return self.clan_members
        return list(filter(custom_ping_filter, self.clan_members))
