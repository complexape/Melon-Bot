import os
from datetime import datetime

import discord
from discord import team
from discord.ext import commands
from discord_slash import cog_ext, SlashContext, manage_commands
from discord_slash.utils.manage_commands import create_option, create_choice
from pymongo import MongoClient
import pytz

from helpers.db_manager import format_dtstring, check_guild_member, user_leave 
from constants import DBNAME, TIMEZONE

db_client = MongoClient(os.getenv("mongodb_url"))
db = db_client[DBNAME]
tz = pytz.timezone(TIMEZONE)

test_guilds = [779451772573450281]
class VCTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(
        name="vcrank",
        description="Display the ranking of each member based on VC activity.",
        options=[
            create_option(name="by", description="What you want to rank each member by.",option_type=3, required=True,
            choices=[
                create_choice(name="Total Time Spent", value="total"),
                create_choice(name="Longest Continuous Time Spent", value="long")
            ])
        ])
    async def _vcrank(self, ctx: SlashContext, by: str):
        print(by)
        try:
            collection = db[str(ctx.guild.id)]
        except:
            await ctx.send(f"no activity found in **{ctx.guild.name}**.")
            return

        title = ":trophy: Longest Periods Spent in VC" if by == "long" else ":bar_chart: Total Time in VC"
        category = "longestvctime" if by == "long" else "totalvctime"
        sorted_users = sorted(list(collection.find({}, {"_id": 1,category:1})), key=lambda items: items[category], reverse=True)
        embed = discord.Embed(
            title=f"{title} ({ctx.guild.name})", 
            color=0xf02dd0
        )
        embed.set_thumbnail(url=ctx.guild.icon_url)
        pos = 0
        for user in sorted_users:
            if pos <= 8: 
                this_user = await self.bot.fetch_user(user["_id"])
                user_time = user[category]
                if user_time != "1900-01-01 00:00:00.01":
                    embed.add_field(
                        name=f"{str(pos+1)}. {this_user.display_name}", 
                        value=await format_dtstring(user_time),
                        inline=False
                    )
                    pos += 1
            else:
                break
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="stats", description="Display your VC data for this guild.")
    async def _stats(self, ctx: SlashContext):
        collection = db[str(ctx.guild.id)]
        if await check_guild_member(ctx.author):
            first_joined = collection.find_one({"_id": ctx.author.id})["firstjoined"]
            embed = discord.Embed(title=f":bar_chart: {ctx.author.name}'s stats ({ctx.guild.name})", color=0x8088ff)
            embed.set_thumbnail(url=ctx.author.avatar_url)
            embed.set_footer(text=f"(taken since {datetime.strptime(first_joined, '%Y-%m-%d %H:%M:%S.%f').date()})")
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
        else:
            await ctx.send(f"no activity found for **{ctx.author.name}**.")
    
    """
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot: return
        #user joins
        if not before.channel and after.channel and not after.afk:
            print(f"{member.name} joins {member.guild.name}")
            await check_guild_member(member)
            collection = db[str(member.guild.id)]
            collection.update_one({"_id": member.id}, {"$set":{"lastjoined": str(datetime.now(self.tz).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S.%f"))}}) 

            first_joined = collection.find_one({"_id": member.id})["firstjoined"]
            if first_joined == "":
                collection.update_one({"_id": member.id}, {"$set":{"firstjoined": str(datetime.now(self.tz).replace(tzinfo=None))}})

        #user leaves
        elif not after.channel and before.channel and not before.afk:
            print(f"{member.name} leaves {member.guild.name}")
            await check_guild_member(member)
            collection = db[str(member.guild.id)]
            user = collection.find_one({"_id": member.id})
            await user_leave(user, db[str(member.guild.id)])
    """
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