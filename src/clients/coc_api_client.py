import urllib.parse
from typing import Optional

from models.clash_of_clans import ClanMember, War, CWLGroup, CapitalRaidSeason, Player
from .base_api_client import BaseApiClient
from utils import log, LogLevel


COC_API_BASE_URL = 'https://api.clashofclans.com/v1'


class ClashOfClansApiClient(BaseApiClient):
    def __init__(self, api_token: str) -> None:
        super().__init__(COC_API_BASE_URL, {'Authorization': f'Bearer {api_token}'})

    async def get_clan_members(self, clan_tag: str) -> list[ClanMember]:
        response = await self.GET(f'clans/{urllib.parse.quote(clan_tag)}/members')
        if response.status_code == 200:
            return [ClanMember(raw) for raw in response.json()['items']]
        return []

    async def get_current_regular_war(self, clan_tag: str) -> Optional[War]:
        response = await self.GET(f'clans/{urllib.parse.quote(clan_tag)}/currentwar')
        if response.status_code == 200:
            return War(response.json())
        return None

    async def get_current_leaguegroup(self, clan_tag: str) -> Optional[CWLGroup]:
        response = await self.GET(f'clans/{urllib.parse.quote(clan_tag)}/currentwar/leaguegroup')
        if response.status_code == 200:
            return CWLGroup(response.json())
        return None

    async def get_cwl_war(self, war_tag: str) -> Optional[War]:
        response = await self.GET(f'clanwarleagues/wars/{urllib.parse.quote(war_tag)}')
        if response.status_code == 200:
            return War(response.json(), is_cwl = True, tag = war_tag)
        return None

    async def get_capital_raid_seasons(self, clan_tag: str) -> list[CapitalRaidSeason]:
        response = await self.GET(f'clans/{urllib.parse.quote(clan_tag)}/capitalraidseasons')
        if response.status_code == 200:
            return [CapitalRaidSeason(raw) for raw in response.json()['items']]
        return []

    async def get_current_capital_raid_season(self, clan_tag: str) -> Optional[CapitalRaidSeason]:
        seasons = await self.get_capital_raid_seasons(clan_tag)
        if len(seasons) > 0 and seasons[0].state == 'ongoing':
            return seasons[0]
        return None

    async def get_current_war(self, clan_tag: str) -> Optional[War]:
        war = await self.get_current_regular_war(clan_tag)
        if war is not None and war.state != 'notInWar':
            log(f'Regular war found', LogLevel.INFO)
            return war
        return await self.get_current_league_war(clan_tag)

    async def get_current_league_war(self, clan_tag: str) -> Optional[War]:
        cwl_group = await self.get_current_leaguegroup(clan_tag)
        if cwl_group is None or len(cwl_group.rounds) == 0:
            log(f'No league group found', LogLevel.INFO)
            return None

        war = None
        league_day = len(cwl_group.rounds)
        for war_tag in cwl_group.rounds[-1].war_tags:
            cwl_war = await self.get_cwl_war(war_tag)
            if cwl_war is not None and cwl_war.clan.tag == clan_tag:
                war = cwl_war
                break

        if war is not None and war.state in 'preparation' and len(cwl_group.rounds) > 1:
            league_day -= 1
            for war_tag in cwl_group.rounds[-2].war_tags:
                cwl_war = await self.get_cwl_war(war_tag)
                if cwl_war is not None and cwl_war.clan.tag == clan_tag:
                    war = cwl_war
                    break

        log(f'Found war for league day {league_day}', LogLevel.INFO)
        if war is not None:
            war.league_day = league_day
        return war

    async def get_player(self, player_tag: str) -> Optional[Player]:
        response = await self.GET(f'players/{urllib.parse.quote(player_tag)}')
        if response.status_code == 200:
            return Player(response.json())
        return None
