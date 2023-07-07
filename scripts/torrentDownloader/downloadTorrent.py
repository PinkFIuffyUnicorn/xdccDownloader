from lxml import etree
import requests
import sys
from datetime import datetime
from scripts.common.databaseAccess import Database
from scripts.common.customLogger import Logger
from scripts.common.qBitTorrent import QBitTorrent
from scripts.config import config
import logging

def formatError(errorMsg):
    return str(errorMsg).replace("'","''")

def currentTimestamp(type="print"):
    if type.lower() == "file":
        return datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
    elif type.lower() == "db":
        return datetime.now().strftime("%d_%m_%Y")
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S")

# Logger
logger = Logger(logging.INFO).log()
# Database Config
sqlServerName = config.sqlServerName
database = config.database
# Plex Config
username = config.username
password = config.password
plexServerName = config.plexServerName
# SubsPlease RSS Feed
subsplease_url = config.url1080
# Other Variables
parentDir = config.parentDir
dbBackupPath = rf"C:\Users\Aleš\Desktop\GitHub\xdccDownloader\DB Backups\animeBKP_{currentTimestamp('db')}.bak"

def getDbConnAndCursor(sqlServerNameFunc, databaseFunc):
    try:
        databaseClass = Database(sqlServerNameFunc, databaseFunc)
        logger.info("DB Connection successful")
        return databaseClass.dbConnect()
    except Exception as e:
        logger.error("Error Connecting to DB " + formatError(e))
        return [2, f"Db Exception occured: {formatError(e)}"]

def getDiscordGuildChannelLocations():
    conn, cursor = getDbConnAndCursor(sqlServerName, database)
    cursor.execute("""
        select channel_id from discord_guild_channel_locations where type = 'updateAnimeNotifications'
    """)

    return cursor.fetchall()

def getAnimeListFromDbTorrent(downloadAnimeName=None, downloadCurrentDay=False):
    animeList = []
    # Database Connection And Cursor
    conn, cursor = getDbConnAndCursor(sqlServerName, database)
    if conn == 2:
        sys.exit(cursor)
    downloadAnimeName = f" and name = '{downloadAnimeName}'" if downloadAnimeName != None and downloadAnimeName != "" else " "
    currentDayDownload = f" and download_day = {datetime.now().weekday() + 1}" if downloadCurrentDay == True else " "
    sql = f"""
                select
                     id as '0'
                    , name as '1'
                    , episode as '2'
                    , quality as '3'
                    , done as '4'
                    , last_change_date as '5'
                    , current_season as '6'
                    , dir_name as '7'
                    , english_name as '8'
                    , live_chart_image_url as '9'
                    , torrent_provider as '10'
                from
                    anime_to_download
                where 1 = 1
                and download = 1
                and done = 0
                {downloadAnimeName}
                {currentDayDownload}
                 order by name
            """
    cursor.execute(sql)
    downloadList = cursor.fetchall()

    logger.info(f""
                f"3")

    subsplease_query_list = [f"([{x[10]}] {x[1]})" for x in downloadList]
    subsplease_query_string = u"|".join((subsplease_query_list)) + " 1080p"
    # print(f"https://nyaa.si/?page=rss&q={subsplease_query_string}&c=0_0&f=0")

    # https://nyaa.si/?page=rss&q={QUERY}&c=0_0&f=0
    # https://nyaa.si/?page=rss&q=([SubsPlease]) | ([Anime Time] Tengoku) 1080p&c=0_0&f=0

    # r = requests.get(url=subsplease_url)
    # print(subsplease_query_string)
    r = requests.get(url=f"https://nyaa.si/?page=rss&q={subsplease_query_string}&c=0_0&f=0", timeout=300)
    subsplease_content = r.content
    root = etree.fromstring(subsplease_content)

    for row in downloadList:
        id = int(row[0])
        name = row[1]
        episode = int(row[2])
        # episode = "0" + str(episode) if len(str(episode)) == 1 else episode
        quality = row[3]
        done = row[4]
        last_change_date = row[5]
        current_season = int(row[6])
        dir_name = row[7]
        english_name = row[8]
        live_chart_image_url = row[9]
        torrent_provider = row[10]

        logger.debug(f"Anime was updated {(datetime.now() - last_change_date).days} days ago")
        if (datetime.now() - last_change_date).days > 30:
            cursor.execute(f"""
                                    update anime_to_download
                                    set done = 1, download = 0
                                    where id = {id}
                    """)
            logger.info(f"Updated Anime ({name}) to done")
            continue

        while True:
            searchTerm = f"{name} - {'0' + str(episode) if len(str(episode)) == 1 else episode}"
            if name == "Summer Time Rendering":
                searchTerm = f"{name} S01E{'0' + str(episode) if len(str(episode)) == 1 else episode}"
            # print(searchTerm)
            items = root.xpath(f".//item/title[contains(text(), '{searchTerm}')]")
            items = [item.getparent() for item in items]
            for index, item in enumerate(items):
                torrent_link = item[1].text
                # animeList.append(["", "", dir_name, episode, current_season, live_chart_image_url, torrent_link])
                animeList.append([dir_name, episode, current_season, live_chart_image_url, torrent_link, english_name])

                cursor.execute(
                    f"select count(*) from information_schema.tables where table_name = '{dir_name.replace(' ', '_')}'"
                )
                checkTableExists = cursor.fetchall()[0][0]
                if checkTableExists == 0:
                    cursor.execute(f"""
                        create table [{dir_name.replace(' ', '_')}] (
                            id int IDENTITY(1,1) PRIMARY KEY
                            , xdcc varchar(100)
                            , season int
                            , episode int
                            , downloaded bit default 0
                            , error varchar(8000)
                            , is_error bit default 0
                            , notification_sent bit default 0
                        )
                    """)
                    logger.debug(f"Added new Anime table ({dir_name.replace(' ', '_')})")

                cursor.execute(
                    f"select count(*) from [{dir_name.replace(' ', '_')}] where episode = {episode} and season = {current_season}"
                )
                checkEpisodeExists = cursor.fetchall()[0][0]
                if checkEpisodeExists == 0:
                    cursor.execute(
                        f"insert into [{dir_name.replace(' ', '_')}] (episode, xdcc, season) values ({episode},'{torrent_link}',{current_season})"
                    )
                    logger.debug(f"Inserted new episode into Anime table ({dir_name.replace(' ', '_')})")
                episode += 1

                if len(items) == index + 1:
                    cursor.execute(f"""
                        update anime_to_download
                        set episode = {episode}
                        where id = {id}
                    """)
                    logger.debug(f"Updated Anime ({name}) episode")

                break
            else:
                break

    cursor.commit()
    conn.commit()
    conn.close()

    return animeList

