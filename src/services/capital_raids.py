import asyncio
from time import time
from datetime import datetime
from typing import Optional
from clients import ClashOfClansApiClient, DiscordApiClient
from models.clash_of_clans import CapitalRaidSeason
from utils import log, LogLevel


class CapitalRaidsService:
    def __init__(
        self,
        clan_tag: str,
        coc_api_client: ClashOfClansApiClient,
        discord_api_client: DiscordApiClient,
        on_current_raid_change = None
    ) -> None:
        self.clan_tag = clan_tag
        self.coc_api_client = coc_api_client
        self.discord_api_client = discord_api_client

        self.current_capital_raid_season: Optional[CapitalRaidSeason] = None
        self.raid_last_fetched_at: Optional[float] = None
        self.raid_fetch_next_task: Optional[asyncio.TimerHandle] = None
        self.on_current_raid_change = on_current_raid_change

        now = datetime.now()
        if now.weekday() >= 4 or now.weekday() == 0 and now.hour <= 12:
            self.create_next_raid_season_fetch_task()
        else:
            days_delta, seconds_delta = 4 - now.weekday(), (12 - now.hour) * 3600 - now.minute * 60 - now.second
            duration = days_delta * 86400 + seconds_delta
            event_loop = asyncio.get_event_loop()
            self.raid_fetch_next_task = event_loop.call_later(duration, self.create_next_raid_season_fetch_task)

    async def get_current_capital_raid_season(self):
        if self.raid_last_fetched_at is not None and time() - self.raid_last_fetched_at < 3:
            return self.current_capital_raid_season
        current_season = await self.coc_api_client.get_current_capital_raid_season(self.clan_tag)
        if current_season is not None:
            if self.on_current_raid_change is not None and self.current_capital_raid_season != current_season:
                await self.on_current_raid_change(current_season)
            self.current_capital_raid_season = current_season
            self.raid_last_fetched_at = time()
            log('Succesfully fetched capital raid', LogLevel.INFO)
            event_loop = asyncio.get_event_loop()
            if self.raid_fetch_next_task is not None:
                self.raid_fetch_next_task.cancel()
            self.raid_fetch_next_task = event_loop.call_later(10800, self.create_next_raid_season_fetch_task)  # 3 hours
            return current_season

    def create_next_raid_season_fetch_task(self):
        asyncio.create_task(self.get_current_capital_raid_season())
