import os
from xdcc_dl.xdcc import download_packs
from xdcc_dl.entities import XDCCPack, IrcServer
import configparser
from scripts.common.databaseAccess import Database

# Config File
config = configparser.ConfigParser()
config.read("../config/config.ini")
# Root Dir
driverConfig = config["Driver"]
rootDir = driverConfig["parentDir"]
# Database Config
databaseConfig = config["Database"]
sqlServerName = databaseConfig["serverName"]
database = databaseConfig["database"]

def searchForEpisodeNumberErrors(directory):
    dirsToIgnore = ["100 man no Inochi no Ue ni Ore wa Tatte Iru", "Bleach", "Boku no Hero Academia", "Eighty Six", "Honzuki no Gekokujou", "Kimetsu no Yaiba", "Kyokou Suiri", "Mushoku Tensei", "One Piece", "Shingeki no Kyojin", "Spy x Family"
                    , "Tensei shitara Slime Datta Ken"]
    for subdir, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".mkv"):
                try:
                    dirEpisode = filename.split("[")[1].split("]")[0]
                    webEpisode = filename.split("- s")[1].split("e")[1].split(" ")[0]
                except:
                    print("AAAA", filename)
                if dirEpisode != webEpisode:
                    print(filename)

def renameFiles(directory, season, animeName, rename=False):
    for subdir, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".mkv"):
                # episode = filename.split('S01E')[1].split('.')[0]
                episode = filename.split('- E')[1].split(' ')[0]
                # episode = filename.split('- ')[1].split(' ')[0]
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

def updateNotificationsView():
    databaseClass = Database(sqlServerName, database)
    conn, cursor = databaseClass.dbConnect()
    tablesSql = """
        select it.table_name
        from INFORMATION_SCHEMA.TABLES as it
        inner join sys.tables as t on t.name = it.TABLE_NAME
        where
        it.TABLE_NAME in (select replace(dir_name,' ','_') from anime_to_download where download = 1)
    """
    cursor.execute(tablesSql)
    tablesList = cursor.fetchall()

    for row in tablesList:
        tableName = row[0]
        animeName = tableName.replace("_", " ")
        updateNotificationsSql = f"""
            update [{tableName}]
            set notification_sent = 1
            where notification_sent = 0
        """
        cursor.execute(updateNotificationsSql)
        cursor.commit()
    conn.commit()
    conn.close()

# renameFiles(r"F:\Anime\Great Teacher Onizuka\Season 1", "1", "Great Teacher Onizuka", True)

updateNotificationsView()

# searchForEpisodeNumberErrors(rootDir)