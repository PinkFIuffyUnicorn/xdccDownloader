import math
import pprint
import os
import sys
import discord
from discord.ext import commands, tasks
import configparser
from scripts.common.databaseAccess import Database
from scripts.common.customLogger import Logger
from scripts.common.enumTypes import Types
from scripts.xdccDownloader.downloadXdcc import mainFunc
from scripts.common.plexLibrary import PlexLibrary
import urllib.request
import pathlib
import configparser

# Config File
config = configparser.ConfigParser()
config.read("../config/config.ini")
# Plex Config
plexCredentials = config["PlexCredentials"]
username = plexCredentials["username"]
password = plexCredentials["password"]
serverName = plexCredentials["serverName"]

def connectToDb(sqlServerName, database):
    try:
        # print("Connecting to DB...")
        databaseClass = Database(sqlServerName, database)
        conn, cursor = databaseClass.dbConnect()
        # print("Connection successful")
        return conn, cursor
    except Exception as e:
        print("Connection unsuccessful")
        sys.exit(1)

def getChannelId(allChannels, channelName):
    channel = discord.utils.get(allChannels, name=channelName)
    return channel.id if channel != None else channel

def check(author):
    def inner_check(messsage):
        return messsage.author == author
    return inner_check

def isAdminCheck(ctx):
    return "GayRole" in [role.name for role in ctx.author.roles] or ctx.author.name == "Pink Fluffy Unicorn"

# Config File
config = configparser.ConfigParser()
config.read("../config/config.ini")
# Database Config
databaseConfig = config["Database"]
sqlServerName = databaseConfig["serverName"]
database = databaseConfig["database"]

# TOKEN = "NDM2NTkyNDYzNTI5MTE1NjU4.GoOVnc.xD1HZv1XOuacqIygVeqESxlSju9HN7G_2m66LA" # Sana-Chan
TOKEN = "OTk1NzMyOTUxMzc3NjQ5ODc1.G_gaRf.mEkzfCdNLd3nb0uvum31NBsm26rQHRWfyDWmls" # Igor Igorović
bot = commands.Bot(command_prefix="!")

# notificationsChannel = "notifications"

@bot.event
async def on_ready():
    # myLoop.start()
    print(f"{bot.user} is online!")

@bot.command(
    name="setLocations"
    , description="Set locations for notification updates"
    , help="Set locations for notification updates"
)
async def setLocations(ctx, channelName, type):
    try:
        if not isAdminCheck(ctx):
            await ctx.send("You don't have permissions for this command")
            return
        conn, cursor = connectToDb(sqlServerName, database)
        type = Types(type).name
        channel = discord.utils.get(ctx.guild.text_channels, name=channelName)
        if channel == None:
            await ctx.send(f"Channel: `{channelName}` was not found in your server, please check your spelling!")
            return
        channelId = channel.id
        guildId = ctx.guild.id
        guildName = ctx.guild.name
        cursor.execute(f"""
            select count(*) from discord_guild_channel_locations where guild_id = {guildId} and type = '{type}'
        """)
        recordExists = cursor.fetchall()[0][0]
        if recordExists == 0:
            cursor.execute(f"""
                insert into discord_guild_channel_locations(guild_id, guild_name, channel_id, channel_name, type)
                values ({guildId}, '{guildName}', {channelId}, '{channelName}', '{type}')
            """)
        elif recordExists == 1:
            cursor.execute(f"""
                update discord_guild_channel_locations
                set channel_id = {channelId}, channel_name = '{channelName}'
                where guild_id = {guildId} and type = '{type}'
            """)
        # print(guildId, guildName, channelId, channelName, type, recordExists)
        cursor.commit()
        await ctx.send(f"Successfully updated location for: `{type}`")

        conn.commit()
        conn.close()
    except Exception as e:
        await ctx.send(f"Error Occurred: `{e}`")

