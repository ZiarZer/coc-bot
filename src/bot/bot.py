import asyncio
import os
import traceback
from time import time
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

from models.clash_of_clans import ClanRole, WarScore, War, WarClan, WarParticipant, CapitalRaidSeason, CWLGroup
from models.discord import Message, ChannelType, User, PresenceActivity
from clients import DiscordGatewayClient, ClashOfClansApiClient, DiscordApiClient
from repositories import CommandUsesRepository, DiscordCocLinksRepository, TroopGiversRepository, WhitelistsRepository
from services import ClanMembersService
from utils import to_timestamp, parse_year_month, log, LogLevel

from .custom_pings import parse_custom_ping
from .commands import Command, requires_role


APP_NAME = 'coc-bot'
APP_VERSION = '0.3.0'

CLAN_BANNER_EMOJI = '<:The3200Club:1393849123341340814>'

TODO = [
    'multi-clans',
    'migration',
    'embeds',
    '>troops th16 / >tdc hdv16 / >tdc 16'

    'erase cached info when not needed anymore (no longer save cwl wars when cwl ends for example)',
    'add clan games activity when event is active',
    'custom timer (not discord)',
    'translations',

    'command to init clan by server (to remove hardcoded vars)'

    '@actifs / @actifs7 / @actifs30',
    '@gdc / @gdc-attack: ping members that have an available attack in war'
]


CLAN_APPLICATION_ID = '1395131415825354884'
CWL_APPLICATION_ID = '1394456649170812939'
CLAN_WAR_APPLICATION_ID = '1391897870713487451'
CLAN_GAMES_APPLICATION_ID = '1394592457634611280'
WEEKEND_RAID_APPLICATION_ID = '1394592567105949777'

load_dotenv()
BACKOFFICE_CHANNEL_ID = os.environ.get('BACKOFFICE_CHANNEL_ID')


