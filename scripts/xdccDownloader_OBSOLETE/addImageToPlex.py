import os, shutil
from scripts.common.plexLibrary import PlexLibrary
import configparser

def addImagesToSeasons(directory, filesLocation):
    for subdir, dirs, files in os.walk(directory):
        for filenameJpg in files:
            fileName = filenameJpg.replace(".jpg","")
            name = fileName.split("_")[0]
            seasonName = fileName.split("_")[1]
            dirPath = u"\\".join((filesLocation, name, seasonName))
            dirExists = os.path.isdir(dirPath)
            # print(dirExists, fileName, dirPath)

            if dirExists:
                old_name = os.path.join(os.path.abspath(subdir), filenameJpg)
                base, extension = os.path.splitext(name)
                new_name = os.path.join(filesLocation, base, seasonName, seasonName.lower().replace(" ", "") + ".jpg")
                fileExists = os.path.isfile(new_name)
                # print(fileExists, old_name, new_name)
                if not fileExists:
                    print(old_name, new_name)
                    shutil.copy(old_name, new_name)

def addImagesToShows(directory):
    for subdir, dirs, files in os.walk(directory):
        if subdir != directory and dirs:
            latestSeasonId = max([x.split(" ")[1] for x in dirs])
            latestSeason = f"Season {latestSeasonId}"
            latestSeasonPoster = os.path.join(subdir, latestSeason, f"season{latestSeasonId}.jpg")
            latestSeasonPosterExists = os.path.isfile(latestSeasonPoster)
            if latestSeasonPosterExists:
                showPoster = os.path.join(subdir, "poster.jpg")
                # print(latestSeasonPoster, showPoster)
                shutil.copy(latestSeasonPoster, showPoster)

# Config File
config = configparser.ConfigParser()
config.read("../config/config.ini")
# Plex Config
plexCredentials = config["PlexCredentials"]
username = plexCredentials["username"]
password = plexCredentials["password"]
serverName = plexCredentials["serverName"]

directory = r"../Images/"
filesLocation = r"F:\Anime"
addImagesToSeasons(directory, filesLocation)

directory = r"F:\Anime"
addImagesToShows(directory)

myPlexLibrary = PlexLibrary(username, password, serverName, "Anime")
myPlexLibrary.updatePlexLibraryMetadate()