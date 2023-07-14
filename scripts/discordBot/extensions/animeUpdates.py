import discord
from discord.ext import commands, tasks
from scripts.common.enumDays import Days
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import threading
from scripts.config import config


class AnimeUpdates(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.added_anime = {}
        self.max_attempts = 5
        self.retry_add = True
        self.logger = config.logger
        # self.updateAnimeDownloadsForTodayTorrentLoop.start()

    @commands.command(
        name="addAnime",
        description="Add new anime to the download list",
        help="Add new anime to the download list"
    )
    async def addAnime(self, ctx):
        for attempt in range(self.max_attempts):
            try:
                if not self.retry_add:
                    break
                if not self.bot.common_functions.isAdminCheck(ctx):
                    await ctx.send("You don't have permissions for this command")
                    return
                conn, cursor = self.bot.common_functions.connectToDb()
                if not self.added_anime.get("name"):
                    await ctx.send("**Anime Name**")
                    name = await self.bot.wait_for("message", check=self.bot.common_functions.check(ctx.author))
                    self.added_anime["name"] = name.content
                if not self.added_anime.get("dir_name"):
                    await ctx.send("**Dir Name**")
                    dir_name = await self.bot.wait_for("message", check=self.bot.common_functions.check(ctx.author))
                    self.added_anime["dir_name"] = dir_name.content
                if not self.added_anime.get("english_name"):
                    await ctx.send("**English Name**")
                    english_name = await self.bot.wait_for("message", check=self.bot.common_functions.check(ctx.author))
                    self.added_anime["english_name"] = english_name.content
                if not self.added_anime.get("current_season"):
                    await ctx.send("**Current Season**")
                    current_season = await self.bot.wait_for("message", check=self.bot.common_functions.check(ctx.author))
                    self.added_anime["current_season"] = current_season.content
                if not self.added_anime.get("episode"):
                    await ctx.send("**Episode**")
                    episode = await self.bot.wait_for("message", check=self.bot.common_functions.check(ctx.author))
                    self.added_anime["episode"] = episode.content
                if not self.added_anime.get("torrent_provider"):
                    await ctx.send("**Torrent Provider**")
                    torrent_provider = await self.bot.wait_for("message", check=self.bot.common_functions.check(ctx.author))
                    self.added_anime["torrent_provider"] = torrent_provider.content
                if not self.added_anime.get("live_chart_url"):
                    await ctx.send("**LiveChart Url**")
                    live_chart_url = await self.bot.wait_for("message", check=self.bot.common_functions.check(ctx.author))
                    self.added_anime["live_chart_url"] = live_chart_url.content

                if not self.added_anime.get("image_url") or not self.added_anime.get("download_day"):
                    options = Options()
                    options.add_argument("--headless")
                    driver = webdriver.Chrome(service=Service(
                        ChromeDriverManager().install()),
                        options=options
                    )
                    driver.get(self.added_anime["live_chart_url"])
                    image = driver.find_elements(By.XPATH, "//div[@class='anime-poster']/img")
                    self.added_anime["image_url"] = image[0].get_attribute("src")

                    self.added_anime["download_day"] = self.bot.common_functions.getDayOfTheWeek(driver)

                embed = discord.Embed(
                    title="Add this anime to the download list? (Y/N)",
                    color=discord.Color.dark_teal()
                )
                embed.set_image(url=self.added_anime["image_url"])
                embed.add_field(name="Anime Name", value=self.added_anime["name"], inline=False)
                embed.add_field(name="Directory Name", value=self.added_anime["dir_name"], inline=False)
                embed.add_field(name="English Name", value=self.added_anime["english_name"], inline=False)
                embed.add_field(name="Current Season", value=self.added_anime["current_season"], inline=True)
                embed.add_field(name="Current Episode", value=self.added_anime["episode"], inline=True)
                embed.add_field(name="Download Day", value=Days(self.added_anime["download_day"]).name, inline=True)
                embed.add_field(name="Torrent Provider", value=self.added_anime["torrent_provider"], inline=False)

                await ctx.send(embed=embed)

                add_anime = False
                while True:
                    user_response = await self.bot.wait_for("message", check=self.bot.common_functions.check(ctx.author))
                    user_response = user_response.content
                    if user_response.lower() not in ("y", "n", "yes", "no"):
                        await ctx.send("Incorrect response, respond with ```y, n, yes, no```")
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
                        values ('{self.added_anime["name"]}',
                                '{self.added_anime["dir_name"]}',
                                '{self.added_anime["english_name"].replace("'", "''")}',
                                {self.added_anime["current_season"]},
                                {self.added_anime["episode"]},
                                1,
                                '{self.added_anime["live_chart_url"]}',
                                (select id from days where day_id = {self.added_anime["download_day"]}),
                                '{self.added_anime["image_url"]}',
                                '{self.added_anime["torrent_provider"]}')
                    """)
                    cursor.commit()
                    await ctx.send(f"Successfully Added Anime: `{self.added_anime['name']}`")

                conn.commit()
                conn.close()
                self.added_anime = {}
                break
            except Exception as e:
                self.logger.error(f"Error in addAnime(): {e}")
                await ctx.send("Error occured, would you like to retry adding the previous entry? (y/n)")
                user_response = await self.bot.wait_for("message", check=self.bot.common_functions.check(ctx.author))
                user_response = user_response.content
                while True:
                    if user_response.lower() not in ("y", "n", "yes", "no"):
                        await ctx.send("Incorrect response, respond with ```y, n, yes, no```")
                        continue
                    elif user_response.lower() in ("n", "no"):
                        self.retry_add = False
                        break
                    else:
                        self.logger.info("Retrying download")
                        break

    @commands.command(name="updateAnimeDownloadsTorrent")
    async def updateAnimeDownloadsTorrent(self, ctx, *args):
        if "UpdateAnimeDownloads" in self.bot.common_functions.getAllActiveThreadsName():
            await ctx.send("Downloading is already running, check notifications channel for more information.")
            return False
        animeName = None
        if len(args) > 1:
            await ctx.send(
                'Incorrect syntax, usage: ```!updateAnimeDownloadsTorrent``` or ```!updateAnimeDownloadsTorrent "anime name"```')
            return False
        elif len(args) == 1:
            animeName = args[0]
        thread = threading.Thread(target=self.bot.common_functions.updateDownloadsTorrent, args=(ctx.channel.id, animeName, False),
                                  name="UpdateAnimeDownloads")
        thread.start()

    @commands.command(name="updateAnimeDownloadsForTodayTorrent")
    async def updateAnimeDownloadsForTodayTorrent(self, ctx):
        if "UpdateAnimeDownloads" in self.bot.common_functions.getAllActiveThreadsName():
            await ctx.send("Download is already running, check notifications channel for more information.")
            return False
        thread = threading.Thread(target=self.bot.common_functions.updateDownloadsTorrent, args=(ctx.channel.id, None, True),
                                  name="UpdateAnimeDownloads")
        thread.start()

    @tasks.loop(seconds=7200)
    async def updateAnimeDownloadsForTodayTorrentLoop(self):
        if "UpdateAnimeDownloads" in self.bot.common_functions.getAllActiveThreadsName():
            print("Download is already running")
            return False
        thread = threading.Thread(target=self.bot.common_functions.updateDownloadsTorrent, args=(None, None, True),
                                  name="UpdateAnimeDownloads")
        thread.start()
