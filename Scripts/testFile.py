import pyodbc
import configparser
from datetime import datetime

def dbConnect(sqlServerName, database):
    conn = pyodbc.connect(
        'Driver={SQL Server};'
        'Server=' + sqlServerName + ';'
        'Database=' + database + ';'
        'Trusted_Connection=yes;'
    )
    return [conn, conn.cursor()]

config = configparser.ConfigParser()
config.read("config.ini")
databaseConfig = config["Database"]
sqlServerName = databaseConfig["serverName"]
database = databaseConfig["database"]

db = dbConnect(sqlServerName, database)
conn = db[0]
cursor = db[1]

currentDatetime = datetime.now()
formattedCurrentDatetime = currentDatetime.strftime("%d-%m-%Y %H_%M_%S")

backup = rf"backup database [master] to disk = N'C:\Users\Nabernik\Desktop\GitHub\xdccDownloader\DB Backups\masterBKP_{formattedCurrentDatetime}.bak'"
conn.autocommit = True
cursor.execute(backup)
while cursor.nextset():
    pass
conn.close()