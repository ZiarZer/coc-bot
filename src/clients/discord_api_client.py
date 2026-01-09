import os
from typing import Optional
from dotenv import load_dotenv

from models.discord import Message, Guild, embed
from .base_api_client import BaseApiClient
from utils import get_base64_image_from_url


DISCORD_API_BASE_URL = 'https://discord.com/api/v10'
load_dotenv()
ENV = os.environ.get('ENV', 'DEV')


def format_message_content_for_env(message: Optional[str]) -> Optional[str]:
    if ENV == 'DEV':
        sent_content = message if message is not None else ''
        return f"{sent_content}\n-# dev"
    return message


class DiscordApiClient(BaseApiClient):
    def __init__(self, authorization_token: str) -> None:
        super().__init__(
            DISCORD_API_BASE_URL,
            {'Authorization': authorization_token}
        )

    async def send_message(
        self,
        channel_id: str,
        content: Optional[str],
        embeds: Optional[list[embed.Embed]] = None
    ) -> Optional[Message]:
        sent_content = format_message_content_for_env(content)
        body: dict = {'content': sent_content, 'flags': 1 << 2}
        if embeds is not None:
            body['embeds'] = list(map(lambda e: e.to_dict(), embeds))
            body['flags'] = 0
        response = await self.POST(f'channels/{channel_id}/messages', body)
        if response.status_code == 200:
            return Message(response.json())
        return None

    async def edit_message(
        self,
        channel_id: str,
        message_id: str,
        content: Optional[str],
        embeds: Optional[list[embed.Embed]] = None
    ) -> Optional[Message]:
        sent_content = format_message_content_for_env(content)
        body: dict = {'content': sent_content, 'flags': 1 << 2}
        if embeds is not None:
            body['embeds'] = list(map(lambda e: e.to_dict(), embeds))
            body['flags'] = 0
        response = await self.PATCH(f'channels/{channel_id}/messages/{message_id}', body)
        if response.status_code == 200:
            return Message(response.json())
        return None

    async def react_message(self, channel_id: str, message_id: str, emoji: str) -> bool:
        response = await self.PUT(f'channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me')
        return response.status_code == 204

    async def modify_guild(self, guild_id, name = None, icon_url = None) -> Optional[Guild]:
        body: dict = {}
        if name is not None:
            body['name'] = name
        if icon_url is not None:
            body['icon'] = get_base64_image_from_url(icon_url)  # Should not update if cannot convert icon URL
        response = await self.PATCH(f'guilds/{guild_id}', body)
        if response.status_code == 200:
            return Guild(response.json())
        return None
