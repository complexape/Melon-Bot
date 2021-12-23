import discord
from discord.ext import commands

from helpers.guild import DBGuild, DocNotFoundError
from utils.mongo import vc_leave
from constants import ZERODATE, DB

test_guilds = [779451772573450281, 923427919299235870]

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # force leaves all users to prepare for any downtime
    @commands.command(hidden = True)
    @commands.is_owner()
    async def forceleaveall(self, ctx):
        leavers = []
        for id in DB.list_collection_names():
            collection = DBGuild(id)
            for db_member in collection.get_all_members():
                if db_member.get_value("lastjoined") != "":
                    await vc_leave(db_member)
                    leavers.append(db_member.name)
        await ctx.author.send(embed=discord.Embed(
            title="Bot can now be stopped.",
            description=f"**{len(leavers)}** member(s) forced to leave: \n{leavers}",
            colour=0xfa0000
        ))

    @commands.command(hidden = True)
    @commands.is_owner()
    async def clearthisguild(self, ctx):
        if str(ctx.guild.id) in DB.list_collection_names():
            DB[str(ctx.guild.id)].drop()
            await ctx.send(f"`all data for '{ctx.guild.name}' has been cleared.`")
        else:
            await ctx.send("`data for this guild does not exist.`")

    @commands.command(hidden = True)
    @commands.is_owner()
    async def clearmember(self, ctx, *, id):
        try:
            db_guild = DBGuild(ctx.guild.id)
            db_guild.delete_member(id)
            await ctx.send(f"`all data for user_id: '{id}' in '{ctx.guild.name}' cleared.`")
        except DocNotFoundError:
            await ctx.send("`id does not exist in this guild.`")

def setup(bot):
    bot.add_cog(Admin(bot))