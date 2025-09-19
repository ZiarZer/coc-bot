from models.clash_of_clans import War
from clients import ClashOfClansApiClient, DiscordApiClient


CLAN_MAIN_CHANNEL_ID = '1327513254473236481'
CLAN_MEMBERS_WARNING_THRESHOLD = 49


class ClanWarsService:
    def __init__(self, clan_tag: str, coc_api_client: ClashOfClansApiClient, discord_api_client: DiscordApiClient):
        self.clan_tag = clan_tag
        self.coc_api_client = coc_api_client
        self.discord_api_client = discord_api_client
