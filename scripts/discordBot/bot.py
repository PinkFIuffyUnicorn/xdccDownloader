from discord.ext import commands, tasks
from scripts.xdccDownloader.downloadXdcc import *
from scripts.common.plexLibrary import PlexLibrary
from extensions.commonFunctions import *
import xml.etree.ElementTree as ET
from extensions.locations import Locations
from extensions.displayLists import DisplayLists
from extensions.animeUpdates import AnimeUpdates
from scripts.config import config

# Plex
username = config.username
password = config.password
plexServerName = config.plexServerName
# Discord Bot
token = config.tokenSana


# TOKEN = "NDM2NTkyNDYzNTI5MTE1NjU4.GqVmYZ.qAVHdJzGg1rji8pvjMNpeyuy4NGSc26n7uKaAc" # Sana-Chan
# TOKEN = "OTk1NzMyOTUxMzc3NjQ5ODc1.Ga19dj.THhyXe1I6wmHEL_iWuBrGIsTdoo9dtiSXoYpP4" # Igor Igorović
bot = commands.Bot(command_prefix="!")
bot.add_cog(Locations(bot))
bot.add_cog(DisplayLists(bot))
bot.add_cog(AnimeUpdates(bot))
discord_bot_headers = {
        "Authorization": f"Bot {token}",
        "User-Agent": "MyBot/1.0",
        "Content-Type": "application/json"
    }

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")

@bot.command(name="updateAnimePlexLibrary")
async def updateAnimePlexLibrary(ctx):
    myPlexLibrary = PlexLibrary(username, password, plexServerName, "Anime")
    myPlexLibrary.updatePlexLibraryData()
    await ctx.send("Anime Library Updated Successfully!")

@bot.command(name="getAllActiveThreads")
async def getAllActiveThreads(ctx):
    activeThreads = getAllActiveThreadsName()
    for thread in activeThreads:
        print(thread)

@tasks.loop(seconds=3600)
async def updateAnimeDownloadsForTodayLoop():
    print("loop - start")
    get_list_to_download = getAnimeListFromDb(downloadCurrentDay=True)
    # print(len(get_list_to_download))
    anime_list = sendInitialEmbed(get_list_to_download)
    downloadAnimeFromList(anime_list)
    print("loop - end")

@bot.command(name="test")
async def test(ctx):
    await ctx.send("TEST!")

bot.run(token)