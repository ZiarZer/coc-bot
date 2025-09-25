from typing import Optional
import asyncio
from time import time
from models.clash_of_clans import War, CWLGroup, WarScore
from clients import ClashOfClansApiClient, DiscordApiClient
from utils import log, LogLevel, to_timestamp


CLAN_MAIN_CHANNEL_ID = '1327513254473236481'
CLAN_MEMBERS_WARNING_THRESHOLD = 49


class ClanWarsService:
    def __init__(
        self,
        clan_tag: str,
        coc_api_client: ClashOfClansApiClient,
        discord_api_client: DiscordApiClient,
        on_current_war_change = None
    ) -> None:
        self.clan_tag = clan_tag
        self.coc_api_client = coc_api_client
        self.discord_api_client = discord_api_client

        self.current_war: Optional[War] = None
        self.war_last_fetched_at: Optional[float] = None
        self.war_fetch_next_task: Optional[asyncio.TimerHandle] = None
        self.on_current_war_change = on_current_war_change

        # CWL
        self.current_cwl_group: Optional[CWLGroup] = None
        self.cwl_last_fetched_at: Optional[float] = None
        self.league_end_time: Optional[float] = None
        self.cwl_scores: dict[str, WarScore] = {}  # Keys are in the format '#WARTAG#CLANTAG'
        self.ended_cwl_wars: dict[str, War] = {}

    async def get_current_war(self) -> Optional[War]:
        if self.war_last_fetched_at is not None and time() - self.war_last_fetched_at < 3:
            return self.current_war
        current_war = await self.coc_api_client.get_current_war(self.clan_tag)
        if current_war is not None:
            if self.on_current_war_change is not None and self.current_war != current_war:
                await self.on_current_war_change(current_war)
            self.current_war = current_war
            self.war_last_fetched_at = time()
            log('Succesfully fetched war', LogLevel.INFO)
            if self.war_fetch_next_task is not None:
                self.war_fetch_next_task.cancel()
            duration = 3600
            if current_war.state == 'preparation':
                duration = to_timestamp(current_war.war_start_time) - int(time()) + 300
            elif current_war.state == 'inWar' and to_timestamp(current_war.end_time) - int(time()) < 3600:
                duration = to_timestamp(current_war.end_time) - int(time()) + 300
            event_loop = asyncio.get_event_loop()
            self.war_fetch_next_task = event_loop.call_later(duration, self.create_next_war_fetch_task)
        return current_war

    async def get_current_cwl_group(self):
        if self.cwl_last_fetched_at is not None and time() - self.cwl_last_fetched_at < 3:
            return self.current_cwl_group
        league_group = await self.coc_api_client.get_current_leaguegroup(self.clan_tag)
        if league_group is not None:
            self.current_cwl_group = league_group
            self.cwl_last_fetched_at = time()
            log('Succesfully fetched cwl group', LogLevel.INFO)
        else:
            return None

        clan_scores = {c.tag: WarScore() for c in league_group.clans}
        for ir in range(len(league_group.rounds)):
            round = league_group.rounds[ir]
            for war_tag in round.war_tags:
                war = self.ended_cwl_wars.get(war_tag)
                if war is None:
                    war = await self.coc_api_client.get_cwl_war(war_tag)
                    if war is not None:
                        war.league_day = ir + 1
                        if war.state == 'warEnded':
                            self.ended_cwl_wars[war_tag] = war
                        if war.state == 'inWar' and self.clan_tag in (war.clan.tag, war.opponent.tag):
                            self.current_war = war
                            self.war_last_fetched_at = time()

                if war is not None:
                    clan_1_tag, clan_2_tag = war.clan.tag, war.opponent.tag
                    clan_scores[clan_1_tag].add_to_score(war.clan)
                    clan_scores[clan_2_tag].add_to_score(war.opponent)
                    star_diff = war.clan.stars - war.opponent.stars
                    percent_diff = war.clan.destruction_percentage - war.opponent.destruction_percentage
                    if war.state == 'warEnded':
                        if star_diff > 0 or star_diff == 0 and percent_diff > 0:
                            clan_scores[clan_1_tag].stars += 10
                        elif star_diff < 0 or star_diff == 0 and percent_diff < 0:
                            clan_scores[clan_2_tag].stars += 10
        league_group.clan_scores = clan_scores
        return league_group

    def create_next_war_fetch_task(self):
        asyncio.create_task(self.get_current_war())
