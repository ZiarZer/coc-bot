from enum import Enum
from typing import Optional
from utils import to_timestamp, format_number
from .discord import PresenceActivity, embed


TOWNHALL_CUSTOM_EMOJIS = {
    8: '936511388849934356',
    9: '288436023573086211',
    10: '288436059203829770',
    11: '288436090665172992',
    12: '451408476426469387',
    13: '651100997367627823',
    14: '1027658536882286653',
    15: '1027658448697032714',
    16: '1183775328884228216',
    17: '1309517214113599530'
}

CUSTOM_EMOJIS = {
    'STAR': '<:star:927704564914860052>',
    'EMPTY_STAR': '<:starempty:1153758399117414502>',
    'SWORDS': '<:Swords:1115520126607958057>',
    'LOSE_WAR': '<:pleading_sob:1380234164237766826>',
    'WIN_WAR': '<:poucegg:1388150079277236234>',
}

CLAN_WAR_APPLICATION_ID = '1391897870713487451'
CWL_APPLICATION_ID = '1394456649170812939'
WEEKEND_RAID_APPLICATION_ID = '1394592567105949777'


class ClanRole(Enum):
    NOT_MEMBER = 0
    MEMBER = 1
    ADMIN = 2
    COLEADER = 3
    LEADER = 4


class ClanMember:
    def __init__(self, raw_member: dict) -> None:
        self.tag: str = raw_member['tag']
        self.name: str = raw_member['name']
        self.role = ClanRole[raw_member['role'].upper()]
        self.townhall_level: int = raw_member['townHallLevel']
        self.exp_level: int = raw_member['expLevel']
        self.donations: int = raw_member['donations']
        self.donations_received: int = raw_member['donationsReceived']
        self.trophies: int = raw_member['trophies']
        self.builder_base_trophies: int = raw_member['builderBaseTrophies']


class CapitalRaidSeasonMember:
    def __init__(self, raw_member) -> None:
        self.tag: str = raw_member['tag']
        self.name: str = raw_member['name']
        self.attacks: int = raw_member['attacks']
        self.attack_limit: int = raw_member['attackLimit']
        self.bonus_attack_limit: int = raw_member['bonusAttackLimit']
        self.capital_resources_looted: int = raw_member['capitalResourcesLooted']


class CapitalRaidSeason:
    def __init__(self, raw_season: dict) -> None:
        self.state: str = raw_season['state']
        self.war_start_time: Optional[str] = raw_season.get('startTime')
        self.end_time: Optional[str] = raw_season.get('endTime')
        self.capital_total_loot: int = raw_season['capitalTotalLoot']
        self.raids_completed: int = raw_season['raidsCompleted']
        self.total_attacks: int = raw_season['totalAttacks']
        self.enemy_districts_destroyed: int = raw_season['enemyDistrictsDestroyed']
        self.offensive_reward: int = raw_season['offensiveReward']
        self.defensive_reward: int = raw_season['defensiveReward']
        sorted_raid_members = sorted(
            raw_season.get('members', []),
            key=lambda m: m['capitalResourcesLooted'],
            reverse=True
        )
        self.members = [CapitalRaidSeasonMember(member) for member in sorted_raid_members]

    def build_presence_activity(self) -> Optional[PresenceActivity]:
        if self.state != 'ongoing':
            return None
        return PresenceActivity(
            f'Week-end de Raids',
            5,
            # f'Contre {self.current_war.opponent.name}',
            state=f'{format_number(self.capital_total_loot)} joyaux récoltés',
            end_timestamp = 1000 * to_timestamp(self.end_time),
            application_id = WEEKEND_RAID_APPLICATION_ID
        )


class ClanWarAttack:
    def __init__(self, raw_attack) -> None:
        self.order: int = raw_attack.get('order')
        self.attacker_tag: str = raw_attack.get('attackerTag')
        self.defender_tag: str = raw_attack.get('defenderTag')
        self.stars: int = raw_attack.get('stars')
        self.destruction_percentage: float = round(raw_attack.get('destructionPercentage'), 2)
        self.duration: int = raw_attack.get('duration')


