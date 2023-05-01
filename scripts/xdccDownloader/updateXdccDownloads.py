import pyodbc
from xdcc_dl.xdcc import download_packs
from xdcc_dl.entities import XDCCPack, IrcServer
import os
import configparser
from scripts.common.databaseAccess import Database
from scripts.discordBot.extensions.commonFunctions import getDiscordGuildChannelLocations, sendInitialEmbed

# Config File
config = configparser.ConfigParser()
config.read("../config/config.ini")
# Database Config
databaseConfig = config["Database"]
sqlServerName = databaseConfig["sqlServerName"]
database = databaseConfig["database"]
# Driver Config
driverConfig = config["Driver"]
parentDir = driverConfig["parentDir"]

conn = pyodbc.connect('Driver={SQL Server};'
                      'Server='+sqlServerName+';'
                      'Database='+database+';'
                      'Trusted_Connection=yes;')
cursor = conn.cursor()

# cursor.execute(
#     # "createXdccView"
#     "select * from createXdccViewData"
# )

cursor.execute("""
    select it.table_name
    from INFORMATION_SCHEMA.TABLES as it
	inner join sys.tables as t on t.name = it.TABLE_NAME
	where
	it.TABLE_NAME in (select replace(dir_name,' ','_') from anime_to_download where download = 1)
""")
tablesList = cursor.fetchall()

for row in tablesList:
    tableName = row[0]

    cursor.execute(f"""
        select 
            *, (select top 1 live_chart_image_url from anime_to_download where dir_name = '{tableName.replace("_", " ")}' order by last_change_date desc)
        from [{tableName}]
        where
            downloaded = 0 and notification_sent = 0
    """)
    errorResult = cursor.fetchall()

    for row2 in errorResult:
        id = row2[0]
        xdcc = row2[1]
        # season = row2[2]
        # episode = row2[3]
        season = "0" + str(row2[2]) if len(str(row2[2])) == 1 else row2[2]
        # episode = row[3]
        episode = "0" + str(row2[3]) if len(str(row2[3])) == 1 else row2[3]
        image = row2[8]
        animeName = tableName.replace("_", " ")
        xdccPack = xdcc.rsplit("#", 1)[1]
        botName = xdcc.split(" ")[1]

        # decision = input(f"Would you like to retry download for xdcc {tableName} - s{season}e{episode}?")
        decision = "n"
        print(animeName, season, episode, xdcc)

        if decision.lower() in ("y","yes","d"):
            animeNameDir = f"{parentDir}\{animeName}"
            animeSeasonDir = f"{animeNameDir}\Season {row2[2]}"
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

            # ["", "", "name", "episode", "season", "image"]

            discord_urls = sendInitialEmbed([["", "", animeName, episode, season, image]])

            anime_details_dict = {
                "anime_name": animeName,
                "episode": episode,
                "current_season": season,
                "live_chart_image_url": image,
                "channel_ids": getDiscordGuildChannelLocations(),
                "discord_urls": discord_urls
            }

            packSearch = XDCCPack(IrcServer("irc.rizon.net"), botName, xdccPack, anime_details_dict)
            packSearch.set_filename(fileName)
            packSearch.set_directory(animeSeasonDir)
            # print(fileName, animeSeasonDir)
            # print(botName, xdcc)
            download_packs([packSearch])

            cursor.execute(f"update {tableName} set downloaded = 1, is_error = 0, error = null where episode = {episode} and season = {season}")
            cursor.commit()
        elif decision.lower() in ("n","no"):
            print(f"Skipped download for {tableName} - {episode}")

cursor.commit()
conn.commit()
conn.close()