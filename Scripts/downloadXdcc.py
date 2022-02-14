from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pyperclip as pc
import pyodbc
from datetime import datetime
from xdcc_dl.xdcc import download_packs
from xdcc_dl.entities import XDCCPack, IrcServer
import os
from pathlib import Path

sqlServerName = "DESKTOP-V6UNK5R"
database = "master"
driverUrl = "https://nibl.co.uk/search?"
botPackList = []
parentDir = "F:\Anime"

currentDatetime = datetime.now()
formattedCurrentDatetime = currentDatetime.strftime("%d-%m-%Y %H:%M:%S")

conn = pyodbc.connect('Driver={SQL Server};'
                      'Server='+sqlServerName+';'
                      'Database='+database+';'
                      'Trusted_Connection=yes;')
cursor = conn.cursor()

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
    # " and name = 'One Piece'"
    # " where id = 54"
    # " where id in (71,72)"
    " order by name"
)
downloadList = cursor.fetchall()

chromeDriverPath = r"../Chrome Drivers/chromedriver_98"
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
            cursor.execute("""
                            update anime_to_download
                            set done = 1, download = 0
                            where id = {0}
            """.format(id))
            continue
        loopCounter = 0
        while True:
            #if name == "One Piece" and episode == 983:
                #break
            searchTerm = "{0} - {1} {2}p".format(name, "0" + str(episode) if len(str(episode)) == 1 else episode, quality) # Shiroi Suna no Aquatope - 05 1080p
            query = "query={0}".format(searchTerm)
            searchDriverUrl = "{0}{1}".format(driverUrl, query)
            driver.get(searchDriverUrl)
            # if name == "Boku no Hero Academia" and episode < 14:
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
                    cursor.execute("""
                                    update anime_to_download
                                    set days_without_episode = {0} + 1
                                    where id = {1}
                    """.format(days_without_episode, id))
                else:
                    cursor.execute("""
                                    update anime_to_download
                                    set days_without_episode = 0
                                    where id = {0}
                    """.format(id))
                break
            button = buttons[0]
            #button.click()
            #xdcc = pc.paste()
            #xdccSplit = xdcc.split()
            #botName = xdccSplit[1]
            #xdccPack = xdccSplit[4].replace("#","")
            botName = button.get_attribute("data-botname")
            xdccPack = button.get_attribute("data-botpack")
            xdcc = f"/msg {botName}|{quality}p xdcc send #{xdccPack}"

            botPackList.append([botName, xdccPack, dir_name, episode, current_season])

            print(f"""
                        \rName: {name}
                        \rDir Name: {dir_name}
                        \rEpisode: {episode}
            """)

            cursor.execute("select count(*) from information_schema.tables where table_name = '{0}'".format(dir_name.replace(" ","_")))
            checkTableExists = cursor.fetchall()[0][0]
            if checkTableExists == 0:
                cursor.execute("""
                    create table [{0}] (
                        id int IDENTITY(1,1) PRIMARY KEY,
                        xdcc varchar(100),
                        season int,
                        episode int,
                        downloaded bit default 0
                    )
                """.format(dir_name.replace(" ","_")))

            cursor.execute("select count(*) from [{0}] where episode = {1} and season = {2}".format(dir_name.replace(" ","_"), episode, current_season))
            checkEpisodeExists = cursor.fetchall()[0][0]
            if checkEpisodeExists == 0:
                cursor.execute("insert into [{0}] (episode, xdcc, season) values ({1},'{2}',{3})".format(dir_name.replace(" ","_"), episode, xdcc, current_season))

            episode += 1
            loopCounter += 1

        cursor.execute("""
                        update anime_to_download
                        set episode = {0}
                        where id = {1}
        """.format(episode, id))

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
            packSearch.set_filename(fileName)
            packSearch.set_directory(animeSeasonDir)
            download_packs([packSearch])
            cursor.execute(f"update {animeName.replace(' ', '_')} set downloaded = 1 where episode = {episode} and season = {x[4]}")
            cursor.commit()
        except Exception as e:
            print(e)
            continue

conn.commit()
conn.close()