import os
from datetime import datetime, timedelta

import pytz
import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext, manage_commands
from discord_slash.utils.manage_commands import create_option, create_choice
from pymongo import MongoClient

from helpers.db_manager import check_guild_member, background_task
from constants import DBNAME, TIMEZONE


db_client = MongoClient(os.getenv("mongodb_url"))
db = db_client[DBNAME]
tz = pytz.timezone(TIMEZONE)

test_guilds = [779451772573450281, 620056088863178752]

class BDayTracker(commands.Cog, name="BDay tracker"):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.loop.create_task(background_task())  
        
    @cog_ext.cog_slash(
        name="setbday",
        description="Set the date of your birthday for a special message on that day. (Note: CANNOT be changed again)",
        guild_ids=test_guilds,
        options=[
            create_option(name="year", description="The year of your birthday.",option_type=4, required=True),
            create_option(name="month", description="The month of your birthday.",option_type=4, required=True),
            create_option(name="day", description="The day of your birthday.",option_type=4, required=True)
        ])
    async def _setbday(self, ctx: SlashContext, year: int, month: int, day: int):
        date = f"{month}/{day}/{year}"
        try: #verfies user has sent a date
            birthday_dt = datetime.strptime(date, '%m/%d/%Y')
            if datetime.now(tz).replace(tzinfo=None) < birthday_dt:
                raise ValueError
        except ValueError:
            await ctx.reply(f"'{date}' is not a valid date.", hidden=True)
            return
        collection = db[str(ctx.guild.id)]
        await check_guild_member(ctx.author)
        if collection.find_one({"_id": ctx.author.id})["birthday"] == "":
            collection.update_one({"_id": ctx.author.id}, {"$set":{"birthday": date}}) 
            await ctx.reply(f"Your birthday has successfully been set to: {date}", hidden=True)
        else: 
            await ctx.reply("You've already provided me a birthday.", hidden=True)   

    @cog_ext.cog_slash(
        name="upcomingbdays",
        guild_ids=test_guilds, 
        description="Displays known upcoming birthdays within the next two weeks."
    )
    async def _upcomingbdays(self, ctx: SlashContext):
        collection = db[str(ctx.guild.id)]
        birthdays = list(collection.find({}, {"name": 1,"birthday":1}))

        description = ""
        for user in birthdays:
            if user["birthday"] != "":
                birthday = datetime.strptime(user["birthday"], '%m/%d/%Y')
                days_away = birthday.replace(year=2000) - datetime.today().replace(year=2000)

                # birthday must be between the range of now and two weeks
                if days_away < timedelta(weeks=2) and days_away > timedelta(days=0):
                    description += f"\n- **{user['name']}**'s birthday is on **{user['birthday']}**)"

        await ctx.reply(embed=discord.Embed(
            title=f":birthday: Upcoming Birthdays in '{ctx.guild.name}' :birthday:", 
            color=0xf02dd0,
            description="No upcoming birthdays :/" if description == "" else description
        )) 

def setup(bot):
    bot.add_cog(BDayTracker(bot))