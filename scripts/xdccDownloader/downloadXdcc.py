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
import configparser
from scripts.common.databaseAccess import Database
from scripts.common.plexLibrary import PlexLibrary
from scripts.common.customLogger import Logger

def currentTimestamp(type="print"):
    if type.lower() == "file":
        return datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
    elif type.lower() == "db":
        return datetime.now().strftime("%d_%m_%Y")
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S")

def formatError(errorMsg):
    return str(errorMsg).replace("'","''")

# Other Variables
botPackList = []
dbBackupPath = rf"C:\Users\Aleš\Desktop\GitHub\xdccDownloader\DB Backups\animeBKP_{currentTimestamp('db')}.bak"
downloadFiles = True
logger = Logger().log()

print(f"{currentTimestamp()} | Script Started")
logger.info("Script Started")

# Config File
config = configparser.ConfigParser()
config.read("../config/config.ini")
# Database Config
databaseConfig = config["Database"]
sqlServerName = databaseConfig["serverName"]
database = databaseConfig["database"]
# Driver Config
driverConfig = config["Driver"]
driverUrl = driverConfig["driverUrl"]
parentDir = driverConfig["parentDir"]
# Plex Config
plexCredentials = config["PlexCredentials"]
username = plexCredentials["username"]
password = plexCredentials["password"]
serverName = plexCredentials["serverName"]
# Database Connection Variables
try:
    databaseClass = Database(sqlServerName, database)
    conn, cursor = databaseClass.dbConnect()
    print(f"{currentTimestamp()} | DB Connection successful")
    logger.info("DB Connection successful")
except Exception as e:
    print(f"{currentTimestamp()} | Error Connecting to DB " + str(e).replace("'", "''"))
    logger.error("Error Connecting to DB " + str(e).replace("'", "''"))
    sys.exit(1)

cursor.execute(
    "select"
    " id as '0'"
    ", name as '1'"
    ", episode as '2'"
    ", quality as '3'"
    ", done as '4'"
    ", days_without_episode as '5'"
    ", current_season as '6'"
    ", dir_name as '7'"
    ", english_name as '8'"
    " from anime_to_download"
    " where 1 = 1"
    " and download = 1"
    # " and id < 145"
    # " and id not in (52, 73)"
    # " and name <> 'Bungo Stray Dogs'"
    # " and name = 'Bleach'"
    # " and name = 'Jashin Chan Dropkick S2'"
    # " where id = 54"
    # " where id in (71,72)"
    " order by name"
)
downloadList = cursor.fetchall()

options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(service=Service(
    ChromeDriverManager().install())
    , options=options
)
logger.debug("Driver Start")
driver.get(driverUrl)

