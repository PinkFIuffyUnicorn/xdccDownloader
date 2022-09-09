import os
from xdcc_dl.xdcc import download_packs
from xdcc_dl.entities import XDCCPack, IrcServer

def searchForEpisodeNumberErrors(directory):
    for subdir, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".mkv"):
                dirEpisode = filename.split("[")[1].split("]")[0]
                webEpisode = filename.split("-")[1].split("e")[1].split(" ")[0]
                if dirEpisode != webEpisode:
                    print(filename)

def renameFiles(directory, season, animeName, rename=False):
    for subdir, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".mkv"):
                episode = filename.split('- ')[1].split(' ')[0]
                season = f"0{season}" if len(season) == 1 else season
                oldPath = os.path.join(directory, filename)
                newPath = os.path.join(directory, f"{animeName} - s{season}e{episode} (1080p) [{episode}].mkv")
                print(oldPath)
                print(newPath)
                if rename:
                    os.rename(oldPath, newPath)

def xdccDownload(server, botName, xdccPack):
    # irc.rizon.net
    # /msg Ginpachi-Sensei xdcc send #3150
    packSearch = XDCCPack(IrcServer(server), botName, xdccPack)
    download_packs([packSearch])