import sys

import qbittorrentapi
from dataclasses import dataclass
from time import sleep
import os
import re

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

    def addTorent(self, torrent_url: str, anime: list):
        anime_name = anime[0]
        episode = "0" + str(anime[1]) if len(str(anime[1])) == 1 else anime[1]
        season = "0" + str(anime[2]) if len(str(anime[2])) == 1 else anime[2]
        filename = f"{anime_name} - s{season}e{episode} (1080p) [{episode}].mkv"
        anime_name_dir = f"C:\{anime_name}"
        anime_season_dir = f"{anime_name_dir}\Season {season}"
        self.client.torrents_add(urls=torrent_url, save_path=anime_season_dir, rename=filename)
        torrent = self.getTorrent(filename)
        torrent_hash = torrent.hash
        torrent_name = torrent.name
        save_path = torrent.save_path
        self.client.torrents_pause(torrent_hash)
        sleep(2)
        files = os.listdir(save_path)
        torrent_partial_name = fr"\[SubsPlease\] {anime_name} - {episode} (1080p)*"
        file = [file for file in files if re.match(torrent_partial_name, file)][0]
        # for file in files:
        #     print(file, torrent_partial_name, re.match(torrent_partial_name, file))
        # sys.exit(1)
        # print(file)
        # os.rename(os.path.join(save_path, file), os.path.join(save_path, filename))
        print(torrent_hash, save_path)
        sleep(2)
        # self.client.torrents_set_location(location=save_path, torrent_hashes=torrent_hash)
        # self.client.torrents_set_save_path(save_path=save_path, torrent_hashes=torrent_hash)
        # self.client.torrents_set_download_path(download_path=save_path, torrent_hashes=torrent_hash)
        print(save_path, filename)
        self.client.torrents_rename_file(old_path=os.path.join(save_path, torrent_name), new_path=".", new_file_name=torrent_name,  torrent_hash=torrent_hash)
        self.client.torrents_resume(torrent_hash)

    def getTorrent(self, filename: str):
        while True:
            torrents = self.client.torrents_info(filter="active")
            torrent = [torrent for torrent in torrents if torrent.name.startswith(filename)]
            if len(torrents) > 1:
                return f"ERROR: Multiple torrents found for filename: {filename}"
            elif len(torrents) == 0:
                continue
            return torrent[0]