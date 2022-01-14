import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option, create_choice

from helpers.db_models import DBGuild, DBMember
from utils.mongo import vc_join, vc_leave, parse_duration
from utils.displays import build_embed

class VCTracker(commands.Cog):
    def __init__(self, bot: discord.Client):
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
        option = {
            "total": ["totalvctime", ":bar_chart: Total Time in VC", True],
            "long": ["longestvctime", ":trophy: Longest Periods Spent in VC", True],
            "first": ["firstjoined", ":frog: First Time Joining a VC", False]
        }[by]
        db_guild = DBGuild(ctx.guild_id)

        if not db_guild.is_new:
            embed = build_embed(title=f"{option[1]} ({ctx.guild.name})", thumb_url=ctx.guild.icon_url, has_time=True)
            key = option[0]
            # gets and sorts the target fields for every user in the guild
            for member in db_guild.get_sorted_values(key, is_reverse=option[2]):
                if len(embed.fields) > 6:
                    break
                elif len(embed.fields) == 0:
                    user = await self.bot.fetch_user(int(member["_id"]))
                    embed.set_thumbnail(url=user.avatar_url)
                dt = DBMember.value_as_datetime(member[key])
                value = dt.date() if by == "first" else parse_duration(dt)
                embed.add_field(name=member["name"], value=f"`{value}`", inline=False)
            await ctx.reply(embed=embed)
        else:
            await ctx.reply(f"No VC activity detected in **{ctx.guild_id}**.", hidden=True)

    @cog_ext.cog_slash(name="stats", description="Display your VC data for this guild.")
    async def _stats(self, ctx: SlashContext):
        db_member = DBMember.from_new(ctx.author)
        first_joined = db_member.get("firstjoined", as_dt=True)

        if not db_member.is_new() and first_joined:
            embed = build_embed(title=f":bar_chart: {ctx.author.name}'s stats ({ctx.guild.name})", thumb_url=ctx.author.avatar_url)
            embed.set_footer(text=f"(taken since {first_joined.date()})")
            embed.add_field(name="Total Time in VC:", value=f"`{parse_duration(db_member.get('totalvctime', as_dt=True))}`")
            embed.add_field(name="Longest Time Spent in VC:", value=f"`{parse_duration(db_member.get('longestvctime', as_dt=True))}`")
            await ctx.reply(embed=embed)
        else:
            await ctx.reply(f"No VC activity detected from **{ctx.author.name}**.", hidden=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot:
            db_member = DBMember.from_new(member)

            if not before.channel and after.channel and not after.afk:
                print(f"{member.name} joins {member.guild.name}")
                await vc_join(db_member)

            elif not after.channel and before.channel and not before.afk:
                print(f"{member.name} leaves {member.guild.name}")
                await vc_leave(db_member)

def setup(bot):
    bot.add_cog(VCTracker(bot))