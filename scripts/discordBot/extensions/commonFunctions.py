import sys
import time
import discord
import requests
import threading
import concurrent.futures
from scripts.common.databaseAccess import Database
import configparser
from scripts.xdccDownloader.downloadXdcc import getAnimeListFromDb, downloadAnimeFromList
from time import sleep
from scripts.config import config

# Database
sqlServerName = config.sqlServerName
database = config.database
# Discord Bot
token = config.token

discord_bot_headers = {
        "Authorization": f"Bot {token}",
        "User-Agent": "MyBot/1.0",
        "Content-Type": "application/json"
    }

def formatError(errorMsg):
    return str(errorMsg).replace("'","''")

def connectToDb(sqlServerName, database):
    try:
        databaseClass = Database(sqlServerName, database)
        conn, cursor = databaseClass.dbConnect()
        return conn, cursor
    except Exception as e:
        # sys.exit(1)
        return [2, f"Db Exception occured: {formatError(e)}"]

def getChannelId(allChannels, channelName):
    channel = discord.utils.get(allChannels, name=channelName)
    return channel.id if channel != None else channel

def getAllActiveThreadsName():
    return [thread.name for thread in threading.enumerate()]

def check(author):
    def inner_check(messsage):
        return messsage.author == author
    return inner_check

def isAdminCheck(ctx):
    return "GayRole" in [role.name for role in ctx.author.roles] or ctx.author.name == "Pink Fluffy Unicorn"

def getDiscordGuildChannelLocations():
    conn, cursor = connectToDb(sqlServerName, database)
    cursor.execute("""
        select channel_id from discord_guild_channel_locations where type = 'updateAnimeNotifications'
    """)

    return cursor.fetchall()

def sendInitialEmbed(anime_list):
    discord_url_list = []
    channel_ids = getDiscordGuildChannelLocations()
    for channel_id in channel_ids:
        discord_url = "https://discordapp.com/api/v6/channels/{channel_id}/messages".format(channel_id=channel_id[0])
        discord_url_list.append(discord_url)

    embeds = []
    payload = {"embed": embeds}

    # ["", "", "name", "episode", "season", "image"]
    for index, anime in enumerate(anime_list):
        anime_name = anime[2]
        episode = "0" + str(anime[3]) if len(str(anime[3])) == 1 else anime[3]
        current_season = "0" + str(anime[4]) if len(str(anime[4])) == 1 else anime[4]
        live_chart_image_url = anime[5]
        english_name = anime[6] if len(anime) > 6 else ""

        embed = discord.Embed(title="Anime Queued For Downloading",
                              description=f"**{anime_name}** Season **{current_season}** Episode **{episode}** has been queued for downloading.",
                              color=0x3234a8)
        embed.set_image(url=live_chart_image_url)
        embed.add_field(name="English Name", value=english_name, inline=True)
        embed.add_field(name="File Size", value="-/-", inline=True)
        embed.add_field(name="Download Progress", value=f"{0}% complete", inline=True)
        embed.add_field(name="Download Speed", value=0, inline=True)
        embed.add_field(name="Time Remaining", value="-", inline=True)
        embed.add_field(name="Status", value="Queued", inline=True)
        embed.set_footer(text="This is an automated message.")
        embed_dict = embed.to_dict()
        # embeds.append(embed)
        payload["embed"] = embed_dict

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = tuple(executor.map(
                lambda url: (response := requests.post(url, json=payload, headers=discord_bot_headers).json()) and (
                    response["id"], response["channel_id"]), discord_url_list))
            temp_discord_url_list = []
            for message_channel_id in results:
                message_id = message_channel_id[0]
                channel_id = message_channel_id[1]
                temp_discord_url_list.append(
                    f"https://discordapp.com/api/v6/channels/{channel_id}/messages/{message_id}")
            anime_list[index].append(temp_discord_url_list)

        sleep(0.5)

    return anime_list

def updateDownloads(channel_id, anime_name=None, current_day=False):
    getListToDownload = getAnimeListFromDb(downloadCurrentDay=current_day) if anime_name is None else getAnimeListFromDb(downloadAnimeName=anime_name)
    information_text = "" if len(getListToDownload) == 0 else " check the notifications channel for more information"
    requests.post(url=f"https://discordapp.com/api/v6/channels/{channel_id}/messages",
                  json={"content": f"Found {len(getListToDownload)} Anime to download{information_text}."},
                  headers=discord_bot_headers)
    if information_text != "":
        anime_list = sendInitialEmbed(getListToDownload)
        downloadAnimeFromList(anime_list)