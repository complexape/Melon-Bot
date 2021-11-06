import os
from datetime import datetime

import discord
from discord.ext import commands
from pymongo import MongoClient

from helpers.db_manager import *
from constants import DBNAME


db_client = MongoClient(os.getenv("mongodb_url"))
db = db_client[DBNAME]

class VCTracker(commands.Cog, name="VC tracker"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def vcrank(self, ctx, arg = None):
        try:
            collection = db[str(ctx.guild.id)]
        except:
            await ctx.send(f"no activity found in **{ctx.guild.name}**.")
            return
        sorted_users = []
        if arg == "long":
            title = ":trophy: Longest Periods Spent in VC"
            users = list(collection.find({}, {"_id": 1,"longestvctime":1}))
            sorted_users = sorted(users, key=lambda items: items["longestvctime"], reverse=True)
        else:
            title = ":bar_chart: Total Time in VC"
            users = list(collection.find({}, {"_id": 1,"totalvctime":1}))
            sorted_users = sorted(users, key=lambda k: k["totalvctime"], reverse=True)
        embed = discord.Embed(
            title=f"{title} ({ctx.guild.name})", 
            color=0xf02dd0
        )
        embed.set_thumbnail(url=ctx.guild.icon_url)

        for position, user in enumerate(sorted_users):
            if position > 10: break

            user = await self.bot.fetch_user(user["_id"])
            name = user.display_name
            if arg == "long":
                time = user["longestvctime"]
            else:
                time = user["totalvctime"]

            # user has not been in vc yet
            if time == "1900-01-01 00:00:00.01": continue

            embed.add_field(
                name=f"{str(position)}. {name}", 
                value= await format_dtstring(time),
                inline=False
            )
            position +=1
        await ctx.send(embed=embed)

    @commands.command()
    async def stats(self, ctx):
        collection = db[str(ctx.guild.id)]
        if not await check_guild_member(ctx.author): 
            await ctx.send(f"no activity found for **{ctx.author.name}**.")
            return
        first_joined = collection.find_one({"_id": ctx.author.id})["firstjoined"]

        embed = discord.Embed(
            title=f":bar_chart: {ctx.author.name}'s stats ({ctx.guild.name})", 
            color=0x8088ff,
        )
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.set_footer(text="(taken since {})".format(datetime.strptime(first_joined, "%Y-%m-%d %H:%M:%S.%f").date()))
        embed.add_field(
            name="TOTAL VC TIME:", 
            value= await format_dtstring(collection.find_one({"_id": ctx.author.id})["totalvctime"]), 
            inline=True
        )
        embed.add_field(
            name="Longest Stayed in VC:", 
            value= await format_dtstring(collection.find_one({"_id": ctx.author.id})["longestvctime"]), 
            inline=False
        )
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot: return
        #user joins
        if not before.channel and after.channel and not after.afk:
            print(f"{member.name} joins {member.guild.name}")
            await check_guild_member(member)
            collection = db[str(member.guild.id)]
            collection.update_one({"_id": member.id}, {"$set":{"lastjoined": str(datetime.now(tz).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S.%f"))}}) 

            first_joined = collection.find_one({"_id": member.id})["firstjoined"]
            if first_joined == "":
                collection.update_one({"_id": member.id}, {"$set":{"firstjoined": str(datetime.now(tz).replace(tzinfo=None))}})

        #user leaves
        elif not after.channel and before.channel and not before.afk:
            print(f"{member.name} leaves {member.guild.name}")
            await check_guild_member(member)
            await user_leave(member, db[str(member.guild.id)])

    # automatically logs users' vc times to prepare for downtime
    @commands.command(hidden = True)
    @commands.is_owner()
    async def logvctimes(self, ctx):
        # loops through every user in every guild
        count = 0
        for name in db.list_collection_names():
            collection = db[name]
            for user in collection.find():
                # simulate user leaving
                await user_leave(user, collection)
                count+=1

        await ctx.author.send(embed=discord.Embed(
            title="Bot can now be stopped.",
            description=f"**{count}** member(s) successfully logged.",
            colour=0xfa0000
        ))

    @commands.command(hidden = True)
    @commands.is_owner()
    async def clearthisguild(self, ctx):
        if str(ctx.guild.id) in db.list_collection_names():
            db[str(ctx.guild.id)].drop()
            await ctx.send(f"`all data for '{ctx.guild.name}' cleared.`")
        else:
            await ctx.send("`data for this guild does not exist.`")

    @commands.command(hidden = True)
    @commands.is_owner()
    async def clearuser(self, ctx, *, name):
        try:
            collection = db[str(ctx.guild.id)]
            collection.delete_one({"name": name})
            await ctx.send(f"`all data for user: '{name}' in '{ctx.guild.name}' cleared.`")
        except:
            await ctx.send("`does not exist.`")

def setup(bot):
    bot.add_cog(VCTracker(bot))