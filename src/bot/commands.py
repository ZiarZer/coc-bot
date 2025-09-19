from functools import wraps
from models.clash_of_clans import ClanRole
from utils import log, LogLevel


class Command:
    def __init__(self, name, func, aliases = None, hidden = False, bypass_whitelist = False):
        self.name = name
        self.aliases = aliases or []
        self.hidden = hidden
        self.bypass_whitelist = bypass_whitelist
        self.func = func

    def help_entry(self, prefix) -> str:
        return '- ' + ' / '.join([f'`{prefix}{a}`' for a in ([self.name] + self.aliases)])


def requires_role(role: ClanRole = ClanRole.NOT_MEMBER):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, message):
            if role != ClanRole.NOT_MEMBER:
                player_tags = self.discord_coc_links_repository.get_player_tags_from_discord_id(message.author.id)
                clan_members = await self.clan_members_service.get_clan_members(lambda m: m.role.value >= role.value)
                eligible_members = sorted(
                    (m for m in clan_members if m.tag in player_tags),
                    key=lambda m: m.role.value,
                    reverse=True
                )
                if len(eligible_members) == 0:
                    log('No eligible clan member found for the Discord account that ran the command', LogLevel.INFO)
                    return
                log(f'Player {eligible_members[0].name} ({eligible_members[0].role.name}) eligible', LogLevel.INFO)
            await func(self, message)
        return wrapper
    return decorator
