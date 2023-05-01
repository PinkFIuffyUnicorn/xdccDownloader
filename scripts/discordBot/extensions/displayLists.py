import math
import discord
from discord.ext import commands
from scripts.discordBot.extensions.commonFunctions import *
from .paginatedEmbed import PaginatedEmbed
from scripts.config import config

class DisplayLists(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sql_server_name = config.sqlServerName
        self.database = config.database

    @commands.command(
        name="displayAllErrors"
        , description="Display all errors that occured during download"
        , help="Display all errors that occured during download"
    )
    async def displayAllErrors(self, ctx):
        if not isAdminCheck(ctx):
            await ctx.send("You don't have permissions for this command")
            return
        conn, cursor = connectToDb(self.sql_server_name, self.database)
        cursor.execute("""
                select it.table_name
                from INFORMATION_SCHEMA.TABLES as it
            	inner join sys.tables as t on t.name = it.TABLE_NAME
            	where
            	it.TABLE_NAME in (select replace(dir_name,' ','_') from anime_to_download where download = 1)
            """)
        tablesList = cursor.fetchall()

        embedList = []
        for row in tablesList:
            tableName = row[0]
            animeName = tableName.replace("_", " ")

            cursor.execute(f"""
                    select 
                        season
                        , episode
                        , xdcc
                        , error
                        , (select live_chart_image_url From anime_to_download where dir_name = '{animeName}' and current_season = season) as image
                        , (select english_name From anime_to_download where dir_name = '{animeName}' and current_season = season) as english_name
                    from [{tableName}]
                    where
                        is_error = 1
                        or episode = 1
                """)
            erorrResult = cursor.fetchall()

            for row2 in erorrResult:
                season = "0" + str(row2[0]) if len(str(row2[0])) == 1 else row2[0]
                episode = "0" + str(row2[1]) if len(str(row2[1])) == 1 else row2[1]
                xdcc = row2[2]
                error = row2[3]
                image = row2[4]
                englishName = row2[5]

                # with open("image2.png", "wb") as f:
                #     f.write(image)

                embed = discord.Embed(
                    title="Download Error For Anime Episode"
                    , description=f"**Anime:** {animeName}\n"
                                  f"**English Name:** {englishName}\n"
                                  f"**Season:** {season}\n"
                                  f"**Episode:** {episode}\n"
                                  f"**Xdcc:** {xdcc}\n"
                                  f"**Error:** {error}"
                    , color=discord.Color.dark_teal()
                )
                embedList.append(embed)
                # await ctx.send(embed=embed)

        errorsCount = len(embedList)

        # await ctx.send(f"There are: {errorsCount} errors, do you want to display them all? (Y/N)")
        await ctx.send(f"There are: {errorsCount} errors, how many do you want to display?")
        userInput = await self.bot.wait_for("message", check=check(ctx.author))
        userInput = userInput.content
        # if userInput.strip().lower() != "y":
        #     return
        if not userInput.isdigit():
            return

        for index, embed in enumerate(embedList[0:int(userInput)]):
            embed.title = embed.title + f" ({index + 1}/{errorsCount})"
            await ctx.send(embed=embed)

        conn.commit()
        conn.close()

    @commands.command(name="listAllAnimeToDownload")
    async def listAllAnimeToDownload(self, ctx):
        conn, cursor = connectToDb(self.sql_server_name, self.database)
        cursor.execute("""
                        select name, episode, current_season
                        from anime_to_download
                        where download = 1
                        order by name
                    """)
        allAnimeToDownloadList = cursor.fetchall()

        embedList = []
        current_page = 0
        all_pages = math.ceil(len(allAnimeToDownloadList) / 7)
        new_page = False

        for index, row in enumerate(allAnimeToDownloadList):
            if current_page != math.ceil((index + 1) / 7):
                current_page = math.ceil((index + 1) / 7)
                new_page = True
                if index != 0:
                    embedList.append(embed)
            if new_page:
                new_page = False
                embed = discord.Embed(
                    title=f"All Anime currently scheduled to download."
                    , color=discord.Color.dark_teal()
                )
                embed.add_field(name="Anime Name", value="", inline=True)
                embed.add_field(name="Current Season", value="", inline=True)
                embed.add_field(name="Current Episode", value="", inline=True)
                embed.set_footer(text=f"Page {current_page}/{all_pages}")
            name = row[0]
            episode = row[1]
            current_season = row[2]

            embed.add_field(name="", value=name, inline=True)
            embed.add_field(name="", value=current_season, inline=True)
            embed.add_field(name="", value=episode, inline=True)

            if (index + 1) == len(allAnimeToDownloadList):
                embedList.append(embed)

        cursor.commit()
        conn.commit()
        conn.close()

        if len(embedList) > 0:
            paginated_embed = PaginatedEmbed(ctx, embedList)
            await paginated_embed.start()