from datetime import datetime

from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option

from helpers.db_models import DBGuild, DBMember
from utils.mongo import check_bdays, dtstr_to_dt
from utils.displays import build_embed
from constants import TZ


class BDayTracker(commands.Cog, name="BDay tracker"):
    def __init__(self, bot):
        self.bot = bot
    
    # checks for birthdays every day
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.loop.create_task(check_bdays(self.bot))
        
    @cog_ext.cog_slash(
        name="setbday",
        description="Set the date of your birthday for a special message on that day. (Note: CANNOT be changed again)",
        options=[
            create_option(name="year", description="The year of your birthday.",option_type=4, required=True),
            create_option(name="month", description="The month of your birthday.",option_type=4, required=True),
            create_option(name="day", description="The day of your birthday.",option_type=4, required=True)
        ])
    async def _setbday(self, ctx: SlashContext, year: int, month: int, day: int):
        date = f"{month}/{day}/{year}"
        try: #verfies user has sent a date
            birthday_dt = dtstr_to_dt(date)
    
            # date can't be in the future
            if datetime.now(TZ).replace(tzinfo=None) < birthday_dt:
                raise ValueError
        except ValueError:
            await ctx.reply(f"'{date}' is not a valid date.", hidden=True)
            return

        db_member = DBMember.from_member(ctx.author)
        bday = db_member.get_value("birthday")
        if bday == "":
            db_member.update_field("birthday", date)
            await ctx.reply(f"Your birthday has successfully been set to: {date}", hidden=True)
        else: 
            await ctx.reply(f"Your birthday has already been set to: **{bday}**", hidden=True)   

    @cog_ext.cog_slash(
        name="upcomingbdays", 
        description="Displays known upcoming birthdays within the next two weeks."
    )
    async def _upcomingbdays(self, ctx: SlashContext):
        db_guild = DBGuild(ctx.guild_id)
        members = db_guild.get_sorted_values("birthday")

        description = ""
        for member in members:
            date = member["birthday"]
            if date != "":
                birthday = datetime.strptime(date, '%m/%d/%Y')
                now = datetime.now(TZ).replace(tzinfo=None)
                bday = datetime(now.year, birthday.month, birthday.day)
                days_away = (bday - now.today()).days-1
                days_range = 14
                if days_away in range(-364, -364 + days_range) or days_away in range(days_range):
                    description += f"\n- **{member['name']}**'s birthday is on **{date}**)"

        await ctx.reply(embed=build_embed(
            title=f":birthday: Upcoming Birthdays in '{ctx.guild.name}' :birthday:", 
            desc=description
        ))

def setup(bot):
    bot.add_cog(BDayTracker(bot))