import fnmatch
import sys
import time
import requests
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

def formatError(errorMsg):
    return str(errorMsg).replace("'","''")

def setDriver():
    options = Options()
    options.add_argument("--headless")
    return webdriver.Chrome(service=Service(
        ChromeDriverManager().install())
        # , options=options
    )

def mainFunc():
    logger = Logger().log()
    conn, cursor = None, None

    # Config File
    config = configparser.ConfigParser()
    config.read("../config/config.ini")
    # Database Config
    databaseConfig = config["Database"]
    sqlServerName = databaseConfig["serverName"]
    database = databaseConfig["database"]
    # Driver Config
    driverConfig = config["Driver"]
    driverUrl = driverConfig["driverLiveChartUrl"]
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
        logger.info("DB Connection successful")
    except Exception as e:
        logger.error("Error Connecting to DB " + formatError(e))
        return [2, f"Db Exception occured: {formatError(e)}"]

    res = requests.get("")

    driver = setDriver()
    logger.debug("Driver Start")
    driver.get("https://nowsecure.nl/")

    # loginButton = driver.find_elements(By.XPATH, "//a[contains(text(), 'Log in')]")[1]
    # loginButton.click()

    # handle = driver.current_window_handle
    # driver.service.stop()
    # time.sleep(6)
    # driver = setDriver()
    # print(handle)
    # driver.switch_to.window(handle)

    time.sleep(5)

if __name__ == "__main__":
    mainFunc()