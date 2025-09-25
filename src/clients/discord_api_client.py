import os
from typing import Optional
from dotenv import load_dotenv

from models.discord import Message
from .base_api_client import BaseApiClient


DISCORD_API_BASE_URL = 'https://discord.com/api/v10'
load_dotenv()
ENV = os.environ.get('ENV', 'DEV')


class DiscordApiClient(BaseApiClient):
    def __init__(self, authorization_token: str) -> None:
        super().__init__(
            DISCORD_API_BASE_URL,
            {'Authorization': authorization_token}
        )

    async def send_message(self, channel_id: str, content: str) -> Optional[Message]:
        sent_content = content
        if ENV == 'DEV':
            if content is None:
                sent_content = ''
            sent_content += '\n-# dev'
        response = await self.POST(f'channels/{channel_id}/messages', {'content': sent_content, 'flags': 1 << 2})
        if response.status_code == 200:
            return Message(response.json())
        return None