class WarParticipant:
    def __init__(self, raw_participant, current_war_position = None) -> None:
        self.tag: str = raw_participant['tag']
        self.name: str = raw_participant['name']
        self.map_position: int = raw_participant.get('mapPosition')
        self.current_war_position: int = current_war_position
        self.townhall_level: int = raw_participant.get('townhallLevel')
        self.attacks = list(map(ClanWarAttack, raw_participant.get('attacks', [])))
        self.opponent_attacks: int = raw_participant.get('opponentAttacks')
        self.best_opponent_attack = None
        if self.opponent_attacks:
            self.best_opponent_attack = ClanWarAttack(raw_participant.get('bestOpponentAttack'))

    def str_as_defender(self, use_custom_emojis) -> str:
        townhall = self.str_townhall(use_custom_emojis)
        star = ':star:' if not use_custom_emojis else CUSTOM_EMOJIS['STAR']
        empty_star = '' if not use_custom_emojis else CUSTOM_EMOJIS['EMPTY_STAR']
        s = f'{townhall} - ``{str(self.current_war_position or "?").rjust(2, " ")}. {self.name}``'
        if self.best_opponent_attack is not None and self.best_opponent_attack.stars > 0:
            star_emojis = star * self.best_opponent_attack.stars + (3 - self.best_opponent_attack.stars) * empty_star
            s += '(' + star_emojis + f' - {self.best_opponent_attack.destruction_percentage}%)'
        return s

    def missing_attacks_str(self, attacks_per_member, use_custom_emojis, show_townhall_level = False) -> str:
        s = f'`{self.current_war_position or "?"}. {self.name}` ({len(self.attacks)}/{attacks_per_member})'
        if show_townhall_level:
            s = f'{self.str_townhall(use_custom_emojis)} - {s}'
        return s

    def str_townhall(self, use_custom_emojis) -> str:
        if use_custom_emojis and self.townhall_level in TOWNHALL_CUSTOM_EMOJIS:
            return f'<:th{self.townhall_level}:{TOWNHALL_CUSTOM_EMOJIS[self.townhall_level]}>'
        return f'TH{self.townhall_level}'


class WarClan:
    def __init__(self, raw_war_clan) -> None:
        self.destruction_percentage: float = round(raw_war_clan.get('destructionPercentage'), 2)
        self.tag: str = raw_war_clan.get('tag')
        self.name: str = raw_war_clan.get('name')
        self.clan_level: int = raw_war_clan.get('clanLevel')
        self.attacks: int = raw_war_clan.get('attacks')
        self.stars: int = raw_war_clan.get('stars')
        self.exp_earned: int = raw_war_clan.get('expEarned')
        self.members = [WarParticipant(member, idx + 1) for idx, member in enumerate(
            sorted(raw_war_clan.get('members', []), key=lambda m: m['mapPosition'])
        )]

    def __eq__(self, other_war_clan) -> bool:
        if self.tag != other_war_clan.tag or self.name != other_war_clan.name:
            return False
        if self.stars != other_war_clan.stars or self.destruction_percentage != other_war_clan.destruction_percentage:
            return False
        if self.attacks != other_war_clan.attacks or self.exp_earned != other_war_clan.exp_earned:
            return False
        return True


