import pyodbc
from xdcc_dl.xdcc import download_packs
from xdcc_dl.entities import XDCCPack, IrcServer
import os
import configparser

sqlServerName = "DESKTOP-V6UNK5R"
database = "master"
# Config File
config = configparser.ConfigParser()
config.read("config.ini")
# Driver Config
driverConfig = config["Driver"]
parentDir = driverConfig["parentDir"]

conn = pyodbc.connect('Driver={SQL Server};'
                      'Server='+sqlServerName+';'
                      'Database='+database+';'
                      'Trusted_Connection=yes;')
cursor = conn.cursor()

cursor.execute(
    "createXdccView"
)

viewList = cursor.fetchall()

for row in viewList:
    id = row[0]
    xdcc = row[1]
    xdccPack = xdcc.rsplit("#", 1)[1]
    #season = row[2]
    season = "0" + str(row[2]) if len(str(row[2])) == 1 else row[2]
    #episode = row[3]
    episode = "0" + str(row[3]) if len(str(row[3])) == 1 else row[3]
    downloaded = row[4]
    is_error = row[5]
    error = row[6]
    tableName = row[7]
    botName = xdcc.split(" ")[1]
    animeName = tableName.replace("_", " ")
    print(f"""
        \rAnime: {tableName}
        \rSeason: {season}
        \rEpisode = {episode}
        \rXdcc: {xdcc}
    """)

    # decision = input(f"Would you like to retry download for xdcc {tableName} - s{season}e{episode}?")
    decision = "y"

    if decision.lower() in ("y","yes","d"):
        animeNameDir = f"{parentDir}\{animeName}"
        animeSeasonDir = f"{animeNameDir}\Season {row[2]}"
        dirExists = os.path.isdir(animeSeasonDir)
        if not dirExists:
            seasonEpisode = "01"
            dirExists2 = os.path.isdir(animeNameDir)
            if not dirExists2:
                os.mkdir(animeNameDir)
            os.mkdir(animeSeasonDir)
        else:
            seasonEpisode = len([f for f in os.listdir(animeSeasonDir)]) + 1
            seasonEpisode = "0" + str(seasonEpisode) if len(str(seasonEpisode)) == 1 else seasonEpisode

        fileName = f"{animeName} - s{season}e{seasonEpisode} (1080p) [{episode}].mkv"

        packSearch = XDCCPack(IrcServer("irc.rizon.net"), botName, xdccPack)
        packSearch.set_filename(fileName)
        packSearch.set_directory(animeSeasonDir)
        print(fileName, animeSeasonDir)
        print(botName, xdcc)
        download_packs([packSearch])
        print("A")

        cursor.execute(f"update {tableName} set downloaded = 1 where episode = {episode} and season = {season}")
        cursor.commit()
    elif decision.lower() in ("n","no"):
        print(f"Skipped download for {tableName} - {episode}")

cursor.commit()
conn.commit()
conn.close()