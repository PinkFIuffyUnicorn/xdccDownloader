import urllib
import re
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import os
from xdcc_dl.xdcc import download_packs
from xdcc_dl.entities import XDCCPack, IrcServer
import configparser
from scripts.common.databaseAccess import Database
from scripts.common.plexLibrary import PlexLibrary

# Config File
config = configparser.ConfigParser()
config.read("../config/config.ini")
# Root Dir
driverConfig = config["Driver"]
rootDir = driverConfig["parentDir"]
# Database Config
databaseConfig = config["Database"]
sqlServerName = databaseConfig["sqlServerName"]
database = databaseConfig["database"]

def searchForEpisodeNumberErrors(directory):
    dirsToIgnore = ["100 man no Inochi no Ue ni Ore wa Tatte Iru", "Bleach", "Boku no Hero Academia", "Eighty Six", "Honzuki no Gekokujou", "Kimetsu no Yaiba", "Kyokou Suiri", "Mushoku Tensei", "One Piece", "Shingeki no Kyojin", "Spy x Family"
                    , "Tensei shitara Slime Datta Ken"]
    for subdir, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".mkv"):
                try:
                    dirEpisode = filename.split("[")[1].split("]")[0]
                    webEpisode = filename.split("- ")[1].split(" ")[0]
                except:
                    print("AAAA", filename)
                if dirEpisode != webEpisode:
                    new_filename = filename.replace(f"- {webEpisode}", f"- {dirEpisode}")
                    old_file_path = u"\\".join((subdir, filename))
                    new_file_path = u"\\".join((subdir, new_filename))
                    print(old_file_path, " | ", new_file_path)
                    os.rename(old_file_path, new_file_path)

def renameFiles(directory, rename=False, print_errors=False):
    pattern = r"s\d+e\d+"
    errorList = []
    for subdir, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".mkv"):
                matches = re.findall(pattern, filename)
                if matches:
                    anime_name = filename.split(" - s")[0]
                    end_file_name = filename.split("- s")[1].split(" ", 1)[1]
                    season = filename.split("- s")[1].split("e")[0]
                    episode = filename.split("- s")[1].split(" ")[0].split("e")[1]
                    new_filename = f"{anime_name} - {episode} {end_file_name}"
                    old_file_path = u"\\".join((subdir, filename))
                    new_file_path = u"\\".join((subdir, new_filename))
                    print(old_file_path, " | ", new_file_path)
                    # if os.path.isfile(old_file_path) and rename:
                    #     os.rename(old_file_path, new_file_path)
                    # print(filename, " | ", new_filename)
                    # if rename:
                    #     os.rename()
                else:
                    errorList.append(filename)
    if print_errors:
        print("************************************* ERRORS *************************************")
        errorString = u"\n".join((errorList))
        print(errorString)
        print("************************************* ERRORS *************************************")


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

def update_live_chart_image_urls():
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(
        ChromeDriverManager().install())
        , options=options
    )
    database_class = Database(sqlServerName, database)
    conn, cursor = database_class.dbConnect()
    live_chart_sql = """
            select id, live_chart_url
            from anime_to_download
            where
                live_chart_url is not null
            order by name
        """
    cursor.execute(live_chart_sql)
    live_chart_list = cursor.fetchall()

    for row in live_chart_list:
        id = row[0]
        live_chart_url = row[1]
        driver.get(live_chart_url)
        sleep(2)
        image = driver.find_elements(By.XPATH, "//div[@class='anime-poster']/img")
        try:
            # image_url = image[0].get_attribute("src")
            image_url = image[0].get_attribute("srcset").split(",")[1].strip().split(" ")[0]
            update_image_url_sql = f"""
                update anime_to_download
                set live_chart_image_url = '{image_url}'
                where id = {id} 
            """
            cursor.execute(update_image_url_sql)
            cursor.commit()
        except Exception as e:
            print(id, image, e)
            break
    conn.commit()
    conn.close()
    driver.quit()

def is_int(value):
    return bool(re.match(r'^-?\d+$', str(value)))

