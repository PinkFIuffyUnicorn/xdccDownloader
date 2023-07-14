import os
import fnmatch
import threading
import time
from time import sleep
import qbittorrentapi
from dataclasses import dataclass
import discord
import concurrent.futures
from puffotter.units import human_readable_bytes
import requests
from scripts.config import config
from scripts.common.plexLibrary import PlexLibrary

@dataclass
class QBitTorrent():
    """Class for QBitTorrent operations"""
    server: str
    port: int

    def __init__(self, server: str, port: int):
        self.server = server
        self.port = port
        self.client = qbittorrentapi.Client(
            host=self.server,
            port=self.port
        )
        self.discord_bot_headers = {
            "Authorization": f"Bot {config.tokenSana}",
            "User-Agent": "MyBot/1.0",
            "Content-Type": "application/json"
        }

    def secondsToHMS(self, time_in_seconds):
        hours = time_in_seconds // 3600
        minutes = (time_in_seconds % 3600) // 60
        seconds = time_in_seconds % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        elif minutes > 0:
            return f"{minutes:02d}:{seconds:02d}"
        else:
            return f"{seconds:02d}s"

    def addTorent(self, anime: list):
        anime_name = anime[0]
        episode = "0" + str(anime[1]) if len(str(anime[1])) == 1 else anime[1]
        # season = "0" + str(anime[2]) if len(str(anime[2])) == 1 else anime[2]
        torrent_url = anime[4]
        save_path = f"{config.parentDir}\{anime_name}\Season {anime[2]}"
        seasonEpisode = "01" if anime[1] != 0 else "00"
        if os.path.isdir(save_path):
            seasonEpisode = len([x for x in fnmatch.filter(os.listdir(save_path), "*.mkv") if "- 00 (" not in x]) + 1
            seasonEpisode = "0" + str(seasonEpisode) if len(str(seasonEpisode)) == 1 else seasonEpisode
        # filename = f"{anime_name} - s{season}e{seasonEpisode} (1080p) [{episode}].mkv"
        filename = f"{anime_name} - {seasonEpisode} (1080p) [{episode}].mkv"
        self.client.torrents_add(urls=torrent_url, save_path=save_path, rename=filename, category=anime_name)
        sleep(2)
        torrent = self.getTorrentByName(filename, anime_name)
        torrent_hash = torrent.hash
        self.client.torrents_pause(torrent_hash)
        for file in torrent.files:
            self.client.torrents_rename_file(torrent_hash, file.id, filename)
        self.client.torrents_resume(torrent_hash)
        sleep(2)
        thread = threading.Thread(target=self.sendProgress, args=(torrent_hash, anime), name=f"send_progress_{anime_name}")
        thread.start()

    def getTorrentByName(self, filename: str, category: str):
        while True:
            torrents = self.client.torrents_info(category=category)
            torrents = [torrent for torrent in torrents if torrent.name.startswith(filename)]
            if len(torrents) > 1:
                return f"ERROR: Multiple torrents found for filename: {filename}"
            elif len(torrents) == 0:
                continue
            return torrents[0]

    def getTorrentByHash(self, torrent_hash: str):
        while True:
            torrents = self.client.torrents_info(torrent_hashes=torrent_hash)
            if len(torrents) > 1:
                return f"ERROR: Multiple torrents found for Hash: {torrent_hash}"
            elif len(torrents) == 0:
                continue
            return torrents[0]

    def sendProgress(self, torrent_hash: str, anime: list):
        anime_name = anime[0]
        episode = anime[1]
        current_season = anime[2]
        live_chart_image_url = anime[3]
        english_name = anime[5]
        discord_url_list = anime[6]
        download_status = "Preparing Download"
        torrent = self.getTorrentByHash(torrent_hash)

        embed = discord.Embed(title="Anime Downloading",
                              description=f"**{anime_name}** Season **{current_season}** Episode **{episode}** is currently downloading",
                              color=0xFFFF33)
        # embed.set_thumbnail(url=live_chart_image_url)
        embed.set_image(url=live_chart_image_url)
        embed.add_field(name="English Name", value=english_name, inline=True)
        embed.add_field(name="File Size",
                        value=f"{human_readable_bytes(torrent.downloaded)}/{human_readable_bytes(torrent.size)}",
                        inline=True)
        embed.add_field(name="Download Progress", value=f"{0}% complete", inline=True)
        embed.add_field(name="Download Speed", value=0, inline=True)
        embed.add_field(name="Time Remaining", value="-", inline=True)
        embed.add_field(name="Status", value=download_status, inline=True)
        embed.set_footer(text="This is an automated message.")
        embed_dict = embed.to_dict()
        payload = {"embed": embed_dict}

        speed_progress = []
        downloading = True
        while downloading:
            sleep(5)
            torrent = self.getTorrentByHash(torrent_hash)
            download_status = "Downloading"
            speed_progress.append({
                "timestamp": time.time(),
                "progress": torrent.downloaded
            })
            while len(speed_progress) > 0 and time.time() - speed_progress[0]["timestamp"] > 7:
                speed_progress.pop(0)
            if len(speed_progress) > 0:
                bytes_delta = torrent.downloaded - speed_progress[0]["progress"]
                time_delta = time.time() - speed_progress[0]["timestamp"]
                ratio = int(bytes_delta / time_delta) if time_delta != 0 else 0
                speed = human_readable_bytes(ratio) + "/s"
            else:
                speed = "0B/s"
            time_remaining = torrent.eta
            percentage = "%.2f" % (100 * torrent.progress)
            size_downloaded = human_readable_bytes(torrent.downloaded, remove_trailing_zeroes=False)
            if torrent.progress == 1:
                downloading = False
                time_remaining = 0
                percentage = 100
                size_downloaded = human_readable_bytes(torrent.size)
                download_status = "Completed"
                embed.title = "Anime Finished Downloading"
                embed.description = f"**{anime_name}** Season **{current_season}** Episode **{episode}** Finished Downloading"
                embed.color = 0x30fc03
                embed_dict = embed.to_dict()
                speed = "-"
            embed.set_field_at(1, name="File Size",
                               value=f"{size_downloaded}/{human_readable_bytes(torrent.size)}")
            embed.set_field_at(2, name="Download Progress", value=f"{percentage}% complete")
            embed.set_field_at(3, name="Download Speed", value=f"{speed}")
            embed.set_field_at(4, name="Time Remaining", value=f"{self.secondsToHMS(time_remaining)}")
            embed.set_field_at(5, name="Status", value=download_status)
            payload["embed"] = embed_dict
            with concurrent.futures.ThreadPoolExecutor() as executor:
                tuple(executor.map(lambda url: (response := requests.patch(url, json=payload, headers=self.discord_bot_headers).json()),
                                   discord_url_list))
        myPlexLibrary = PlexLibrary(config.username, config.password, config.plexServerName, "Anime")
        myPlexLibrary.updatePlexLibraryData()