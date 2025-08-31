import pathlib
import urllib
import re
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import os
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
        image = driver.find_elements(By.XPATH, "//img[@class='overflow-hidden rounded']")
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
    for subdir, dirs, files in os.walk(directory):
        subdir_split = subdir.split("\\")
        if len(subdir_split) == 2:
            continue
        missing_image = any(file.endswith(".jpg") for file in files)
        if not missing_image:
            # print(subdir_split[-1:], subdir_split, files)
            print(subdir, dirs, files)
            image_name = ""
            if not files:
                image_name = "poster.jpg"
            else:
                last_item = subdir_split[-1:][0]
                image_name = f'{last_item.replace(" ", "").lower()}.jpg'
                print(image_name)


def download_image_to_dir():
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(
        ChromeDriverManager().install())
        , options=options
    )
    database_class = Database(sqlServerName, database)
    conn, cursor = database_class.dbConnect()
    live_chart_sql = """
                select id, live_chart_image_url
                from anime_to_download
                where
                    live_chart_image_url is not null
                 and dropped = 0
                order by name
            """
    cursor.execute(live_chart_sql)
    live_chart_image_list = cursor.fetchall()

    for row in live_chart_image_list:
        id = row[0]
        image_url = row[1]



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

# def

# find_missing_images(rootDir)
get_missing_episodes("A:\Anime")


# reception.istrian.villas@plavalaguna.com
# tmno plava
# hellihansen (HH)