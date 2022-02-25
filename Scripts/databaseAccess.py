import pyodbc
from dataclasses import dataclass

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