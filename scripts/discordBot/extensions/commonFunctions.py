import discord
import requests
import threading
import concurrent.futures
from scripts.common.databaseAccess import Database
from scripts.torrentDownloader.downloadTorrent import DownloadTorrent
from time import sleep
from scripts.config import config
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By


class CommonFunctions():
    def __init__(self):
        self.sql_server_name = config.sqlServerName
        self.database = config.database
        self.token = config.tokenSana
        self.discord_bot_headers = {
            "Authorization": f"Bot {self.token}",
            "User-Agent": "MyBot/1.0",
            "Content-Type": "application/json"
        }

    def currentTimestamp(self, type="print"):
        if type.lower() == "file":
            return datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
        elif type.lower() == "db":
            return datetime.now().strftime("%d_%m_%Y")
        return datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    def formatError(self, error_msg):
        return str(error_msg).replace("'", "''")

    def connectToDb(self):
        try:
            database_class = Database(self.sql_server_name, self.database)
            conn, cursor = database_class.dbConnect()
            return conn, cursor
        except Exception as e:
            return [2, f"Db Exception occured: {self.formatError(e)}"]

    def getChannelId(self, all_channels, channel_name):
        channel = discord.utils.get(all_channels, name=channel_name)
        return channel.id if channel is not None else channel

    def getAllActiveThreadsName(self):
        return [thread.name for thread in threading.enumerate()]

    def check(self, author):
        def inner_check(messsage):
            return messsage.author == author
        return inner_check

    def isAdminCheck(self, ctx):
        return "Admin" in [role.name for role in ctx.author.roles] or ctx.author.name == "Pink Fluffy Unicorn"

    def getDiscordGuildChannelLocations(self):
        conn, cursor = self.connectToDb()
        cursor.execute("""
            select channel_id from discord_guild_channel_locations where type = 'updateAnimeNotifications'
        """)
        return cursor.fetchall()

    def sendInitialEmbed(self, anime_list, torrent_download=True):
        discord_url_list = []
        channel_ids = self.getDiscordGuildChannelLocations()
        for channel_id in channel_ids:
            discord_url = "https://discordapp.com/api/v6/channels/{channel_id}/messages".format(channel_id=channel_id[0])
            discord_url_list.append(discord_url)

        embeds = []
        payload = {"embed": embeds}

        # ["", "", "name", "episode", "season", "image"]
        for index, anime in enumerate(anime_list):
            if torrent_download:
                anime_name = anime[0]
                episode = "0" + str(anime[1]) if len(str(anime[1])) == 1 else anime[1]
                current_season = "0" + str(anime[2]) if len(str(anime[2])) == 1 else anime[2]
                live_chart_image_url = anime[3]
                english_name = anime[5]
            else:
                anime_name = anime[2]
                episode = "0" + str(anime[3]) if len(str(anime[3])) == 1 else anime[3]
                current_season = "0" + str(anime[4]) if len(str(anime[4])) == 1 else anime[4]
                live_chart_image_url = anime[5]
                english_name = anime[6]

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
                    lambda url: (response := requests.post(url, json=payload, headers=self.discord_bot_headers).json()) and (
                        response["id"], response["channel_id"]), discord_url_list))
                temp_discord_url_list = []
                for message_channel_id in results:
                    message_id = message_channel_id[0]
                    channel_id = message_channel_id[1]
                    temp_discord_url_list.append(
                        f"https://discordapp.com/api/v6/channels/{channel_id}/messages/{message_id}")
                anime_list[index].append(temp_discord_url_list)

            sleep(1)

        return anime_list

    def getDayOfTheWeek(self, driver):
        time_values = driver.find_elements(By.XPATH, "//div[@class='info-bar-cell info-bar-live-element']")
        time_values = [x.text.split("\n") for x in time_values]
        time_dict = {unit: int(quantity) for quantity, unit in time_values}
        delta = timedelta(**time_dict)
        now = datetime.now()
        future_time = now + delta
        day_of_week = future_time.strftime("%u")

        return day_of_week

    def updateDownloadsTorrent(self, channel_id, anime_name=None, current_day=False):
        download_torrent = DownloadTorrent(anime_name, current_day)
        get_list_to_download = download_torrent.getAnimeListFromDbTorrent()
        if channel_id is not None:
            information_text = "" if len(get_list_to_download) == 0 else " check the notifications channel for more information"
            requests.post(url=f"https://discordapp.com/api/v6/channels/{channel_id}/messages",
                          json={"content": f"Found {len(get_list_to_download)} episodes to download{information_text}."},
                          headers=self.discord_bot_headers)
        if len(get_list_to_download) != 0:
            anime_list = self.sendInitialEmbed(get_list_to_download)
            download_torrent.downloadAnimeFromListTorrent(anime_list)