@bot.command(
    name="addAnime"
    , description="Add new anime to the download list"
    , help="Add new anime to the download list"
)
async def addAnime(ctx):
    try:
        if not isAdminCheck(ctx):
            await ctx.send("You don't have permissions for this command")
            return
        conn, cursor = connectToDb(sqlServerName, database)
        await ctx.send("**Anime Name**")
        name = await bot.wait_for("message", check=check(ctx.author))
        name = name.content
        await ctx.send("**Dir Name**")
        dirName = await bot.wait_for("message", check=check(ctx.author))
        dirName = dirName.content
        await ctx.send("**English Name**")
        englishName = await bot.wait_for("message", check=check(ctx.author))
        englishName = englishName.content
        await ctx.send("**Current Season**")
        currentSeason = await bot.wait_for("message", check=check(ctx.author))
        currentSeason = currentSeason.content
        await ctx.send("**Episode**")
        episode = await bot.wait_for("message", check=check(ctx.author))
        episode = episode.content
        await ctx.send("**Download Day**```0 - Monday, 1 - Tuesday, 2 - Wednesday, 3 - Thursday, 4 - Friday, 5 - Saturday, 6 - Sunday```")
        downloadDay = await bot.wait_for("message", check=check(ctx.author))
        downloadDay = downloadDay.content
        await ctx.send("**Image Url**")
        imageUrl = await bot.wait_for("message", check=check(ctx.author))
        imageUrl = imageUrl.content
        dirPath = pathlib.Path(__file__).parent.parent.parent.resolve()
        urllib.request.urlretrieve(imageUrl, fr"{dirPath}\Images\{dirName}_Season {currentSeason}.png")
        image = os.path.abspath(fr"{dirPath}\Images\{dirName}_Season {currentSeason}.png")
        # print(name, dirName, englishName, currentSeason, episode, image)
        cursor.execute(f"""
            insert into anime_to_download (name, dir_name, english_name, current_season, episode, download, image, download_day)
            values ('{name}','{dirName}','{englishName.replace("'","''")}',{currentSeason},{episode},1,(SELECT * FROM OPENROWSET(BULK N'{image}', SINGLE_BLOB) as T1),(select id from days where day_id = {downloadDay}))
        """)
        cursor.commit()
        await ctx.send(f"Successfully Added Anime: `{name}`")

        conn.commit()
        conn.close()
    except Exception as e:
        await ctx.send(f"Error Occurred: `{e}`")

