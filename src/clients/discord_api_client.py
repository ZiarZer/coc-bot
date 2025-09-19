from typing import Optional

from models.discord import Message
from .base_api_client import BaseApiClient


DISCORD_API_BASE_URL = 'https://discord.com/api/v10'


class DiscordApiClient(BaseApiClient):
    def __init__(self, authorization_token: str) -> None:
        super().__init__(
            DISCORD_API_BASE_URL,
            {'Authorization': authorization_token}
        )

    async def send_message(self, channel_id: str, content: str) -> Optional[Message]:
        response = await self.POST(f'channels/{channel_id}/messages', {'content': content, 'flags': 1 << 2})
        if response.status_code == 200:
            return Message(response.json())
        return None
