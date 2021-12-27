from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option, create_choice

from helpers.db_models import DBGuild, DBMember
from utils.mongo import format_time_str, vc_join, vc_leave, dtstr_to_date
from utils.displays import build_embed
from constants import ZERODATE


class VCTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(
        name="vcrank",
        description="Displays the ranking of each member based on VC activity.",
        options=[
            create_option(name="by", description="What you want to rank each member by.",option_type=3, required=True,
            choices=[
                create_choice(name="Total Time Spent", value="total"),
                create_choice(name="Longest Continuous Time Spent", value="long"),
                create_choice(name="First Joined", value="first")
            ])
        ])
    async def _vcrank(self, ctx: SlashContext, by: str):
        choices = {
            "total": ["totalvctime", ":trophy: Longest Periods Spent in VC", False, True],
            "long": ["longestvctime", ":bar_chart: Total Time in VC", False, True],
            "first": ["firstjoined", ":frog: First Time Joining a VC", True, False]
        }
        db_guild = DBGuild(ctx.guild_id)

        if not db_guild.is_new:
            choice = choices[by]
            key = choice[0]
            embed = build_embed(title=f"{choice[1]} ({ctx.guild.name})", thumb_url=ctx.guild.icon_url)

            # gets and sorts the target fields for every user in the guild
            pos = 0
            for user in db_guild.get_sorted_values(key, is_reverse=choice[3]):
                if pos <= 6 and user[key] not in [ZERODATE, ""]:
                    embed.add_field(name=user["name"], value=format_time_str(user[key], to_date=choice[2]), inline=False)
                    pos += 1
            await ctx.reply(embed=embed)
        else:
            await ctx.reply(f"No VC activity detected in **{ctx.guild_id}**.", hidden=True)

    @cog_ext.cog_slash(name="stats", description="Display your VC data for this guild.")
    async def _stats(self, ctx: SlashContext):
        db_guild = DBGuild(ctx.author.guild.id)
        db_member = DBMember(ctx.author_id, ctx.author.name, db_guild.collection)

        if not db_member.is_new and db_member.get_value("firstjoined") != "":
            embed = build_embed(title=f":bar_chart: {ctx.author.name}'s stats ({ctx.guild.name})", thumb_url=ctx.author.avatar_url)
            embed.set_footer(text=f"(taken since {dtstr_to_date(db_member.get_value('firstjoined'))})")
            embed.add_field(name="Total Time in VC:", value=format_time_str(db_member.get_value("totalvctime")))
            embed.add_field(name="Longest Time Spent in VC:", value=format_time_str(db_member.get_value("longestvctime")))
            await ctx.reply(embed=embed)
        else:
            await ctx.reply(f"No VC activity detected from **{ctx.author.name}**.", hidden=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot:
            db_guild = DBGuild(member.guild.id)
            db_member = DBMember(member.id, member.name, db_guild.collection)

            if not before.channel and after.channel and not after.afk:
                print(f"{member.name} joins {member.guild.name}")
                await vc_join(db_member)

            elif not after.channel and before.channel and not before.afk:
                print(f"{member.name} leaves {member.guild.name}")
                await vc_leave(db_member)

def setup(bot):
    bot.add_cog(VCTracker(bot))