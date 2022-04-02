from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime
from xdcc_dl.xdcc import download_packs
from xdcc_dl.entities import XDCCPack, IrcServer
import os
import configparser
from Scripts.databaseAccess import Database
from Scripts.plexLibrary import PlexLibrary

def formatDate(date):
    return date.strftime("%d-%m-%Y %H:%M:%S")

def formatError():
    return "'" + str(e).replace("'","''") + "'"

# Other Variables
botPackList = []

print(f"{formatDate(datetime.now())} | Started")

# Config File
config = configparser.ConfigParser()
config.read("config.ini")
# Database Config
databaseConfig = config["Database"]
sqlServerName = databaseConfig["serverName"]
database = databaseConfig["database"]
# Driver Config
driverConfig = config["Driver"]
driverUrl = driverConfig["driverUrl"]
parentDir = driverConfig["parentDir"]
chromeDriverPath = driverConfig["chromeDriverPath"]
# Plex Config
plexCredentials = config["PlexCredentials"]
username = plexCredentials["username"]
password = plexCredentials["password"]
serverName = plexCredentials["serverName"]
# Database Connection Variables
try:
    databaseClass = Database(sqlServerName, database)
    conn, cursor = databaseClass.dbConnect()
except Exception as e:
    print(f"{formatDate(datetime.now())} | Error Connecting to DB " + str(e).replace("'","''"))

cursor.execute(
    "select "
    "id as '0'"
    ", name as '1'"
    ", episode as '2'"
    ", quality as '3'"
    ", done as '4'"
    ", days_without_episode as '5'"
    ", current_season as '6'"
    ", dir_name as '7'"
    " from anime_to_download"
    " where download = 1"
    # " and id not in (52, 73)"
    # " and name <> 'Boku no Hero Academia'"
    # " and name = 'Platinum End'"
    # " where id = 54"
    # " where id in (71,72)"
    " order by name"
)
downloadList = cursor.fetchall()

options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(
    executable_path=chromeDriverPath
    , options=options
)
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

    if not done:
        if days_without_episode > 30:
            cursor.execute(f"""
                            update anime_to_download
                            set done = 1, download = 0
                            where id = {id}
            """)
            continue
        loopCounter = 0
        while True:
            #if name == "One Piece" and episode == 983:
                #break
            searchTerm = "{0} - {1} {2}p".format(name, "0" + str(episode) if len(str(episode)) == 1 else episode, quality) # Shiroi Suna no Aquatope - 05 1080p
            query = "query={0}".format(searchTerm)
            searchDriverUrl = "{0}{1}".format(driverUrl, query)
            driver.get(searchDriverUrl)
            # if name == "Yuru Camp":
            #     buttons = driver.find_elements(By.XPATH, "//button[@data-botname='ARUTHA-BATCH|1080p']")
            if 1==2:
                break
            else:
                buttons = driver.find_elements(By.XPATH, "//button[@data-botname='Ginpachi-Sensei']")
                buttons = buttons if len(buttons) > 0 else driver.find_elements(By.XPATH, "//button["
                                                                                          "@data-botname='CR-HOLLAND-IPv6|NEW' or "
                                                                                          "@data-botname='CR-ARUTHA-IPv6|NEW' or "
                                                                                          "@data-botname='CR-HOLLAND|NEW' or "
                                                                                          "@data-botname='CR-ARUTHA|NEW' or"
                                                                                          "@data-botname='ARUTHA-BATCH|1080p']")
            if len(buttons) == 0:
                if loopCounter == 0:
                    cursor.execute(f"""
                                    update anime_to_download
                                    set days_without_episode = {days_without_episode} + 1
                                    where id = {id}
                    """)
                else:
                    cursor.execute(f"""
                                    update anime_to_download
                                    set days_without_episode = 0
                                    where id = {id}
                    """)
                break
            button = buttons[0]
            botName = button.get_attribute("data-botname")
            xdccPack = button.get_attribute("data-botpack")
            xdcc = f"/msg {botName}|{quality}p xdcc send #{xdccPack}"

            botPackList.append([botName, xdccPack, dir_name, episode, current_season])

            print(f"""
                        \rName: {name}
                        \rDir Name: {dir_name}
                        \rEpisode: {episode}
            """)

            cursor.execute(f"select count(*) from information_schema.tables where table_name = '{dir_name.replace(' ','_')}'")
            checkTableExists = cursor.fetchall()[0][0]
            if checkTableExists == 0:
                cursor.execute(f"""
                    create table [{dir_name.replace(' ','_')}] (
                        id int IDENTITY(1,1) PRIMARY KEY
                        , xdcc varchar(100)
                        , season int
                        , episode int
                        , downloaded bit default 0
                        , error varchar(8000)
                        , is_error bit default 0
                    )
                """)

            cursor.execute(f"select count(*) from [{dir_name.replace(' ','_')}] where episode = {episode} and season = {current_season}")
            checkEpisodeExists = cursor.fetchall()[0][0]
            if checkEpisodeExists == 0:
                cursor.execute(f"insert into [{dir_name.replace(' ','_')}] (episode, xdcc, season) values ({episode},'{xdcc}',{current_season})")

            episode += 1
            loopCounter += 1

        cursor.execute(f"""
                        update anime_to_download
                        set episode = {episode}
                        where id = {id}
        """)

        cursor.commit()

driver.quit()

if 1==1:
    for x in botPackList:
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
            seasonEpisode = len([f for f in os.listdir(animeSeasonDir)]) + 1
            seasonEpisode = "0" + str(seasonEpisode) if len(str(seasonEpisode)) == 1 else seasonEpisode

        fileName = f"{animeName} - s{current_season}e{seasonEpisode} (1080p) [{episode}].mkv"

        try:
            print(f"{formatDate(datetime.now())} | Started File Download")
            print(f"Downloading: {fileName}")
            packSearch.set_filename(fileName)
            packSearch.set_directory(animeSeasonDir)
            download_packs([packSearch])
            cursor.execute(f"update {animeName.replace(' ', '_')} set downloaded = 1 where episode = {episode} and season = {x[4]}")
            cursor.commit()

        except Exception as e:
            print(f"{formatDate(datetime.now())} | Error Downloading File")
            cursor.execute(f"update {animeName.replace(' ', '_')} set downloaded = 0, is_error = 1, error = " + "'" + formatError() + "'" + f" where episode = {episode} and season = {x[4]}")
            cursor.commit()
            continue

    if botPackList != []:
        print(f"{formatDate(datetime.now())} | Updating Plex Library")
        try:
            # updatePlexLibrary(username, password, serverName, "Anime")
            myPlexLibrary = PlexLibrary(username, password, serverName, "Anime")
            myPlexLibrary.updatePlexLibrary()
        except Exception as e:
            print(f"{formatDate(datetime.now())} | Error Updating Plex Library: " + formatError())

print(f"{formatDate(datetime.now())} | Ended")
conn.commit()
conn.close()