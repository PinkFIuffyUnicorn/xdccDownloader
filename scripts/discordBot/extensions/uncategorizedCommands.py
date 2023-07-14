import discord
from discord.ext import commands
from scripts.common.plexLibrary import PlexLibrary

class UncategorizedCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="updateAnimePlexLibrary")
    async def updateAnimePlexLibrary(self, ctx):
        myPlexLibrary = PlexLibrary(self.bot.username, self.bot.password, self.bot.plexServerName, "Anime")
        myPlexLibrary.updatePlexLibraryData()
        await ctx.send("Anime Library Updated Successfully!")

    @commands.command(name="getAllActiveThreads")
    async def getAllActiveThreads(self, ctx):
        activeThreads = self.common_functions.getAllActiveThreadsName()
        activeThreads = "\n".join((activeThreads))
        await ctx.send(f"All active threads:\n{activeThreads}")

    @commands.command()
    async def ping(self, ctx):
        self.bot.logger.info("pong!")
        await ctx.send("Pong!")