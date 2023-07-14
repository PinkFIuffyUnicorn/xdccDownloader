from lxml import etree
import requests
import sys
from datetime import datetime
from scripts.common.databaseAccess import Database
from scripts.common.qBitTorrent import QBitTorrent
from scripts.config import config

class DownloadTorrent:
    def __init__(self, anime_name, current_day):
        super().__init__()
        self.anime_name = anime_name
        self.current_day = current_day
        # Logger
        self.logger = config.logger
        # Database Config
        self.sqlServerName = config.sqlServerName
        self.database = config.database
        # Plex Config
        self.username = config.username
        self.password = config.password
        self.plexServerName = config.plexServerName
        # SubsPlease RSS Feed
        self.subsplease_url = config.url1080
        # Other Variables
        self.parentDir = config.parentDir
        # self.dbBackupPath = rf"C:\Users\Aleš\Desktop\GitHub\xdccDownloader_OBSOLETE\DB Backups\animeBKP_{self.currentTimestamp('db')}.bak"

    def getDbConnAndCursor(self):
        try:
            databaseClass = Database(self.sqlServerName, self.database)
            self.logger.info("DB Connection successful")
            return databaseClass.dbConnect()
        except Exception as e:
            self.logger.error("Error Connecting to DB " + self.formatError(e))
            return [2, f"Db Exception occured: {self.formatError(e)}"]

    def getDiscordGuildChannelLocations(self):
        conn, cursor = self.getDbConnAndCursor()
        cursor.execute("""
            select channel_id from discord_guild_channel_locations where type = 'updateAnimeNotifications'
        """)

        return cursor.fetchall()

    def getAnimeListFromDbTorrent(self):
        animeList = []
        # Database Connection And Cursor
        conn, cursor = self.getDbConnAndCursor()
        if conn == 2:
            sys.exit(cursor)
        downloadAnimeName = f" and name = '{self.anime_name}'" if self.anime_name != None and self.anime_name != "" else " "
        currentDayDownload = f" and download_day = {datetime.now().weekday() + 1}" if self.current_day == True else " "
        sql = f"""
                    select
                         id as '0'
                        , name as '1'
                        , episode as '2'
                        , quality as '3'
                        , done as '4'
                        , last_change_date as '5'
                        , current_season as '6'
                        , dir_name as '7'
                        , english_name as '8'
                        , live_chart_image_url as '9'
                        , torrent_provider as '10'
                    from
                        anime_to_download
                    where 1 = 1
                    and download = 1
                    and done = 0
                    {downloadAnimeName}
                    {currentDayDownload}
                     order by name
                """
        cursor.execute(sql)
        downloadList = cursor.fetchall()

        subsplease_query_list = [f"([{x[10]}] {x[1]})" for x in downloadList]
        subsplease_query_string = u"|".join((subsplease_query_list)) + " 1080p"
        # print(f"https://nyaa.si/?page=rss&q={subsplease_query_string}&c=0_0&f=0")

        # https://nyaa.si/?page=rss&q={QUERY}&c=0_0&f=0
        # https://nyaa.si/?page=rss&q=([SubsPlease]) | ([Anime Time] Tengoku) 1080p&c=0_0&f=0

        # r = requests.get(url=subsplease_url)
        # print(subsplease_query_string)
        r = requests.get(url=f"https://nyaa.si/?page=rss&q={subsplease_query_string}&c=0_0&f=0", timeout=300)
        subsplease_content = r.content
        root = etree.fromstring(subsplease_content)

        for row in downloadList:
            id = int(row[0])
            name = row[1]
            episode = int(row[2])
            # episode = "0" + str(episode) if len(str(episode)) == 1 else episode
            quality = row[3]
            done = row[4]
            last_change_date = row[5]
            current_season = int(row[6])
            dir_name = row[7]
            english_name = row[8]
            live_chart_image_url = row[9]
            torrent_provider = row[10]

            self.logger.debug(f"Anime was updated {(datetime.now() - last_change_date).days} days ago")
            if (datetime.now() - last_change_date).days > 30:
                cursor.execute(f"""
                                        update anime_to_download
                                        set done = 1, download = 0
                                        where id = {id}
                        """)
                self.logger.info(f"Updated Anime ({name}) to done")
                continue

            while True:
                searchTerm = f"{name} - {'0' + str(episode) if len(str(episode)) == 1 else episode}"
                if name == "Summer Time Rendering":
                    searchTerm = f"{name} S01E{'0' + str(episode) if len(str(episode)) == 1 else episode}"
                # print(searchTerm)
                items = root.xpath(f".//item/title[contains(text(), '{searchTerm}')]")
                items = [item.getparent() for item in items]
                for index, item in enumerate(items):
                    torrent_link = item[1].text
                    # animeList.append(["", "", dir_name, episode, current_season, live_chart_image_url, torrent_link])
                    animeList.append([dir_name, episode, current_season, live_chart_image_url, torrent_link, english_name])

                    cursor.execute(
                        f"select count(*) from information_schema.tables where table_name = '{dir_name.replace(' ', '_')}'"
                    )
                    checkTableExists = cursor.fetchall()[0][0]
                    if checkTableExists == 0:
                        cursor.execute(f"""
                            create table [{dir_name.replace(' ', '_')}] (
                                id int IDENTITY(1,1) PRIMARY KEY
                                , xdcc varchar(100)
                                , season int
                                , episode int
                                , downloaded bit default 0
                                , error varchar(8000)
                                , is_error bit default 0
                                , notification_sent bit default 0
                            )
                        """)
                        self.logger.debug(f"Added new Anime table ({dir_name.replace(' ', '_')})")

                    cursor.execute(
                        f"select count(*) from [{dir_name.replace(' ', '_')}] where episode = {episode} and season = {current_season}"
                    )
                    checkEpisodeExists = cursor.fetchall()[0][0]
                    if checkEpisodeExists == 0:
                        cursor.execute(
                            f"insert into [{dir_name.replace(' ', '_')}] (episode, xdcc, season) values ({episode},'{torrent_link}',{current_season})"
                        )
                        self.logger.debug(f"Inserted new episode into Anime table ({dir_name.replace(' ', '_')})")
                    episode += 1

                    if len(items) == index + 1:
                        cursor.execute(f"""
                            update anime_to_download
                            set episode = {episode}
                            where id = {id}
                        """)
                        self.logger.debug(f"Updated Anime ({name}) episode")

                    break
                else:
                    break

        cursor.commit()
        conn.commit()
        conn.close()

        return animeList

    def downloadAnimeFromListTorrent(self, anime_list_to_download):
        conn, cursor = self.getDbConnAndCursor()
        if conn == 2:
            sys.exit(cursor)

        qbt_client = QBitTorrent("localhost", 8080)

        for anime in anime_list_to_download:
            qbt_client.addTorent(anime)