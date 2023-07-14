import pyodbc
from dataclasses import dataclass
import os
import glob
from datetime import datetime, timedelta


@dataclass
class Database():
    """Class for Database operations"""
    sql_server_name: str
    database_name: str

    def __init__(self, sql_server_name: str, database_name: str):
        self.sql_server_name = sql_server_name
        self.database_name = database_name

    def dbConnect(self):
        conn = pyodbc.connect(
            'Driver={SQL Server};'
            'Server=' + self.sql_server_name + ';'
            'Database=' + self.database_name + ';'
            'Trusted_Connection=yes;'
        )
        return conn, conn.cursor()

    def dbBackup(self, conn, cursor, path):
        backup = rf"backup database [{self.database_name}] to disk = N'{path}'"
        conn.autocommit = True
        cursor.execute(backup)
        while cursor.nextset():
            pass

    def deleteOldBackups(self):
        deletedFiles = []
        os.chdir("../../DB Backups")
        for file in glob.glob("*.bak"):
            fileExists = os.path.exists(file)
            if fileExists:
                filePath = os.path.abspath(file)
                timestamp = int(os.path.getctime(filePath))
                fileDate = datetime.utcfromtimestamp(timestamp)
                currentDate = datetime.today() - timedelta(days=7)
                deleteFile = fileDate < currentDate
                if deleteFile:
                    deletedFiles.append(file)
                    os.remove(file)
        return deletedFiles
