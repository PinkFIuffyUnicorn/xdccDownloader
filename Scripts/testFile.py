from plexapi.myplex import MyPlexAccount
import configparser

config = configparser.ConfigParser()
config.read("config.ini")

plexCredentials = config["PlexCredentials"]
username = plexCredentials["username"]
password = plexCredentials["password"]
serverName = plexCredentials["serverName"]
account = MyPlexAccount(username, password)
plex = account.resource(serverName).connect()
animeLibrary = plex.library.section("Anime")