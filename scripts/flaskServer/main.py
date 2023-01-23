from flask import Flask
from scripts.common.plexLibrary import PlexLibrary
import configparser
from scripts.xdccDownloader.downloadXdcc import mainFunc

# Config File
config = configparser.ConfigParser()
config.read("../config/config.ini")
# Plex Config
plexCredentials = config["PlexCredentials"]
username = plexCredentials["username"]
password = plexCredentials["password"]
serverName = plexCredentials["serverName"]

app = Flask(__name__)

@app.route('/updateAnimePlexLibrary')
def updateAnimePlexLibrary(usernameFunc=username, passwordFunc=password, serverNameFunc=serverName):
    myPlexLibrary = PlexLibrary(usernameFunc, passwordFunc, serverNameFunc, "Anime")
    myPlexLibrary.updatePlexLibraryData()
    return "Anime Library Updated Successfully!"

@app.route('/updateAnimeDownloads')
def updateAllAnimeDownloads():
    updateAnimeList = mainFunc()
    returnCode = updateAnimeList[0]
    returnMsg = updateAnimeList[1]
    return returnMsg if returnCode == 1 else f"Error Occured in downloading Anime"

@app.route('/updateAnimeDownloads/<animeName>')
def updateAnimeDownloads(animeName):
    updateAnimeList = mainFunc(downloadAnimeName=animeName)
    returnCode = updateAnimeList[0]
    returnMsg = updateAnimeList[1]
    # print(returnCode, returnMsg, animeName)
    return returnMsg if returnCode == 1 else f"Error Occured in downloading Anime: {animeName}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2357)
