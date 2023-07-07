import discord
from discord.ext import commands, tasks
from scripts.discordBot.extensions.commonFunctions import *
from scripts.common.enumDays import Days
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from scripts.config import config
from datetime import datetime

class AnimeUpdates(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sql_server_name = config.sqlServerName
        self.database = config.database
        # self.updateAnimeDownloadsForTodayTorrentLoop.start()

    @commands.command(
        name="addAnime"
        , description="Add new anime to the download list"
        , help="Add new anime to the download list"
    )
    async def addAnime(self, ctx):
        try:
            if not isAdminCheck(ctx):
                await ctx.send("You don't have permissions for this command")
                return
            conn, cursor = connectToDb(sqlServerName, database)
            await ctx.send("**Anime Name**")
            name = await self.bot.wait_for("message", check=check(ctx.author))
            name = name.content
            await ctx.send("**Dir Name**")
            dirName = await self.bot.wait_for("message", check=check(ctx.author))
            dirName = dirName.content
            await ctx.send("**English Name**")
            englishName = await self.bot.wait_for("message", check=check(ctx.author))
            englishName = englishName.content
            await ctx.send("**Current Season**")
            currentSeason = await self.bot.wait_for("message", check=check(ctx.author))
            currentSeason = currentSeason.content
            await ctx.send("**Episode**")
            episode = await self.bot.wait_for("message", check=check(ctx.author))
            episode = episode.content
            await ctx.send("**Torrent Provider**")
            torrent_provider = await self.bot.wait_for("message", check=check(ctx.author))
            torrent_provider = torrent_provider.content
            # await ctx.send(
            #     "**Download Day**```1 - Monday, 2 - Tuesday, 3 - Wednesday, 4 - Thursday, 5 - Friday, 6 - Saturday, 7 - Sunday```")
            # downloadDay = await self.bot.wait_for("message", check=check(ctx.author))
            # downloadDay = downloadDay.content
            await ctx.send("**LiveChart Url**")
            liveChartUrl = await self.bot.wait_for("message", check=check(ctx.author))
            liveChartUrl = liveChartUrl.content

            options = Options()
            options.add_argument("--headless")
            driver = webdriver.Chrome(service=Service(
                ChromeDriverManager().install())
                , options=options
            )
            driver.get(liveChartUrl)
            image = driver.find_elements(By.XPATH, "//div[@class='anime-poster']/img")
            imageUrl = image[0].get_attribute("src")

            downloadDay = getDayOfTheWeek(driver)

            embed = discord.Embed(
                title="Add this anime to the collection? (Y/N)"
                , color=discord.Color.dark_teal()
            )
            embed.set_image(url=imageUrl)
            embed.add_field(name="Anime Name", value=name, inline=False)
            embed.add_field(name="Directory Name", value=dirName, inline=False)
            embed.add_field(name="English Name", value=englishName, inline=False)
            embed.add_field(name="Current Season", value=currentSeason, inline=True)
            embed.add_field(name="Current Episode", value=episode, inline=True)
            embed.add_field(name="Download Day", value=Days(downloadDay).name, inline=True)
            embed.add_field(name="Torrent Provider", value=torrent_provider, inline=False)

            await ctx.send(embed=embed)

            add_anime = False
            while True:
                user_response = await self.bot.wait_for("message", check=check(ctx.author))
                user_response = user_response.content
                if user_response.lower() not in ("y", "n", "yes", "no"):
                    await ctx.send("Incorrect reponse, repond with ```y, n, yes, no```")
                    continue
                elif user_response.lower() in ("y", "yes"):
                    add_anime = True
                    break
                break

            if add_anime:
                # dirPath = pathlib.Path(__file__).parent.parent.parent.resolve()
                # urllib.request.urlretrieve(imageUrl, fr"{dirPath}\Images\{dirName}_Season {currentSeason}.png")
                # image = os.path.abspath(fr"{dirPath}\Images\{dirName}_Season {currentSeason}.png")
                # print(name, dirName, englishName, currentSeason, episode, image)
                cursor.execute(f"""
                    insert into anime_to_download (name, dir_name, english_name, current_season, episode, download, live_chart_url, download_day, live_chart_image_url, torrent_provider)
                    values ('{name}','{dirName}','{englishName.replace("'", "''")}',{currentSeason},{episode},1,'{liveChartUrl}',(select id from days where day_id = {downloadDay}), '{imageUrl}', '{torrent_provider}')
                """)
                cursor.commit()
                await ctx.send(f"Successfully Added Anime: `{name}`")

            conn.commit()
            conn.close()
        except Exception as e:
            await ctx.send(f"Error Occurred: `{e}`")

    # @commands.command(name="updateAnimeDownloadsForToday")
    # async def updateAnimeDownloadsForToday(self, ctx):
    #     if "UpdateAnimeDownloads" in getAllActiveThreadsName():
    #         await ctx.send("Downloading is already running, check notifications channel for more information.")
    #         return False
    #
    #     thread = threading.Thread(target=updateDownloads, args=(ctx.channel.id, None, True), name="UpdateAnimeDownloads")
    #     thread.start()
    #
    # @commands.command(name="updateAnimeDownloads")
    # async def updateAnimeDownloads(self, ctx, *args):
    #     if "UpdateAnimeDownloads" in getAllActiveThreadsName():
    #         await ctx.send("Downloading is already running, check notifications channel for more information.")
    #         return False
    #     animeName = None
    #     if len(args) > 1:
    #         await ctx.send(
    #             'Incorrect syntax, usage: ```!updateAnimeDownloads``` or ```!updateAnimeDownloads "anime name"```')
    #         return False
    #     elif len(args) == 1:
    #         animeName = args[0]
    #
    #     thread = threading.Thread(target=updateDownloads, args=(ctx.channel.id, animeName, False), name="UpdateAnimeDownloads")
    #     thread.start()

    @commands.command(name="updateAnimeDownloadsTorrent")
    async def updateAnimeDownloadsTorrent(self, ctx, *args):
        if "UpdateAnimeDownloads" in getAllActiveThreadsName():
            await ctx.send("Downloading is already running, check notifications channel for more information.")
            return False
        animeName = None
        if len(args) > 1:
            await ctx.send(
                'Incorrect syntax, usage: ```!updateAnimeDownloadsTorrent``` or ```!updateAnimeDownloadsTorrent "anime name"```')
            return False
        elif len(args) == 1:
            animeName = args[0]
        thread = threading.Thread(target=updateDownloadsTorrent, args=(ctx.channel.id, animeName, False),
                                  name="UpdateAnimeDownloads")
        thread.start()

    @commands.command(name="updateAnimeDownloadsForTodayTorrent")
    async def updateAnimeDownloadsForTodayTorrent(self, ctx):
        if "UpdateAnimeDownloads" in getAllActiveThreadsName():
            await ctx.send("Download is already running, check notifications channel for more information.")
            return False
        thread = threading.Thread(target=updateDownloadsTorrent, args=(ctx.channel.id, None, True),
                                  name="UpdateAnimeDownloads")
        thread.start()

    @tasks.loop(seconds=3600*4)
    async def updateAnimeDownloadsForTodayTorrentLoop(self):
        if "UpdateAnimeDownloads" in getAllActiveThreadsName():
            print("Download is already running")
            return False
        thread = threading.Thread(target=updateDownloadsTorrent, args=(None, None, True),
                                  name="UpdateAnimeDownloads")
        thread.start()