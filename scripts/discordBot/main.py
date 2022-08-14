import pprint
import os
import sys
import discord
from discord.ext import commands, tasks
import configparser
from scripts.common.databaseAccess import Database
from scripts.common.customLogger import Logger
from scripts.common.enumTypes import Types
import urllib.request
import pathlib

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
    myLoop.start()
    print(f"{bot.user} is online!")

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong!");

@bot.command(name="setLocations")
async def setLocations(ctx, channelName, type):
    try:
        if not isAdminCheck(ctx):
            await ctx.send("You don't have permissions for this command");
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

@bot.command(name="addAnime")
async def addAnime(ctx):
    try:
        if not isAdminCheck(ctx):
            await ctx.send("You don't have permissions for this command");
            return
        conn, cursor = connectToDb(sqlServerName, database)
        await ctx.send("Anime Name:")
        name = await bot.wait_for("message", check=check(ctx.author))
        name = name.content
        await ctx.send("Dir Name:")
        dirName = await bot.wait_for("message", check=check(ctx.author))
        dirName = dirName.content
        await ctx.send("English Name:")
        englishName = await bot.wait_for("message", check=check(ctx.author))
        englishName = englishName.content
        await ctx.send("Current Season:")
        currentSeason = await bot.wait_for("message", check=check(ctx.author))
        currentSeason = currentSeason.content
        await ctx.send("Episode:")
        episode = await bot.wait_for("message", check=check(ctx.author))
        episode = episode.content
        await ctx.send("Image Url:")
        imageUrl = await bot.wait_for("message", check=check(ctx.author))
        imageUrl = imageUrl.content
        dirPath = pathlib.Path(__file__).parent.parent.parent.resolve()
        urllib.request.urlretrieve(imageUrl, fr"{dirPath}\Images\{dirName}_Season {currentSeason}.png")
        image = os.path.abspath(fr"{dirPath}\Images\{dirName}_Season {currentSeason}.png")
        # print(name, dirName, englishName, currentSeason, episode, image)
        cursor.execute(f"""
            insert into anime_to_download (name, dir_name, english_name, current_season, episode, download, image)
            values ('{name}','{dirName}','{englishName}',{currentSeason},{episode},1,(SELECT * FROM OPENROWSET(BULK N'{image}', SINGLE_BLOB) as T1))
        """)
        cursor.commit()
        await ctx.send(f"Successfully Added Anime: `{name}`")

        conn.commit()
        conn.close()
    except Exception as e:
        await ctx.send(f"Error Occurred: `{e}`")

@bot.command(name="displayAllErrors")
async def displayAllErrors(ctx):
    if not isAdminCheck(ctx):
        await ctx.send("You don't have permissions for this command");
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
    tableCount = len(tablesList)

    await ctx.send(f"There are: {tableCount} errors, do you want to display them all? (Y/N)")
    userInput = await bot.wait_for("message", check=check(ctx.author))
    userInput = userInput.content
    if userInput.lower() != "y":
        return

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

            embed = discord.Embed(
                title="Download Error For Anime Episode"
                , description=f"**Anime:** {animeName}\n"
                              f"**Season:** {season}\n"
                              f"**Episode:** {episode}\n"
                              f"**Xdcc:** {xdcc}\n"
                              f"**Error:** {error}"
                , color=discord.Color.dark_teal()
            )
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
    # print("DB Connection Closed For Loop")

@bot.command(name="test")
async def test(ctx):
    dirPath = pathlib.Path(__file__).parent.parent.parent.resolve()
    image = os.path.abspath(fr"{dirPath}\Images\_Season.png")
    print(dirPath, image)

bot.run(TOKEN)