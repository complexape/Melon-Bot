from discord.ext import commands
import bson

from helpers.db_models import DBGuild, DocNotFoundError
from utils.mongo import vc_leave
from utils.mongo import build_embed
from constants import DB


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    # force leaves all users to prepare for any downtime
    @commands.command(hidden = True)
    async def forceleaveall(self, ctx):
        leavers = []
        for id in DB.list_collection_names():
            collection = DBGuild(id)
            vcing_members = collection.get_all_members({"lastjoined": {"$ne": ""}})
            for db_member in vcing_members:
                    await vc_leave(db_member)
                    leavers.append(db_member.name)
        await ctx.author.send(embed=build_embed(
            title="Bot can now be stopped.",
            desc=f"**{len(leavers)}** member(s) forced to leave: \n{leavers}",
        ))

    @commands.command(hidden = True)
    async def clearthisguild(self, ctx):
        if str(ctx.guild.id) in DB.list_collection_names():
            DB[str(ctx.guild.id)].drop()
            await ctx.author.send(f"`all data for '{ctx.guild.name}' has been cleared.`")
        else:
            await ctx.author.send("`data for this guild does not exist.`")

    @commands.command(hidden = True)
    async def clearmember(self, ctx, *, id):
        try:
            db_guild = DBGuild(ctx.guild.id)
            db_guild.delete_member(id)
            await ctx.author.send(f"`all data for user_id: '{id}' in '{ctx.guild.name}' cleared.`")
        except DocNotFoundError:
            await ctx.author.send("`id does not exist in this guild.`")

    @commands.command(hidden=True)
    async def fetchdoc(self, ctx, *, id):
        for guild_id in DB.list_collection_names():
            collection = DBGuild(guild_id)
            guild = self.bot.get_guild(int(collection.id))
            for db_member in collection.get_all_members({"_id": bson.Int64(id)}):
                await ctx.author.send(embed=build_embed(
                    title=f"Document found (in {guild.name})",
                    desc=f"`{db_member.doc}`"
                ))

def setup(bot):
    bot.add_cog(Admin(bot))