class War:
    def __init__(self, raw_clan: dict, is_cwl = False, tag: Optional[str] = None) -> None:
        self.state: str = raw_clan['state']
        self.clan = WarClan(raw_clan['clan'])
        self.opponent = WarClan(raw_clan['opponent'])
        self.team_size: int = raw_clan.get('teamSize', 0)
        self.battle_modifier: str = raw_clan.get('battleModifier', 'none')
        self.preparation_start_time: Optional[str] = raw_clan.get('preparationStartTime')
        self.war_start_time: Optional[str] = raw_clan.get('warStartTime') or raw_clan.get('startTime')
        self.end_time: Optional[str] = raw_clan.get('endTime')
        self.is_cwl = is_cwl
        self.attacks_per_member: int = raw_clan.get('attacksPerMember', 1 if self.is_cwl else 2)
        self.attacks_per_clan = self.attacks_per_member * self.team_size

        self.league_day: Optional[int] = None
        self.tag: Optional[str] = tag

    def __eq__(self, other_war) -> bool:
        if other_war is None:
            return False
        if self.state != other_war.state or self.clan != other_war.clan or self.opponent != other_war.opponent:
            return False
        if self.is_cwl != other_war.is_cwl:
            return False
        return True

    def as_discord_message(self, use_custom_emojis, short = False) -> str:
        vs_emoji = ':vs:' if not use_custom_emojis else CUSTOM_EMOJIS['SWORDS']
        star_emoji = ':star:' if not use_custom_emojis else CUSTOM_EMOJIS['STAR']
        lose_war_emoji = ':broken_heart:' if not use_custom_emojis else CUSTOM_EMOJIS['LOSE_WAR']
        win_war_emoji = ':mechanical_arm:' if not use_custom_emojis else CUSTOM_EMOJIS['WIN_WAR']

        if self.state == 'notInWar':
            return 'Aucune guerre en cours'
        title = 'GDC actuelle'
        if self.league_day is not None:
            title += f' - Jour {self.league_day} de Ligue'
        main_info = f'## {title}\n**`{self.clan.name}`** {vs_emoji} `{self.opponent.name}`\n'

        if self.state == 'preparation':
            main_info += f'Début du jour de combat dans : <t:{to_timestamp(self.war_start_time)}:R>'
            return main_info

        clan_attacks = f'{self.clan.attacks}/{self.attacks_per_clan}'
        opponent_attacks = f'{self.opponent.attacks}/{self.attacks_per_clan}'
        main_info += f'{self.clan.stars} {star_emoji} {self.opponent.stars}\n'
        main_info += f'{self.clan.destruction_percentage}% - {self.opponent.destruction_percentage}%\n'
        main_info += f'{clan_attacks} :crossed_swords: {opponent_attacks}\n'
        if self.state == 'warEnded':
            star_diff = self.clan.stars - self.opponent.stars
            percentage_diff = self.clan.destruction_percentage - self.opponent.destruction_percentage
            if star_diff == 0 and percentage_diff == 0:
                main_info += '## :handshake: Égalité'
            elif star_diff > 0 or (star_diff == 0 and percentage_diff > 0):
                main_info += f'## {win_war_emoji} Victoire'
            else:
                main_info += f'## {lose_war_emoji} Défaite'
        elif self.state == 'inWar':
            main_info += f'Fin dans : <t:{to_timestamp(self.end_time)}:R>\n'
            if short:
                return main_info

            uncleared_bases = [
                m.str_as_defender(use_custom_emojis)
                for m in self.opponent.members
                if m.best_opponent_attack is None or m.best_opponent_attack.stars < 3
            ]
            if len(uncleared_bases) == 0:
                main_info += '\n:white_check_mark: Tous les villages ennemis détruits à 100%'
                return main_info

            uncleared_bases_str = '\n'.join(uncleared_bases)
            main_info += f'\n**Villages ennemis restants :**\n{uncleared_bases_str}\n'
            missing_attacks = [
                m.missing_attacks_str(self.attacks_per_member, use_custom_emojis)
                for m in self.clan.members
                if len(m.attacks) <self.attacks_per_member
            ]
            if len(missing_attacks) > 0:
                missing_attacks_str = '   **;**   '.join(missing_attacks)
                main_info += f'\n**Attaques restantes :**\n{missing_attacks_str}\n'
            else:
                main_info += '\n:white_check_mark: **Aucune attaque restante**'

        return main_info

    def build_presence_activity(self) -> Optional[PresenceActivity]:
        if self.state not in ('inWar', 'preparation', 'warEnded'):
            return None

        if self.state == 'preparation':
            activity_state = 'Préparation'
        else:
            activity_state = f'{self.clan.stars} ★ {self.opponent.stars}'
        activity_details = f'Contre {self.opponent.name}'
        if self.state == 'warEnded':
            star_diff = self.clan.stars - self.opponent.stars
            percentage_diff = self.clan.destruction_percentage - self.opponent.destruction_percentage
            activity_details = 'Défaite'
            if star_diff == 0 and percentage_diff == 0:
                activity_details = 'Égalité'
            elif star_diff > 0 or (star_diff == 0 and percentage_diff > 0):
                activity_details = 'Victoire'
        return PresenceActivity(
            f'Guerre de Clans - Jour {self.league_day} de Ligue' if self.is_cwl else 'Guerre de Clans',
            5,
            activity_details,
            activity_state,
            end_timestamp = 1000 * to_timestamp(self.end_time),
            application_id = CLAN_WAR_APPLICATION_ID
        )

    def build_cwl_presence_activity(self) -> Optional[PresenceActivity]:
        if not self.is_cwl:
            return None
        end_timestamp = to_timestamp(self.end_time) + 25 * 3600 * (7 - (self.league_day or 0))
        return PresenceActivity(
            'Ligue de Guerre de Clans',
            5,
            f'Jour {self.league_day}',
            end_timestamp = 1000 * end_timestamp,
            application_id = CWL_APPLICATION_ID
        )


