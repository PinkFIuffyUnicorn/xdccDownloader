import configparser
from Scripts.databaseAccess import Database
import sys
import os

# Config File
config = configparser.ConfigParser()
config.read("config.ini")
# Database Config
databaseConfig = config["Database"]
sqlServerName = databaseConfig["serverName"]
database = databaseConfig["database"]

try:
    databaseClass = Database(sqlServerName, database)
    conn, cursor = databaseClass.dbConnect()
except Exception as e:
    sys.exit(1)


directory = r"../Images/"

for subdir, dirs, files in os.walk(directory):
    for filename in files:
        filePath = os.path.abspath(filename).replace(r"\Scripts", r"\Images")
        name = filename.replace(".jpg","")

        print(filePath, name)
        cursor.execute(f"""
            update anime_to_download
            set image = (SELECT * FROM OPENROWSET(BULK N'{filePath}', SINGLE_BLOB) as T1)
            where name = '{name}'
        """)
        cursor.commit()
conn.commit()
conn.close()