class Bot:
    def __init__(self, clan_tag: str, discord_auth_token: str, coc_api_token: str, prefix = '>') -> None:
        self.discord_coc_links_repository = DiscordCocLinksRepository()
        self.command_uses_repository = CommandUsesRepository()
        self.troop_givers_repository = TroopGiversRepository()
        self.whitelists_repository = WhitelistsRepository()
        self.discord_coc_links_repository.init_table()
        self.command_uses_repository.init_table()
        self.troop_givers_repository.init_table()
        self.whitelists_repository.init_table()

        self.discord_api_client = DiscordApiClient(discord_auth_token)
        self.discord_gateway_client = DiscordGatewayClient(
            APP_NAME,
            discord_auth_token,
            on_ready=self.on_ready,
            on_message=self.on_message,
            on_error=self.on_error
        )
        self.coc_api_client = ClashOfClansApiClient(coc_api_token)
        self.clan_tag = clan_tag
        self.clan_invite_link = f'https://link.clashofclans.com/fr?action=OpenClanProfile&tag={clan_tag}'
        self.prefix = prefix
        self.can_use_custom_emojis = False
        self.activities: dict[str, Optional[PresenceActivity]] = {}

        # Wars
        self.current_war: Optional[War] = None
        self.war_last_fetched_at: Optional[float] = None
        self.war_fetch_next_task: Optional[asyncio.TimerHandle] = None

        # CWL
        self.current_cwl_group: Optional[CWLGroup] = None
        self.cwl_last_fetched_at: Optional[float] = None
        self.league_end_time: Optional[float] = None
        self.cwl_scores: dict[str, WarScore] = {}  # Keys are in the format '#WARTAG#CLANTAG'
        self.ended_cwl_wars: dict[str, War] = {}

        # Capital raids
        self.current_capital_raid_season: Optional[CapitalRaidSeason] = None
        self.raid_last_fetched_at: Optional[float] = None
        self.raid_fetch_next_task: Optional[asyncio.TimerHandle] = None

        # Clan members
        self.clan_members_service = ClanMembersService(self.clan_tag, self.coc_api_client, self.discord_api_client)

        commands = [
            Command('gdc', self.war, aliases=['war']),
            Command('ldc', self.cwl, aliases=['cwl', 'ligue', 'league']),
            Command('spyldc', self.spy_cwl, aliases=['spycwl', 'spyleague']),
            Command('annonce', self.announce, aliases=['announce'], hidden=True),
            Command('troops', self.troops, aliases=['troupes', 'tdc']),
            Command('troopgiver', self.add_troop_giver, aliases=['addtroopgiver']),
            Command('removetroopgiver', self.remove_troop_giver),
            Command('attacks', self.attacks, aliases=['attaques', 'att']),
            Command('invite', self.invite),
            Command('whitelistchannel', self.whitelist_channel, bypass_whitelist=True),
            Command('whitelistguild', self.whitelist_guild, bypass_whitelist=True),
            Command('help', self.help),
            Command('about', self.about),
            Command('todo', self.todo, hidden=True),
        ]
        self.help_message = 'commands:\n' + '\n'.join([c.help_entry(self.prefix) for c in commands if not c.hidden])
        self.commands: dict[str, Command] = {}
        for command in commands:
            self.commands[command.name] = command
            for alias in command.aliases:
                self.commands[alias] = command

    async def run(self) -> None:
        self.started_at = time()
        await self.discord_gateway_client.run()

    async def get_current_war(self) -> Optional[War]:
        if self.war_last_fetched_at is not None and time() - self.war_last_fetched_at < 3:
            return self.current_war
        current_war = await self.coc_api_client.get_current_war(self.clan_tag)
        if current_war is not None:
            self.current_war = current_war
            self.war_last_fetched_at = time()
            log('Succesfully fetched war', LogLevel.INFO)
            await self.update_presence_with_current_war()
            if self.war_fetch_next_task is not None:
                self.war_fetch_next_task.cancel()
            duration = 3600
            if current_war.state == 'preparation':
                duration = to_timestamp(current_war.war_start_time) - int(time()) + 300
            elif current_war.state == 'inWar' and to_timestamp(current_war.end_time) - int(time()) < 3600:
                duration = to_timestamp(current_war.end_time) - int(time()) + 300
            event_loop = asyncio.get_event_loop()
            self.war_fetch_next_task = event_loop.call_later(duration, self.run_current_war_fetch_task)
            return current_war
        return None

    async def get_current_capital_raid_season(self):
        if self.raid_last_fetched_at is not None and time() - self.raid_last_fetched_at < 3:
            return self.current_capital_raid_season
        current_season = await self.coc_api_client.get_current_capital_raid_season(self.clan_tag)
        if current_season is not None:
            self.current_capital_raid_season = current_season
            self.raid_last_fetched_at = time()
            log('Succesfully fetched capital raid', LogLevel.INFO)
            await self.update_presence_with_current_capital_raid_season()
            event_loop = asyncio.get_event_loop()
            if self.raid_fetch_next_task is not None:
                self.raid_fetch_next_task.cancel()
            self.raid_fetch_next_task = event_loop.call_later(10800, self.run_raid_capital_season_fetch_task)  # 3 hours
            return current_season

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

    async def update_presence(self) -> None:
        ACTIVITIES_ORDER = ('WAR', 'CWL', 'RAID', 'CLAN')
        await self.discord_gateway_client.update_presence([])
        await self.discord_gateway_client.update_presence([
            activity for activity in map(
                lambda a: a[1],
                sorted(self.activities.items(), key = lambda a: ACTIVITIES_ORDER.index(a[0]))
            ) if activity is not None
        ])

    async def update_presence_with_current_war(self) -> None:
        war = self.current_war
        if war is None:
            return
        self.activities['WAR'] = war.build_presence_activity()
        if war.is_cwl:
            self.activities['CWL'] = war.build_cwl_presence_activity()
        await self.update_presence()

    async def update_presence_with_current_capital_raid_season(self) -> None:
        if self.current_capital_raid_season is None:
            return
        if self.current_capital_raid_season.state == 'ongoing':
            self.activities['RAID'] = self.current_capital_raid_season.build_presence_activity()
        await self.update_presence()

    async def invite(self, message: Message) -> None:
        title_emojis = CLAN_BANNER_EMOJI if self.can_use_custom_emojis else ':blue_heart::white_heart::blue_heart:'
        title = f'{title_emojis} **The 3200 Club** {title_emojis}'
        await self.discord_api_client.send_message(
            message.channel_id,
            f'## Rejoins le Clan : `{self.clan_tag}`\n{title}\n{self.clan_invite_link}'
        )

    async def whitelist_channel(self, message: Message) -> None:
        self.whitelists_repository.insert_whitelist(message.channel_id, 'CHANNEL')
        await self.discord_api_client.send_message(message.channel_id, ':white_check_mark: Channel whitelisté')

    async def whitelist_guild(self, message: Message) -> None:
        if message.guild_id is None:
            log(f'Aborted whitelist_guild command, message has no guild ID.', LogLevel.INFO)
            return
        self.whitelists_repository.insert_whitelist(message.guild_id, 'GUILD')
        await self.discord_api_client.send_message(message.channel_id, ':white_check_mark: Serveur whitelisté')

    @requires_role(ClanRole.MEMBER)
    async def troops(self, message: Message):
        snowflakes = self.troop_givers_repository.get_pingable_troop_givers()
        if len(snowflakes) == 0:
            await self.discord_api_client.send_message(
                message.channel_id,
                f'There are currently no troop givers. Use the `{self.prefix}troopgiver` command to add one.'
            )
            return
        pings = '** ; **'.join([f'<@{snowflake}>' for snowflake in snowflakes])
        response_content = f'{message.author} a besoin de tdc\n||{pings}||'
        if message.content.startswith(f'{self.prefix}tdc'):
            response_content = f'{message.author} a lancé une ALERTE TDC !!!!!!!!!!!\n||{pings}||'
        await self.discord_api_client.send_message(message.channel_id, response_content)

    @requires_role(ClanRole.COLEADER)
    async def add_troop_giver(self, message: Message):
        params = message.content.split()[1:]
        # TODO: handle <@User-Id> format and <Username> format
        if len(params) == 0:
            await self.discord_api_client.send_message(
                message.channel_id,
                f'Usage: `{self.prefix}troopgiver <Discord-User-ID>`'
            )
            return
        added_troop_givers = []
        for param in params:
            if len(self.discord_coc_links_repository.get_player_tags_from_discord_id(param)) > 0:
                self.troop_givers_repository.insert_troop_giver(param, True)
                added_troop_givers.append(param)
        if len(added_troop_givers) == 0:
            message_content = "Aucun des IDs donnés n'est lié au compte COC d'un membre du clan"
        else:
            message_content = 'Donneurs de troupes ajoutés : ' + ', '.join(added_troop_givers)
        await self.discord_api_client.send_message(message.channel_id, message_content)

    # TODO: code duped from add_troop_giver with few changes, should refactor
    @requires_role(ClanRole.COLEADER)
    async def remove_troop_giver(self, message: Message):
        params = message.content.split()[1:]
        if len(params) == 0:
            await self.discord_api_client.send_message(
                message.channel_id,
                f'Usage: `{self.prefix}removetroopgiver <Discord-User-ID>`'
            )
        removed_troop_givers = []
        for param in params:
            if len(self.discord_coc_links_repository.get_player_tags_from_discord_id(param)) > 0:
                self.troop_givers_repository.insert_troop_giver(param, False)
                removed_troop_givers.append(param)
        if len(removed_troop_givers) == 0:
            message_content = "Aucun des IDs donnés n'est lié au compte COC d'un membre du clan"
        else:
            message_content = 'Donneurs de troupes retirés : ' + ', '.join(removed_troop_givers)
        await self.discord_api_client.send_message(message.channel_id, message_content)

    def compute_clan_name_str(self, clan: WarClan):
        return f'**`{clan.name}`**' if clan.tag == self.clan_tag else f'`{clan.name}`'

    @requires_role(ClanRole.MEMBER)
    async def cwl(self, message: Message):
        cwl_group = await self.get_current_cwl_group()
        if cwl_group is None:
            content = "Le clan n'est actuellement pas en ligue de guerres de clans"
        else:
            scores = sorted(
                cwl_group.clan_scores.items(),
                key = lambda kv: kv[1].stars + kv[1].destruction_percentage / 100_000,
                reverse=True
            )
            content = '\n'.join(
                map(
                    lambda c: self.compute_clan_name_str(c) + f' - {str(cwl_group.clan_scores[c.tag])}',
                    map(
                        lambda kv: next(filter(lambda c: c.tag == kv[0], cwl_group.clans)),
                        scores
                    )
                )
            )
            content = f'# Ligue de guerre - saison {parse_year_month(cwl_group.season)}\n' + content
            if cwl_group.state == 'inWar' and self.current_war is not None:
                content += '\n' + self.current_war.as_discord_message(self.can_use_custom_emojis, short=True)
        await self.discord_api_client.send_message(message.channel_id, content)

    async def compute_spyed_defender_string(self, war_participant: WarParticipant) -> str:
        PETS_WEIGHT, HEROES_WEIGHT, EQUIPMENTS_WEIGHT = 1, 1, 1
        player_tag = war_participant.tag
        score = 0.
        player = await self.coc_api_client.get_player(player_tag)
        if player is None:
            return war_participant.str_as_defender(self.can_use_custom_emojis)
        sorted_pets = sorted(player.pets, key = lambda p: p.max_level - p.level)
        for i in range(5):
            if i < len(sorted_pets):
                score += PETS_WEIGHT * sorted_pets[i].level / sorted_pets[i].max_level
        for hero in player.heroes:
            if hero.village != 'home':
                continue
            score += HEROES_WEIGHT * hero.level / hero.max_level
            for equipment in hero.equipment:
                score += EQUIPMENTS_WEIGHT * min(24, equipment.level) / min(24, equipment.max_level)
        return war_participant.str_as_defender(self.can_use_custom_emojis) + f' ({int(score / 3 * 100)})'

    @requires_role(ClanRole.MEMBER)
    async def spy_cwl(self, message: Message):
        current_war = await self.get_current_war()
        if current_war is None or not current_war.is_cwl or current_war.league_day is None:
            await self.discord_api_client.send_message(message.channel_id, 'Aucune ligue de guerre de clans en cours')
            return
        spyed_day = current_war.league_day
        if current_war.state == 'inWar' and spyed_day < 7:
            if current_war.league_day == 7:
                await self.discord_api_client.send_message(
                    message.channel_id,
                    'Le clan fait déjà son dernier jour de ligue, aucune guerre à espionner'
                )
                return
            else:
                spyed_day += 1

        league_group = await self.get_current_cwl_group()
        if spyed_day <= len(league_group.rounds):
            for war_tag in league_group.rounds[spyed_day - 1].war_tags:
                fetched_war = self.ended_cwl_wars.get(war_tag)
                if fetched_war is None:
                    fetched_war = await self.coc_api_client.get_cwl_war(war_tag)
                if fetched_war is None:
                    log(
                        f'Failed to find CWL war in which the linked clan participates for day {spyed_day}',
                        LogLevel.ERROR
                    )
                    await self.discord_api_client.send_message(
                        message.channel_id,
                        "La guerre à espionner n'a pas été trouvée !"
                    )
                    return
                if fetched_war.clan.tag == self.clan_tag:
                    r = await asyncio.gather(
                        *(self.compute_spyed_defender_string(m) for m in fetched_war.opponent.members)
                    )
                    message_content = f'## Clan adverse du jour {spyed_day} de ligue (prévisions)\n'
                    defenders_string = '\n'.join(r)
                    message_content += f'Contre `{fetched_war.opponent.name}`\n{defenders_string}\n'
                    message_content += '-# :warning: Le clan adverse peut changer sa composition à tout moment avant '
                    message_content += f'<t:{to_timestamp(fetched_war.war_start_time)}>'
                    await self.discord_api_client.send_message(message.channel_id, message_content)
        else:
            message_content = f'Le jour {spyed_day} ne peut pas encore être espionné'
            await self.discord_api_client.send_message(message.channel_id, message_content)

    @requires_role(ClanRole.MEMBER)
    async def war(self, message: Message):
        current_war = await self.get_current_war()
        if current_war is None:
            content = 'Aucune guerre en cours'
        else:
            content = current_war.as_discord_message(self.can_use_custom_emojis)
        await self.discord_api_client.send_message(message.channel_id, content)

    @requires_role(ClanRole.LEADER)
    async def announce(self, message: Message):
        rest = message.content.strip()[message.content.index(' ') + 1:].strip()
        if len(rest) == 0:
            return
        potential_ping_indices = [i for i, c in enumerate(rest) if c == '@']
        potential_ping_indices.reverse()
        filters = []
        for potential_ping_index in potential_ping_indices:
            custom_ping_filter = parse_custom_ping(rest[potential_ping_index:])
            if custom_ping_filter is None:
                continue
            end_index = potential_ping_index + 1  # TODO: obviously shouldn't recompute that
            while len(rest) > end_index and (rest[end_index].isalnum() or rest[end_index] in '+-|&'):
                end_index += 1
            rest = rest[:potential_ping_index] + '**`' + rest[potential_ping_index:end_index] + '`**' + rest[end_index:]
            filters.append(custom_ping_filter)

        def combined_filter(m):
            for f in filters:
                if f(m):
                    return True
            return False

        members = await self.clan_members_service.get_clan_members(combined_filter)
        discord_mentions = []
        plain_coc_nicknames = []
        for member in members:
            discord_id = self.discord_coc_links_repository.get_discord_id_from_player_tag(member.tag)
            if discord_id is not None:
                discord_mentions.append(f'<@{discord_id}>')
            else:
                plain_coc_nicknames.append(f'`{member.name}`')
        mentions = plain_coc_nicknames + discord_mentions
        pings = ('\n**Mentions :**\n||' + '** ; **'.join(mentions) + '||') if len(mentions) else ''
        await self.discord_api_client.send_message(message.channel_id, f'{rest}\n{pings}')

    @requires_role(ClanRole.MEMBER)
    async def attacks(self, message: Message):
        current_war = await self.get_current_war()
        if current_war is None:
            await self.discord_api_client.send_message(message.channel_id, 'Aucune guerre en cours')
        else:
            missing_attacks = [
                m.missing_attacks_str(current_war.attacks_per_member, self.can_use_custom_emojis, True)
                for m in current_war.clan.members
                if len(m.attacks) <current_war.attacks_per_member
            ]
            missing_attacks_str = '**Attaques restantes:**\n' + '\n'.join(missing_attacks)
            missing_attacks_str += f'\n\n_Fin de la guerre : <t:{to_timestamp(current_war.end_time)}:R>_'
            await self.discord_api_client.send_message(message.channel_id, missing_attacks_str)

    async def help(self, message: Message) -> None:
        await self.discord_api_client.send_message(message.channel_id, self.help_message)

    async def about(self, message: Message) -> None:
        info = f'- {APP_NAME} v{APP_VERSION}\n- Running on Python 3.12\n- Last restart: <t:{int(self.started_at)}:R>'
        info += '\n- https://www.github.com/ZiarZer/coc-bot'
        await self.discord_api_client.send_message(message.channel_id, info)

    @requires_role(ClanRole.LEADER)
    async def todo(self, _) -> None:
        if BACKOFFICE_CHANNEL_ID is not None:
            await self.discord_api_client.send_message(BACKOFFICE_CHANNEL_ID, '\n'.join(map(lambda t: f'- {t}', TODO)))

    async def handle_command(self, message: Message) -> None:
        if message.author.id == self.user.id:
            return
        splitted = message.content.strip().split(' ')
        if len(splitted[0]) == 0 or splitted[0][0] != self.prefix:
            return
        command_name = splitted[0][1:].lower()
        if command_name in self.commands:
            command = self.commands[command_name]
            can_run_command = message.channel_type == ChannelType.DM or command.bypass_whitelist
            if not can_run_command:
                can_run_command = self.whitelists_repository.is_whitelisted(message.channel_id, message.guild_id)
            if can_run_command:
                self.command_uses_repository.insert_command_use(message.author.id, command.name)
                await command.func(message)

    async def on_ready(self, data: dict):
        self.user = User(data['user'])
        self.can_use_custom_emojis = self.user.is_bot or self.user.has_nitro
        self.activities['CLAN'] = PresenceActivity(
            'The 3200 Club',  # TODO: fetch clan info
            0,
            self.clan_tag,
            application_id = CLAN_APPLICATION_ID
        )
        await self.get_current_war()
        now = datetime.now()
        if now.weekday() >= 4 or now.weekday() == 0 and now.hour <= 12:
            await self.get_current_capital_raid_season()
        else:
            days_delta, seconds_delta = 4 - now.weekday(), (12 - now.hour) * 3600 - now.minute * 60 - now.second
            duration = days_delta * 86400 + seconds_delta
            event_loop = asyncio.get_event_loop()
            self.raid_fetch_next_task = event_loop.call_later(duration, self.run_raid_capital_season_fetch_task)

    async def on_error(self, e: Exception):
        content = f'**:warning: ERROR**\n```\n{traceback.format_exc()}```'
        log(str(e), LogLevel.ERROR)
        if BACKOFFICE_CHANNEL_ID is not None:
            await self.discord_api_client.send_message(BACKOFFICE_CHANNEL_ID, content)

    def run_raid_capital_season_fetch_task(self):
        asyncio.create_task(self.get_current_capital_raid_season())

    def run_current_war_fetch_task(self):
        asyncio.create_task(self.get_current_war())

    async def on_message(self, data: dict):
        created_msg = Message(data)
        if created_msg.content.strip().startswith(self.prefix):
            await self.handle_command(created_msg)