class CWLClan:
    class Member:
        def __init__(self, raw_member) -> None:
            self.tag = raw_member.get('tag')
            self.townhall_level = raw_member.get('townHallLevel')
            self.name = raw_member.get('name')

    def __init__(self, raw_cwl_clan) -> None:
        self.tag = raw_cwl_clan.get('tag')
        self.name = raw_cwl_clan.get('name')
        self.clan_level = raw_cwl_clan.get('clanLevel')
        self.members = list(map(CWLClan.Member, raw_cwl_clan.get('members', [])))


class WarScore:
    def __init__(self, stars: int = 0, destruction_percentage: float = 0) -> None:
        self.stars = stars
        self.destruction_percentage = destruction_percentage

    def add_to_score(self, war_clan: WarClan) -> None:
        self.stars += war_clan.stars
        self.destruction_percentage += war_clan.destruction_percentage

    def __str__(self) -> str:
        return f':star: {self.stars} - {int(self.destruction_percentage)}%'


class CWLGroup:
    class Round:
        def __init__(self, raw_round) -> None:
            self.war_tags: list[str] = raw_round.get('warTags')

    def __init__(self, raw_cwl_group) -> None:
        self.tag = raw_cwl_group.get('tag')
        self.state = raw_cwl_group.get('state')
        self.season = raw_cwl_group.get('season')
        self.clans = raw_cwl_group.get('clans')
        self.clans = list(map(CWLClan, raw_cwl_group.get('clans', [])))
        self.rounds = [
            round for round in map(CWLGroup.Round, raw_cwl_group.get('rounds', [])) if '#0' not in round.war_tags
        ]


class Pet(Enum):
    LASSI = 'L.A.S.S.I'
    MIGHTY_YAK = 'Mighty Yak'
    ELECTRO_OWL = 'Electro Owl'
    UNICORN = 'Unicorn'
    PHOENIX = 'Phoenix'
    POISON_LIZARD = 'Poison Lizard'
    DIGGY = 'Diggy'
    FROSTY = 'Frosty'
    SPIRIT_FOX = 'Spirit Fox'
    ANGRY_JELLY = 'Angry Jelly'


class Clan:
    def __init__(self, raw_clan: dict) -> None:
        self.tag: str = raw_clan['tag']
        self.name: str = raw_clan['name']
        self.badge_url: str = raw_clan['badgeUrls']['large']

    def as_discord_embed(self) -> embed.Embed:
        invite_link = f'https://link.clashofclans.com/fr?action=OpenClanProfile&tag={self.tag}'
        return embed.Embed(self.name, self.tag, url=invite_link).set_thumbnail(self.badge_url)


class Player:
    class Hero:
        class Equipment:
            def __init__(self, raw_equipment: dict) -> None:
                self.level: int = raw_equipment['level']
                self.max_level: int = raw_equipment['maxLevel']

        def __init__(self, raw_hero: dict) -> None:
            self.level: int = raw_hero['level']
            self.max_level: int = raw_hero['maxLevel']
            self.village: str = raw_hero['village']
            self.equipment = list(map(Player.Hero.Equipment, raw_hero.get('equipment', [])))

    class Troop:
        def __init__(self, raw_troop: dict) -> None:
            self.level: int = raw_troop['level']
            self.max_level: int = raw_troop['maxLevel']
            self.name: int = raw_troop['name']

    def __init__(self, raw_player: dict) -> None:
        all_troops = map(Player.Troop, raw_player['troops'])
        self.pets = list(filter(lambda t: t.name in Pet, all_troops))
        self.troops = list(filter(lambda t: t.name not in Pet, all_troops))
        self.heroes = list(map(Player.Hero, raw_player['heroes']))