def get_missing_episodes(directory):
    episodes_dict = {}
    pattern = r"\[(\d+(?:\.\d+)?)\]\.mkv$"
    dirsToIgnore = ["100 man no Inochi no Ue ni Ore wa tatte iru", "Bleach", "Boku no Hero Academia", "Eighty Six",
                    "Honzuki no Gekokujou", "Kimetsu no Yaiba", "Kyokou Suiri", "Mushoku Tensei", "One Piece",
                    "Shingeki no Kyojin", "Spy x Family", "Bungo Stray Dogs", "Pokemon", "Temp"
                    , "Tensei shitara Slime Datta Ken", "Arifureta Shokugyou de Sekai Saikyou"]
    unexpected_errors_list = []
    for subdir, dirs, files in os.walk(directory):
        if len([x for x in dirsToIgnore if x in subdir]):
            continue
        anime_name_season = None
        files = [file for file in files if file.endswith(".mkv")]
        # print(subdir, dirs, files)
        if len(dirs) == 0 and len(files) > 0:
            sub_dir_split = subdir.split("\\")
            sub_dir_split.pop(0)
            sub_dir_split.pop(0)
            anime_name_season = u"\\".join((sub_dir_split))
        temp_list = []
        for filename in files:
            match = re.search(pattern, filename)
            try:
                number = match.group(1)
                number = int(number) if is_int(number) else float(number)
            except:
                unexpected_errors_list.append([anime_name_season, filename])
            temp_list.append(number)
        if anime_name_season != None:
            episodes_dict[anime_name_season] = temp_list

    for key, value_list in episodes_dict.items():
        errors_list = [value for index, value in enumerate(value_list) if (index == 0 and value not in (0, 1)) or (index > 0 and value != value_list[index-1]+1)]
        if len(errors_list) > 0:
            print(key, errors_list)
    print(unexpected_errors_list)

def find_missing_images(directory):
    databaseClass = Database(sqlServerName, database)
    conn, cursor = databaseClass.dbConnect()
    for subdir, dirs, files in os.walk(directory):
        subdir_split = subdir.split("\\")
        if len(subdir_split) == 2:
            continue
        elif len(subdir_split) > 2:
            anime_name = subdir_split[2]
            image_name = "poster.jpg"
            season = ""
            if len(subdir_split) == 4:
                season = subdir_split[3]
                if season == "Specials":
                    continue
                image_name = f"{season.replace(' ', '').lower()}.jpg"
            if image_name not in files:
                current_season = "1"
                if season != "":
                    current_season = season.split(' ')[1]
                sql = f"""
                    select live_chart_image_url
                    from anime_to_download
                    where dir_name = '{anime_name}' and current_season = '{current_season}'
                """
                cursor.execute(sql)
                image_url = cursor.fetchone()
                # print(anime_name, image_name, subdir, len(cursor.fetchall()), season)
                if image_url is not None:
                    image_url = image_url[0]
                    if image_url is not None:
                        # print(anime_name, season, image_url)
                        # if subdir.startswith("A:\Anime\Alice Gear Aegis Expansion"):
                        print(subdir, season, image_url, image_name)
                        urllib.request.urlretrieve(image_url, fr"{subdir}\{image_name}")

        # print(current_dir, dirs, files)
        # if "Season" in current_dir:
        #     image_name = f"{current_dir.replace(' ', '').lower()}.jpg"
        #     # print(current_dir, image_name in files)

def find_missing_images(directory):
    for subdir, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".jpg"):
                file_path = u"\\".join((subdir, file))
                print(file_path)
                # os.remove(file_path)

def getAllServerAnime(directory):
    anime_list = []
    for subdir, dirs, files in os.walk(directory):
        subdir_split = subdir.split("\\")
        # print(subdir_split)
        if len(subdir_split) != 3:
            continue
        anime_list.append(subdir_split[2])
    return anime_list

def getMissingAnimeInDb(directory):
    databaseClass = Database(sqlServerName, database)
    conn, cursor = databaseClass.dbConnect()

    anime_list = getAllServerAnime(directory)
    for anime in anime_list:
        sql = f"""
                select count(*)
                from anime_to_download
                where
                    dir_name = '{anime}'
                and id = (select max(atd.id) from anime_to_download atd where atd.dir_name = anime_to_download.dir_name)
            """
        cursor.execute(sql)
        counter = cursor.fetchall()[0][0]
        if counter == 0:
            print(anime, counter)

    cursor.commit()
    conn.commit()
    conn.close()

# renameFiles(directory, old_format, new_format, rename=False, print_errors=False):
# renameFiles("A:\Anime\Summertime Render", False, True)
# updateNotificationsView()
searchForEpisodeNumberErrors("A:\Anime\Shiguang Dailiren")
# update_live_chart_image_urls()
# get_missing_episodes(rootDir + "\Kami-tachi ni Hirowareta Otoko")
# get_missing_episodes(rootDir)
# find_missing_images(rootDir)
# find_missing_images("A:\Anime")
# print(getAllServerAnime("A:\Anime"))
# getMissingAnimeInDb("A:\Anime")