import os
import asyncio
from dotenv import load_dotenv
from bot import Bot
from utils import log


load_dotenv()
CLAN_TAG = '#2GLCQ00G0'
SECONDARY_CLAN_TAG = '#2JG02GVYL'


async def main():
    log('bouliste2clan - \033[4mhttps://www.github.com/ZiarZer/bouliste2clan\033[0m')

    DISCORD_AUTHORIZATION_TOKEN = os.environ.get('DISCORD_AUTHORIZATION_TOKEN')
    IS_BOT_TOKEN = os.environ.get('IS_BOT_TOKEN', '1') == '1'
    discord_auth_token = f'{"Bot " if IS_BOT_TOKEN else ""}{DISCORD_AUTHORIZATION_TOKEN}'

    COC_API_TOKEN = os.environ.get('COC_API_TOKEN')

    bot = Bot(CLAN_TAG, discord_auth_token, COC_API_TOKEN, secondary_clan_tag=SECONDARY_CLAN_TAG)
    await bot.run()


if __name__ == '__main__':
    asyncio.run(main())
