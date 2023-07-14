from plexapi.myplex import MyPlexAccount
from dataclasses import dataclass


@dataclass
class PlexLibrary:
    """Class for plex library"""
    username: str
    password: str
    server_name: str
    library_name: str

    def __init__(self, username: str, password: str, server_name: str, library_name: str):
        self.username = username
        self.password = password
        self.server_name = server_name
        self.library_name = library_name
        self.account = MyPlexAccount(self.username, self.password)
        self.plex = self.account.resource(self.server_name).connect()
        self.anime_library = self.plex.library.section(self.library_name)

    def updatePlexLibraryData(self):
        self.anime_library.update()

    def updatePlexLibraryMetadate(self):
        self.anime_library.refresh()