for row in downloadList:
    id = int(row[0])
    name = row[1]
    episode = int(row[2])
    quality = row[3]
    done = row[4]
    days_without_episode = int(row[5])
    current_season = int(row[6])
    dir_name = row[7]
    english_name = row[8]

    if not done:
        if days_without_episode > 30:
            cursor.execute(f"""
                            update anime_to_download
                            set done = 1, download = 0
                            where id = {id}
            """)
            logger.info(f"Updated Anime ({name}) to done")
            continue
        loopCounter = 0
        while True:
            if episode == 367 and name == "Bleach":
                break
            searchTerm = "{0} - {1} {2}p".format(name, "0" + str(episode) if len(str(episode)) == 1 else episode, quality) # Shiroi Suna no Aquatope - 05 1080p
            if name == "Bungo Stray Dogs":
                # searchTerm = "{0}p {1} - {2} [".format(quality, name, str(episode).zfill(3))  #  1080p Bleach - 001 [ (Bleach)
                if episode in (13, 26, 38):
                    current_season += 1
            query = "query={0}".format(searchTerm)
            searchDriverUrl = "{0}{1}".format(driverUrl, query)
            logger.debug(f"searchTerm: {searchTerm}")
            logger.debug(f"query: {query}")
            logger.debug(f"searchDriverUrl: {searchDriverUrl}")
            driver.get(searchDriverUrl)
            if name == "placeholder":
                # buttons = driver.find_elements(By.XPATH, f"//td[contains(text(),'{searchTerm.replace('1080p', '')}')]/../td/button")
                pass
            else:
                buttons = driver.find_elements(By.XPATH, "//button["
                                                         "@data-botname='Ginpachi-Sensei' "
                                                         # "and @data-botpack >= '16682' and @data-botpack <= '16693'"
                                                         "]"
                                               )
                buttons = buttons if len(buttons) > 0 else driver.find_elements(By.XPATH, "//button["
                                                                                          "@data-botname='CR-ARUTHA-IPv6|NEW' "
                                                                                          "or @data-botname='CR-HOLLAND-IPv6|NEW' "
                                                                                          "or @data-botname='CR-HOLLAND|NEW' "
                                                                                          "or @data-botname='CR-ARUTHA|NEW' "
                                                                                          "or @data-botname='Fincayra' "
                                                                                          "or @data-botname='ARUTHA-BATCH|1080p' "
                                                                                          "or @data-botname='[FFF]Arutha' "
                                                                                          "or @data-botname='Ghouls|Arutha']"
                                                                                )
            logger.debug(f"Buttons: {buttons}")
            if len(buttons) == 0:
                if loopCounter == 0:
                    cursor.execute(f"""
                                    update anime_to_download
                                    set days_without_episode = {days_without_episode} + 1
                                    where id = {id}
                    """)
                    logger.debug(f"Episode not found for {name}")
                else:
                    cursor.execute(f"""
                                    update anime_to_download
                                    set days_without_episode = 0
                                    where id = {id}
                    """)
                    logger.debug(f"Episode found for {name}")
                break
            button = buttons[0]
            botName = button.get_attribute("data-botname")
            xdccPack = button.get_attribute("data-botpack")
            #xdcc = f"/msg {botName}|{quality}p xdcc send #{xdccPack}"
            xdcc = f"/msg {botName} xdcc send #{xdccPack}"

            botPackList.append([botName, xdccPack, dir_name, episode, current_season])
            logger.debug(f"botName: {botName}")
            logger.debug(f"xdcc: {xdcc}")
            logger.debug(f"dir_name: {dir_name}")
            logger.debug(f"episode: {episode}")
            logger.debug(f"current_season: {current_season}")

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

            cursor.execute(f"select count(*) from information_schema.tables where table_name = '{dir_name.replace(' ','_')}'")
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
                # cursor.execute(
                #     "updateNotifications"
                # )
                # cursor.execute(
                #     "createXdccView"
                # )

            cursor.execute(f"select count(*) from [{dir_name.replace(' ','_')}] where episode = {episode} and season = {current_season}")
            checkEpisodeExists = cursor.fetchall()[0][0]
            if checkEpisodeExists == 0:
                cursor.execute(f"insert into [{dir_name.replace(' ','_')}] (episode, xdcc, season) values ({episode},'{xdcc}',{current_season})")
                logger.debug(f"Inserted new episode into Anime table ({dir_name.replace(' ','_')})")

            episode += 1
            loopCounter += 1

        cursor.execute(f"""
                        update anime_to_download
                        set episode = {episode}
                        where id = {id}
        """)
        logger.debug(f"Updated Anime ({name}) episode")

        cursor.commit()

driver.quit()
logger.debug("Driver Quit")
if downloadFiles:
    downloadCounter = 0
    for x in botPackList:
        downloadCounter+=1
        botName = x[0]
        xdccPack = x[1]
        animeName = x[2]
        episode = "0" + str(x[3]) if len(str(x[3])) == 1 else x[3]
        current_season = "0" + str(x[4]) if len(str(x[4])) == 1 else x[4]
        packSearch = XDCCPack(IrcServer("irc.rizon.net"), botName, xdccPack)
        animeNameDir = f"{parentDir}\{animeName}"
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
            print(f"{currentTimestamp()} | Started File Download")
            print(f"Downloading: {fileName} | {downloadCounter}/{len(botPackList)}")
            logger.info("Started File Download")
            logger.info(f"Downloading: {fileName} | {downloadCounter}/{len(botPackList)}")
            packSearch.set_filename(fileName)
            packSearch.set_directory(animeSeasonDir)
            download_packs([packSearch])
            logger.debug("Download Successful")
            cursor.execute(f"update [{animeName.replace(' ', '_')}] set downloaded = 1, error = null, is_error = 0 where episode = {episode} and season = {x[4]}")
            cursor.commit()
        except Exception as e:
            print(f"{currentTimestamp()} | Error Downloading File")
            logger.error("Error Downloading File")
            cursor.execute(f"update [{animeName.replace(' ', '_')}] set downloaded = 0, is_error = 1, error = '{formatError(e)}' where episode = {episode} and season = {x[4]}")
            cursor.commit()
            continue

    if botPackList != []:
        print(f"{currentTimestamp()} | Updating Plex Library")
        logger.info("Updating Plex Library")
        try:
            myPlexLibrary = PlexLibrary(username, password, serverName, "Anime")
            myPlexLibrary.updatePlexLibraryData()
        except Exception as e:
            logger.error(f"Error Updating Plex Library: {formatError(e)}")

logger.info("DB Backup Started")
databaseClass.dbBackup(conn, cursor, dbBackupPath)
logger.info("DB Backup Ended")

deletedFiles = databaseClass.deleteOldBackups()
for file in deletedFiles:
    logger.info(f"Deleted OLD backup file: {file}")

logger.info("Script Ended")
conn.commit()
conn.close()