@bot.command(
    name="displayAllErrors"
    , description="Display all errors that occured during download"
    , help="Display all errors that occured during download"
)
async def displayAllErrors(ctx):
    if not isAdminCheck(ctx):
        await ctx.send("You don't have permissions for this command")
        return
    conn, cursor = connectToDb(sqlServerName, database)
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
                    , (select image From anime_to_download where dir_name = '{animeName}' and current_season = season) as image
                    , (select english_name From anime_to_download where dir_name = '{animeName}' and current_season = season) as english_name
                from {tableName}
                where
                    is_error = 1
                    or episode between 8 and 10
            """)
        erorrResult = cursor.fetchall()
        for row2 in erorrResult:
            season = "0" + str(row2[0]) if len(str(row2[0])) == 1 else row2[0]
            episode = "0" + str(row2[1]) if len(str(row2[1])) == 1 else row2[1]
            xdcc = row2[2]
            error = row2[3]
            image = row2[4]
            englishName = row2[5]

            with open("image2.png", "wb") as f:
                f.write(image)

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
    userInput = await bot.wait_for("message", check=check(ctx.author))
    userInput = userInput.content
    # if userInput.strip().lower() != "y":
    #     return
    if not userInput.isdigit():
        return

    for index, embed in enumerate(embedList[0:int(userInput)]):
        embed.title = embed.title + f" ({index+1}/{errorsCount})"
        await ctx.send(embed=embed)

@tasks.loop(seconds=600)
async def myLoop():
    conn, cursor = connectToDb(sqlServerName, database)
    cursor.execute("""
        select it.table_name
        from INFORMATION_SCHEMA.TABLES as it
    	inner join sys.tables as t on t.name = it.TABLE_NAME
    	where
    	it.TABLE_NAME in (select replace(dir_name,' ','_') from anime_to_download where download = 1)
    """)
    tablesList = cursor.fetchall()

    for row in tablesList:
        tableName = row[0]

        cursor.execute(f"""
                select 
                    *
                from {tableName}
                where
                    notification_sent = 0
                    and downloaded = 1
            """)
        notificationsResult = cursor.fetchall()

        for row2 in notificationsResult:
            season = "0" + str(row2[2]) if len(str(row2[2])) == 1 else row2[2]
            episode = "0" + str(row2[3]) if len(str(row2[3])) == 1 else row2[3]
            animeName = tableName.replace("_", " ")
            # print(animeName)

            cursor.execute(f"""
                select image From anime_to_download
                where dir_name = '{animeName}' and current_season = {season}
            """)
            image = cursor.fetchone()[0]

            with open("image.png", "wb") as f:
                f.write(image)

            embed = discord.Embed(
                title="Added Anime Episode"
                , description=f"**Anime:** {animeName}\n"
                              f"**Season:** {season}\n"
                              f"**Episode:** {episode}"
                , color=discord.Color.dark_teal()
            )
            embed.set_image(url=f"attachment://image.png")
            allGuilds = await bot.fetch_guilds().flatten()
            for guild in allGuilds:
                file = discord.File("image.png", filename="image.png")
                cursor.execute(f"""
                    select channel_id from discord_guild_channel_locations where guild_id = {guild.id}
                """)
                row3 = cursor.fetchone()
                if row3 != None:
                    channelId = row3[0]
                    await bot.get_channel(channelId).send(embed=embed, file=file)
                    cursor.execute(f"""
                        update {tableName}
                        set notification_sent = 1
                        where episode = {episode} and season = {season}
                    """)
                    cursor.commit()
    conn.commit()
    conn.close()
    print("DB Connection Closed For Loop")

@bot.command(name="updateAnimePlexLibrary")
async def updateAnimePlexLibrary(ctx):
    myPlexLibrary = PlexLibrary(username, password, serverName, "Anime")
    myPlexLibrary.updatePlexLibraryData()
    print("Anime Library Updated Successfully!")
    await ctx.send("Anime Library Updated Successfully!")

@bot.command(name="updateAnimeDownloads")
async def updateAnimeDownloads(ctx, *args):
    animeName = ""
    if len(args) > 1:
        await ctx.send('Incorrect syntax, usage: ```!updateAnimeDownloads``` or ```!updateAnimeDownloads "anime name"```')
        return False
    elif len(args) == 1:
        animeName = args[0]
    await ctx.send("Download Started")
    updateAnimeList = mainFunc(downloadAnimeName=animeName, printOutput=False)
    returnCode = updateAnimeList[0]
    returnMsg = updateAnimeList[1]
    print(returnMsg if returnCode == 1 else f"Error Occured in downloading Anime")
    await ctx.send(returnMsg if returnCode == 1 else f"Error Occured in downloading Anime" + f": ```{animeName}```" if animeName != "" else "")

@bot.command(name="listAllAnimeToDownload")
async def listAllAnimeToDownload(ctx):
    conn, cursor = connectToDb(sqlServerName, database)
    cursor.execute("""
            select name, episode, current_season
            from anime_to_download
            where download = 1
            order by name
        """)
    allAnimeToDownloadList = cursor.fetchall()

    embed = discord.Embed()
    current_page = 0
    all_pages = math.ceil(len(allAnimeToDownloadList) / 7)
    new_page = False

    for index, row in enumerate(allAnimeToDownloadList):
        if current_page != math.ceil((index + 1) / 7):
            current_page = math.ceil((index + 1) / 7)
            new_page = True
            if index != 0:
                await ctx.send(embed=embed)
                next_page = await bot.wait_for("message", check=check(ctx.author))
                next_page = next_page.content
                if next_page.lower() != "next":
                    break
        if new_page:
            new_page = False
            embed = discord.Embed(
                title="Added Anime Episode (Type 'next' for next page)"
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
            await ctx.send(embed=embed)

    cursor.commit()
    conn.commit()
    conn.close()

@bot.command(name="test")
async def test(ctx):
    await ctx.send("**Download Day** ```0 - Monday, 1 - Tuesday, 2 - Wednesday, 3 - Thursday, 4 - Friday, 5 - Saturday, 6 - Sunday```")

bot.run(TOKEN)