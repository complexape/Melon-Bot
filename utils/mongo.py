from datetime import datetime, time, timedelta
import asyncio
import discord

from helpers.db_models import DBGuild, DBMember
from utils.displays import build_embed
from constants import DB, TZ, ZERODATE

def dtstr_to_dt(string):
    try:
        return datetime.strptime(string , "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return datetime.strptime(string , "%m/%d/%Y")
        
def dtstr_to_date(string):
    return dtstr_to_dt(string).date()

# time in the database are saved as dates starting from 1900-1-1,
# an offset must be applied to help compensate for this
DATE_OFFSET = dtstr_to_dt(ZERODATE)

def format_time_str(dt_str, to_date=False):
    if to_date:
        return f"`{str(dtstr_to_date(dt_str))}`"
    else:
        s = (dtstr_to_dt(dt_str) - DATE_OFFSET).total_seconds()
        return f"`{int(s //3600)}h {int((s % 3600) // 60)}m {int(s % 60)}s`"

async def vc_join(member: DBMember):
    now = datetime.now(TZ).replace(tzinfo=None)

    # converts time to string, then adds it to the database
    member.update_field("lastjoined", str(now.strftime("%Y-%m-%d %H:%M:%S.%f")))

    if member.get_value("firstjoined") == "":
        member.update_field("firstjoined", str(now))

async def vc_leave(member: DBMember):
    now = datetime.now(TZ).replace(tzinfo=None)
    last_joined = member.get_value("lastjoined")
    # counts duration only if user has a recorded join time
    if last_joined != "":
        duration = now - dtstr_to_dt(last_joined)

        # checks if duration spent is the most the user has spent
        longest_vc_time = dtstr_to_dt(member.get_value("longestvctime"))
        if (DATE_OFFSET + duration) > longest_vc_time:
            member.update_field("longestvctime", str(DATE_OFFSET + duration))

        # adds duration to total time spent in vc and resets last joined entry
        member.update_field("totalvctime", str(dtstr_to_dt(member.get_value("totalvctime")) + duration))
        member.update_field("lastjoined")

def daily_task(WHEN):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # make sure loop doesn't start after the target time as then
            # it will immediately send the first time as negative seconds will make the sleep yield instantly
            now = datetime.utcnow()
            if now.time() > WHEN: 
                tomorrow = datetime.combine(now.date() + timedelta(days=1), time(0))
                seconds = (tomorrow - now).total_seconds()  # Seconds until tomorrow (midnight)
                print(f'({datetime.now(TZ).replace(tzinfo=None)}) waiting for UTC midnight ({seconds/3600} hours from now) before starting loop')

                await asyncio.sleep(seconds) # sleep until tomorrow and then the start the loop

            while True:
                now = datetime.utcnow()
                target_time = datetime.combine(now.date(), WHEN)
                seconds_until_target = (target_time - now).total_seconds()
                print(f'({datetime.now(TZ).replace(tzinfo=None)}) starting task in {seconds_until_target/3600} hours')
                # Sleep until we hit the target time
                await asyncio.sleep(seconds_until_target)  
                
                await func(*args, **kwargs) # the task

                tomorrow = datetime.combine(now.date() + timedelta(days=1), time(0))
                seconds = (tomorrow - now).total_seconds()  # Seconds until tomorrow (midnight)
                print(f"({datetime.now(TZ).replace(tzinfo=None)}) task completed, sleeping for {seconds/60} minutes")

                # Sleep until tomorrow and then the loop will start a new iteration
                await asyncio.sleep(seconds)
        return wrapper
    return decorator

async def leave_all():
    leavers = []
    for id in DB.list_collection_names():
        collection = DBGuild(id)
        vcing_members = collection.get_all_members({"lastjoined": {"$ne": ""}})
        for db_member in vcing_members:
                await vc_leave(db_member)
                leavers.append(db_member.name)
    
    return leavers

@daily_task(time(8, 0, 0))
async def check_bdays(bot):
    await bot.AppInfo.owner.send(f"({(datetime.now(TZ))}) running birthday check now.")
    for id in DB.list_collection_names():
        collection = DBGuild(id)
        for db_member in collection.get_all_members({"birthday": {"$ne": ""}}):
                now = datetime.today()
                bday = dtstr_to_date(db_member.get_value("birthday"))
                if bday == datetime(bday.year, now.month, now.day).date():
                    try:
                        await bot.wait_until_ready()
                        guild = bot.get_guild(int(id))
                        channel = discord.utils.get(guild.channels, name="general")
                        date = bday.strftime("%B %d")

                        await channel.send(embed=build_embed(
                            title=f":birthday: Happy Birthday, {db_member.name}! :birthday: ",
                            desc=f"Everybody say your Happy Birthdays to <@{db_member.id}>! Today is **{date}**."
                        ))
                    except AttributeError:
                        pass