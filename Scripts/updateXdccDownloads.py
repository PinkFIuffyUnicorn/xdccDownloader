import pyodbc

sqlServerName = "DESKTOP-V6UNK5R"
database = "master"

conn = pyodbc.connect('Driver={SQL Server};'
                      'Server='+sqlServerName+';'
                      'Database='+database+';'
                      'Trusted_Connection=yes;')
cursor = conn.cursor()

cursor.execute(
    "createXdccView"
)
viewList = cursor.fetchall()

createView = ""
for row in viewList:
    createViewRow = row[0]
    createView = u" ".join((createView, createViewRow))

cursor.execute(createView)

cursor.execute("select *, 'update [' + table_name + '] set downloaded = 1 where episode = ' + cast(episode as varchar(100)) from tempView"
               #" where table_name = 'Boku_no_Hero_Academia' and episode = 1"
               #" where table_name <> 'Boku_no_Hero_Academia'"
            )
tempViewResult = cursor.fetchall()

for row in tempViewResult:
    id = row[0]
    xdcc = row[1]
    season = row[2]
    episode = row[3]
    downloaded = row[4]
    error = row[5]
    is_error = row[6]
    tableName = row[7]
    updateStatement = row[8]
    print(f"""
        Anime: {tableName}
        Episode = {episode}
        Xdcc: {xdcc}
    """)

    decision = input(f"Would you like to mark this xdcc for {tableName} - {episode} as downloaded(Y/N)?")
    #decision = "y"

    if decision.lower() in ("y","yes","d"):
        cursor.execute(updateStatement)
        cursor.commit()

    elif decision.lower() in ("n","no"):
        print(f"Skipped download for {tableName} - {episode}")

#cursor.execute("drop view tempView")

cursor.commit()
conn.commit()
conn.close()