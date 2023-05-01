import multiprocessing
import concurrent.futures
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import requests
import math
import pprint
import os
import sys
import discord
from discord.ext import commands, tasks
import configparser
from scripts.common.databaseAccess import Database
from scripts.common.customLogger import Logger
from scripts.common.enumTypes import Types
from scripts.xdccDownloader.downloadXdcc import *
from scripts.common.plexLibrary import PlexLibrary
from extensions.commonFunctions import *
import urllib.request
import pathlib
import configparser
import xml.etree.ElementTree as ET
import threading
from extensions.locations import Locations
from extensions.displayLists import DisplayLists
from extensions.animeUpdates import AnimeUpdates
from scripts.config import config

# Plex
username = config.username
password = config.password
plexServerName = config.plexServerName
# Discord Bot
token = config.token


# TOKEN = "NDM2NTkyNDYzNTI5MTE1NjU4.GoOVnc.xD1HZv1XOuacqIygVeqESxlSju9HN7G_2m66LA" # Sana-Chan
# TOKEN = "OTk1NzMyOTUxMzc3NjQ5ODc1.G_gaRf.mEkzfCdNLd3nb0uvum31NBsm26rQHRWfyDWmls" # Igor Igorović
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
    # myLoop.start()
    # newAnimeReleasesLoop.start()
    # updateAnimeDownloadsForTodayLoop.start()
    print(f"{bot.user} is online!")


@bot.command(name="updateAnimePlexLibrary")
async def updateAnimePlexLibrary(ctx):
    myPlexLibrary = PlexLibrary(username, password, plexServerName, "Anime")
    myPlexLibrary.updatePlexLibraryData()
    await ctx.send("Anime Library Updated Successfully!")

@tasks.loop(seconds=3600)
async def updateAnimeDownloadsForTodayLoop():
    print("loop - start")
    get_list_to_download = getAnimeListFromDb(downloadCurrentDay=True)
    print(len(get_list_to_download))
    anime_list = sendInitialEmbed(get_list_to_download)
    downloadAnimeFromList(anime_list)
    print("loop - end")


@tasks.loop(seconds=600)
async def newAnimeReleasesLoop():
    response = requests.get("https://www.livechart.me/feeds/episodes")
    tree = ET.ElementTree(ET.fromstring(response.text))
    root = tree.getroot()
    channel = root[0]
    items = channel.findall("item")

    for item in items:
        guid = item.find("guid").text
        titleSplit = item.find("title").text.split("#")
        title = titleSplit[0].strip()
        cleanTitle = u"".join(e for e in title if e.isalnum() or e == " ").strip()
        episode = titleSplit[1].strip()

        print(title, "|", cleanTitle)

        # mainFunc(printOutput=False, downloadAnimeName=title, guid=guid)

@bot.command(name="test")
async def test(ctx):
    await ctx.send("TEST!")

bot.run(token)