def downloadAnimeFromListTorrent(anime_list_to_download):
    conn, cursor = getDbConnAndCursor(sqlServerName, database)
    if conn == 2:
        sys.exit(cursor)

    qbt_client = QBitTorrent("localhost", 8080)

    for anime in anime_list_to_download:
        qbt_client.addTorent(anime)

def temp():
    anime_name = "Skip to Loafer"
    season = 1
    episode = 4
    fileName = f"{anime_name} - s{season}e{episode} (1080p) [{episode}].mkv"
    fileName2 = f"[SubsPlease] {anime_name} - 0{episode} (1080p)"
    torrent_link = "https://nyaa.si/view/1664868/torrent"
    anime_name_dir = f"C:\{anime_name}"
    anime_season_dir = f"{anime_name_dir}\Season {season}"
    qbt_client = QBitTorrent("localhost", 8080)
    qbt_client.addTorent(torrent_link, anime_season_dir, [anime_name, episode, season])

def temp2():
    anime_name = "Skip to Loafer"
    season = 1
    episode = "04"
    fileName = f"[SubsPlease] {anime_name} - {episode} (1080p)"
    qbt_client = QBitTorrent("localhost", 8080)
    qbt_client.getTorrents(fileName)

if __name__ == "__main__":
    # getAnimeListToDownload = getAnimeListFromDbTorrent()
    # information_text = "" if len(getAnimeListToDownload) == 0 else " check the notifications channel for more information"
    # requests.post(url=f"https://discordapp.com/api/v6/channels/{channel_id}/messages",
    #               json={"content": f"Found {len(getAnimeListToDownload)} Anime to download{information_text}."},
    #               headers=discord_bot_headers)
    # if information_text != "":
    #     anime_list = sendInitialEmbed(getAnimeListToDownload)
    #     downloadAnimeFromListTorrent(getAnimeListToDownload)
    temp()
    # torrent_hash = "3dae6b2489c8db8cca32966f18187345bc4106cd"