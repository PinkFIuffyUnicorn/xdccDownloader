from discord.ext import commands
from scripts.common.plexLibrary import PlexLibrary


class UncategorizedCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="updateAnimePlexLibrary",
        description="Update Plex library for Anime",
        help="Usage `!updateAnimePlexLibrary`"
    )
    async def updateAnimePlexLibrary(self, ctx):
        myPlexLibrary = PlexLibrary(self.bot.username, self.bot.password, self.bot.plexServerName, "Anime")
        myPlexLibrary.updatePlexLibraryData()
        await ctx.send("Anime Library Updated Successfully!")

    @commands.command(
        name="getAllActiveThreads",
        description="Get all active threads running on the bot",
        help="Usage `!getAllActiveThreads`"
    )
    async def getAllActiveThreads(self, ctx):
        activeThreads = self.bot.common_functions.getAllActiveThreadsName()
        activeThreads = "\n".join((activeThreads))
        await ctx.send(f"All active threads:\n{activeThreads}")

    @commands.command(
        name="ping",
        description="Check if the bot is responsive",
        help="Usage `!ping`"
    )
    async def ping(self, ctx):
        self.bot.logger.info("pong!")
        await ctx.send("Pong!")

async def setup(bot):
    await bot.add_cog(UncategorizedCommands(bot))