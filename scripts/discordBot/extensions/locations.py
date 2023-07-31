import discord
from discord.ext import commands
from scripts.common.enumTypes import Types


class Locations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="listLocationTypes",
        aliases=["listLT"],
        description="List all location type avaiable",
        help="Usage `!listLocationTypes`"
    )
    async def listLocationTypes(self, ctx):
        locationsList = u"\n".join(([locationType for locationType in Types.__members__]))
        await ctx.send(f"```\n{locationsList}```")

    @commands.command(
        name="listSetServerLocationTypes",
        aliases=["listSLT"],
        description="List all location type set on this server",
        help="Usage `!listSetServerLocationTypes`"
    )
    async def listSetServerLocationTypes(self, ctx):
        conn, cursor = self.bot.common_functions.connectToDb(self.bot.sql_server_name, self.bot.database)
        cursor.execute(f"""
            select *
            from discord_guild_channel_locations
            where guild_id = {ctx.guild.id}
        """)
        locations_list = cursor.fetchall()
        locations_list = u"\n".join(([f"{row[4]} - {row[5]}" for row in locations_list]))
        await ctx.send(f"```\n{locations_list}```")

    @commands.command(
        name="setLocations",
        aliases=["setL"],
        description="Set locations for notification updates",
        help='Usage `!setLocations "channel-name" "type"`'
    )
    async def setLocations(self, ctx, channelName, type):
        try:
            if not self.bot.common_functions.isAdminCheck(ctx):
                await ctx.send("You don't have permissions for this command")
                return
            conn, cursor = self.bot.common_functions.connectToDb(self.bot.sql_server_name, self.bot.database)
            type = Types(type.lower()).name
            channel = discord.utils.get(ctx.guild.text_channels, name=channelName)
            if channel is None:
                await ctx.send(f"Channel: `{channelName}` was not found on your server, please check your spelling.")
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
                    values ({guildId}, '{guildName.replace("'", "''")}', {channelId}, '{channelName.replace("'", "''")}', '{type}')
                """)
            elif recordExists == 1:
                cursor.execute(f"""
                    update discord_guild_channel_locations
                    set channel_id = {channelId}, channel_name = '{channelName.replace("'", "''")}'
                    where guild_id = {guildId} and type = '{type}'
                """)
            cursor.commit()
            await ctx.send(f"Successfully updated location for: `{type}` on your server")
            conn.commit()
            conn.close()
        except Exception as e:
            await ctx.send(f"Error Occurred: `{e}`")

    @commands.command(
        name="removeLocations",
        aliases=["removeL"],
        description="Remove locations for notification updates",
        help='Usage `!removeLocations "type"`'
    )
    async def removeLocations(self, ctx, type):
        try:
            if not self.bot.common_functions.isAdminCheck(ctx):
                await ctx.send("You don't have permissions for this command")
                return
            conn, cursor = self.bot.common_functions.connectToDb(self.bot.sql_server_name, self.bot.database)
            type = Types(type.lower()).name
            guildId = ctx.guild.id
            cursor.execute(f"""
                        select count(*) from discord_guild_channel_locations where guild_id = {guildId} and type = '{type}'
                    """)
            recordExists = cursor.fetchall()[0][0]
            if recordExists == 0:
                await ctx.send(
                    f"Permission: `{type}` was not found in your server, please check your spelling!")
                return
            else:
                cursor.execute(f"""
                    delete from discord_guild_channel_locations where guild_id = {guildId} and type = '{type}'
                """)
            cursor.commit()
            await ctx.send(f"Successfully removed location for: `{type}` from your server")
            conn.commit()
            conn.close()
        except Exception as e:
            await ctx.send(f"Error Occurred: `{e}`")
