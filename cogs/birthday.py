import os
from datetime import datetime, timedelta

import pytz
import discord
from discord.ext import commands
from pymongo import MongoClient

from helpers.db_manager import check_guild_member, background_task
from constants import DBNAME, TIMEZONE


db_client = MongoClient(os.getenv("mongodb_url"))
db = db_client[DBNAME]
tz = pytz.timezone(TIMEZONE)

class BDayTracker(commands.Cog, name="BDay tracker"):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.loop.create_task(background_task())  
        
    @commands.command(description="Let the bot know when your birthday is for a special message on your birthday...")
    async def setbday(self, ctx):
        prompt = await ctx.send("Please respond with your birthday in MM/DD/YYYY format (ex. 1/1/1999)")

        def check(msg):
            return msg.author.id == ctx.author.id and msg.channel.id == ctx.channel.id
        date_string = await self.bot.wait_for('message', check=check, timeout=30)
        await date_string.delete()
        await prompt.delete()
        try: #verfies user has sent a date
            birthday_dt = datetime.strptime(date_string.content, '%m/%d/%Y')
            if datetime.now(tz).replace(tzinfo=None) < birthday_dt:
                raise ValueError
        except ValueError:
            await ctx.send("Invalid. (date must be in the past and in MM/DD/YYYY format)")

        collection = db[str(ctx.guild.id)]
        await check_guild_member(ctx.author)
        if collection.find_one({"_id": ctx.author.id})["birthday"] != "":
            await ctx.send("You've already provided a birthday.")
            return

        warning = await ctx.send(f"Respond with 'CONFIRM' to confirm your birthday is on {date_string.content}. (you won't be able to change it ever again)")
        msg = await self.bot.wait_for('message', check=check, timeout=30)
        await msg.delete()
        await warning.delete()
        if msg.content != "CONFIRM":
            await ctx.send("Cancelled.")
            return
        collection.update_one({"_id": ctx.author.id}, {"$set":{"birthday": date_string.content}}) 
        await ctx.send("Success!")
        

    @commands.command(description="Displays upcoming birthdays within the next 2 weeks or less")
    async def upcomingbdays(self, ctx):
        collection = db[str(ctx.guild.id)]
        birthdays = list(collection.find({}, {"name": 1,"birthday":1}))
        description = ""
        for user in birthdays:
            if user["birthday"] == "":
                continue
            birthday = datetime.strptime(user["birthday"], '%m/%d/%Y')
            days_away = birthday.replace(year=2000) - datetime.today().replace(year=2000)

            if days_away < timedelta(weeks=2) and days_away > timedelta(days=0):
                name = user["name"]
                description += f"\n**{name}** (on **{user['birthday']}**)"
            if description == "": description = "No upcoming birthdays :/"
            
        await ctx.send(embed=discord.Embed(
            title=f"Birthdays coming in 2 Weeks or Less:", 
            color=0xf02dd0,
            description=description
        )) 

def setup(bot):
    bot.add_cog(BDayTracker(bot))