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

    def updatePlexLibrary(self):
        account = MyPlexAccount(self.username, self.password)
        plex = account.resource(self.server_name).connect()
        anime_library = plex.library.section(self.library_name)
        anime_library.update()