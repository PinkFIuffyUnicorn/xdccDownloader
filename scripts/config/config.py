import configparser
import os
from scripts.common.customLogger import Logger
import logging

main_dir = os.path.abspath(os.path.dirname(__file__))
config_path = os.path.join(main_dir, 'config.ini')
# Config File
config = configparser.ConfigParser()
config.read(config_path)
# Plex Config
plexCredentials = config["PlexCredentials"]
username = plexCredentials["username"]
password = plexCredentials["password"]
plexServerName = plexCredentials["plexServerName"]
# Database Config
databaseConfig = config["Database"]
sqlServerName = databaseConfig["sqlServerName"]
database = databaseConfig["database"]
# Driver Config
driverConfig = config["Driver"]
driverNiblUrl = driverConfig["driverNiblUrl"]
parentDir = driverConfig["parentDir"]
# Discord Bot
discordBotConfig = config["DiscordBot"]
tokenIgor = discordBotConfig["tokenIgor"]
tokenSana = discordBotConfig["tokenSana"]
# SubsPlease
subsPleaseConfig = config["SubsPleaseRSSFeed"]
url1080 = subsPleaseConfig["url1080"]
# Logger
# logger = Logger(logging.INFO).log()
logger = Logger(logging.DEBUG).log()
