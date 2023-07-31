from discord.ext import commands, tasks
from extensions.commonFunctionsDiscord import CommonFunctionsDiscord
from extensions.locations import Locations
from extensions.displayLists import DisplayLists
from extensions.animeUpdates import AnimeUpdates
from extensions.uncategorizedCommands import UncategorizedCommands
from scripts.config import config

TOKEN = config.tokenSana


class MyBot(commands.Bot):
    def __init__(self, command_prefix, **options):
        super().__init__(command_prefix, **options)
        self.logger = config.logger
        self.common_functions = CommonFunctionsDiscord()
        # Plex Config
        self.username = config.username
        self.password = config.password
        self.plexServerName = config.plexServerName
        # Database Config
        self.sql_server_name = config.sqlServerName
        self.database = config.database

        self.add_cog(Locations(self))
        self.add_cog(DisplayLists(self))
        self.add_cog(AnimeUpdates(self))
        self.add_cog(UncategorizedCommands(self))
        self.discord_bot_headers = {
                "Authorization": f"Bot {TOKEN}",
                "User-Agent": "MyBot/1.0",
                "Content-Type": "application/json"
            }

    async def on_ready(self):
        self.logger.info(f"Discord Bot {self.user} is online")
        print(f"{self.user} is online!")


bot = MyBot(command_prefix="!")
bot.run(TOKEN)