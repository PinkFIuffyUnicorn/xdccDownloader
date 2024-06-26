import fnmatch
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from datetime import datetime
from xdcc_dl.xdcc import download_packs
from xdcc_dl.entities import XDCCPack, IrcServer
import os
from scripts.common.databaseAccess import Database
from scripts.common.plexLibrary import PlexLibrary
from scripts.common.customLogger import Logger
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
# Driver Config
driverNiblUrl = config.driverNiblUrl
parentDir = config.parentDir
# Plex Config
username = config.plexUsername
password = config.plexPassword
plexServerName = config.plexServerName
# Other Variables
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

def getAnimeListFromDb(printOutput=False, downloadAnimeName=None, downloadCurrentDay=False):
    botPackList = []
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
                from
                    anime_to_download
                where 1 = 1
                and download = 1
                {downloadAnimeName}
                {currentDayDownload}
                 order by name
            """
    cursor.execute(sql)
    downloadList = cursor.fetchall()

    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(
        ChromeDriverManager().install())
        , options=options
    )
    logger.debug("Driver Start")
    driver.get(driverNiblUrl)

    for row in downloadList:
        id = int(row[0])
        name = row[1]
        episode = int(row[2])
        quality = row[3]
        done = row[4]
        last_change_date = row[5]
        current_season = int(row[6])
        dir_name = row[7]
        english_name = row[8]
        live_chart_image_url = row[9]

        if not done:
            logger.debug(f"Anime was updated {(datetime.now() - last_change_date).days} days ago")
            if (datetime.now() - last_change_date).days > 30:
                cursor.execute(f"""
                                        update anime_to_download
                                        set done = 1, download = 0
                                        where id = {id}
                        """)
                logger.info(f"Updated Anime ({name}) to done")
                continue
            updateEpisode = False
            while True:
                if name == "Itai no wa Iya nano de Bougyoryoku ni Kyokufuri Shitai to Omoimasu Season 2":
                    searchTerm = "[Erai-raws] {0} - {1} [{2}p]".format(name, "0" + str(episode) if len(str(episode)) == 1 else episode, quality)  # Shiroi Suna no Aquatope - 05 1080p
                    # break
                else:
                    searchTerm = "[SubsPlease] {0} - {1} ({2}p)".format(name, "0" + str(episode) if len(str(episode)) == 1 else episode, quality)  # Shiroi Suna no Aquatope - 05 (1080p)
                query = "query={0}".format(searchTerm)
                searchDriverUrl = "{0}{1}".format(driverNiblUrl, query)
                logger.debug(f"searchTerm: {searchTerm}")
                logger.debug(f"query: {query}")
                logger.debug(f"searchDriverUrl: {searchDriverUrl}")
                driver.get(searchDriverUrl)
                buttons = []
                if name == "placeholder":
                    # sys.exit(1)
                    pass
                else:
                    buttons = driver.find_elements(By.XPATH, f"//td[starts-with(text(),'{searchTerm}')]/../td/button[@data-botname='Ginpachi-Sensei']")
                    buttons = buttons if len(buttons) > 0 else driver.find_elements(By.XPATH, f"//td[starts-with(text(),'{searchTerm}')]/../td/button["
                                                                                    "@data-botname='CR-ARUTHA-IPv6|NEW' "
                                                                                    "or @data-botname='CR-HOLLAND-IPv6|NEW' "
                                                                                    "or @data-botname='CR-HOLLAND|NEW' "
                                                                                    "or @data-botname='CR-ARUTHA|NEW' "
                                                                                    # "or @data-botname='Fincayra' "
                                                                                    # "or @data-botname='[FFF]Arutha' "
                                                                                    # "or @data-botname='Ghouls|Arutha' "
                                                                                    "or @data-botname='ARUTHA-BATCH|1080p']"
                                                                                    )
                    buttons = buttons if len(buttons) > 0 else driver.find_elements(By.XPATH, f"//td[starts-with(text(),'{searchTerm.replace(f'{episode} ({quality}p)', f'{episode}v2 ({quality}p)')}')]/../td/button[@data-botname='ARUTHA-BATCH|1080p']")
                logger.debug(f"Buttons: {buttons}")
                if len(buttons) == 0:
                    break
                button = buttons[0]
                botName = button.get_attribute("data-botname")
                xdccPack = button.get_attribute("data-botpack")
                # xdcc = f"/msg {botName}|{quality}p xdcc send #{xdccPack}"
                xdcc = f"/msg {botName} xdcc send #{xdccPack}"

                botPackList.append([botName, xdccPack, dir_name, episode, current_season, live_chart_image_url, english_name])
                logger.debug(f"botName: {botName}")
                logger.debug(f"xdcc: {xdcc}")
                logger.debug(f"dir_name: {dir_name}")
                logger.debug(f"episode: {episode}")
                logger.debug(f"current_season: {current_season}")

                if printOutput:
                    print(f"""
                                        \rName: {name}
                                        \rEnglish Name: {english_name}
                                        \rDir Name: {dir_name}
                                        \rEpisode: {episode}
                                        \rXdcc: {xdcc}
                            """)
                logger.info(f"Name: {name}")
                logger.info(f"English Name: {english_name}")
                logger.info(f"Dir Name: {dir_name}")
                logger.info(f"Episode: {episode}")
                logger.info(f"Xdcc: {xdcc}")

                cursor.execute(
                    f"select count(*) from information_schema.tables where table_name = '{dir_name.replace(' ', '_')}'")
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
                    f"select count(*) from [{dir_name.replace(' ', '_')}] where episode = {episode} and season = {current_season}")
                checkEpisodeExists = cursor.fetchall()[0][0]
                if checkEpisodeExists == 0:
                    cursor.execute(
                        f"insert into [{dir_name.replace(' ', '_')}] (episode, xdcc, season) values ({episode},'{xdcc}',{current_season})")
                    logger.debug(f"Inserted new episode into Anime table ({dir_name.replace(' ', '_')})")

                episode += 1
                updateEpisode = True

            if updateEpisode:
                cursor.execute(f"""
                                        update anime_to_download
                                        set episode = {episode}
                                        where id = {id}
                        """)
                logger.debug(f"Updated Anime ({name}) episode")

                cursor.commit()

    conn.commit()
    conn.close()
    driver.quit()
    logger.debug("Driver Quit")

    return botPackList

def downloadAnimeFromList(animeListToDownload, printOutput=False, testing=False):
    conn, cursor = getDbConnAndCursor(sqlServerName, database)
    if conn == 2:
        sys.exit(cursor)
    downloadCounter = 0
    for x in animeListToDownload:
        downloadCounter += 1
        botName = x[0]
        xdccPack = x[1]
        animeName = x[2]
        episode = "0" + str(x[3]) if len(str(x[3])) == 1 else x[3]
        current_season = "0" + str(x[4]) if len(str(x[4])) == 1 else x[4]
        live_chart_image_url = x[5]
        english_name = x[6]
        discord_urls = x[7]

        anime_details_dict = {
            "anime_name": animeName,
            "episode": episode,
            "current_season": current_season,
            "live_chart_image_url": live_chart_image_url,
            "channel_ids": getDiscordGuildChannelLocations(),
            "english_name": english_name,
            "discord_urls": discord_urls
        }

        # print(anime_details_dict, botName, xdccPack)

        packSearch = XDCCPack(IrcServer("irc.rizon.net"), botName, xdccPack, anime_details_dict)
        # animeNameDir = f"{parentDir}\Temp\{animeName}"
        # animeNameDir = f"{parentDir}\{animeName}"
        animeNameDir = f"{parentDir}\Temp\{animeName}" if testing else f"{parentDir}\{animeName}"
        animeSeasonDir = f"{animeNameDir}\Season {x[4]}"

        dirExists = os.path.isdir(animeSeasonDir)
        if not dirExists:
            seasonEpisode = "01"
            dirExists2 = os.path.isdir(animeNameDir)
            if not dirExists2:
                os.mkdir(animeNameDir)
            os.mkdir(animeSeasonDir)
        else:
            seasonEpisode = len([x for x in fnmatch.filter(os.listdir(animeSeasonDir), "*.mkv") if "e00" not in x]) + 1
            seasonEpisode = "0" + str(seasonEpisode) if len(str(seasonEpisode)) == 1 else seasonEpisode

        fileName = f"{animeName} - s{current_season}e{seasonEpisode} (1080p) [{episode}].mkv"

        try:
            if printOutput:
                print(f"{currentTimestamp()} | Started File Download")
                print(f"Downloading: {fileName} | {downloadCounter}/{len(animeListToDownload)}")
            logger.info("Started File Download")
            logger.info(f"Downloading: {fileName} | {downloadCounter}/{len(animeListToDownload)}")
            packSearch.set_filename(fileName)
            packSearch.set_directory(animeSeasonDir)
            download_packs([packSearch])
            logger.debug("Download Successful")
            cursor.execute(
                f"update [{animeName.replace(' ', '_')}] set downloaded = 1, error = null, is_error = 0 where episode = {episode} and season = {x[4]}")
            cursor.commit()
        except Exception as e:
            if printOutput:
                print(f"{currentTimestamp()} | Error Downloading File: {formatError(e)}")
            logger.error(f"Error Downloading File: {formatError(e)}")
            cursor.execute(
                f"update [{animeName.replace(' ', '_')}] set downloaded = 0, is_error = 1, error = '{formatError(e)}' where episode = {episode} and season = {x[4]}")
            cursor.commit()
            continue

    if animeListToDownload != []:
        if printOutput:
            print(f"{currentTimestamp()} | Updating Plex Library")
        logger.info("Updating Plex Library")
        try:
            myPlexLibrary = PlexLibrary(username, password, plexServerName, "Anime")
            myPlexLibrary.updatePlexLibraryData()
        except Exception as e:
            logger.error(f"Error Updating Plex Library: {formatError(e)}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    """ ALL """
    # mainFunc(printOutput=True)
    """ ONLY ONE """
    # mainFunc(printOutput=True, downloadAnimeName="Tensei Oujo to Tensai Reijou no Mahou Kakumei")
    """ ONLY TODAY """
    # mainFunc(printOutput=True, downloadCurrentDay=True)
    getListToDownload = getAnimeListFromDb(printOutput=True, downloadCurrentDay=True)
    # getListToDownload = getAnimeListFromDb(printOutput=True, downloadAnimeName="REVENGER")
    downloadAnimeFromList(getListToDownload, printOutput=True)