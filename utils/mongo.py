from datetime import datetime, time, timedelta
import asyncio
import discord

from helpers.db_models import DBGuild, DBMember
from utils.displays import build_embed
from constants import BDAY_CHECK, DB, TZ, ZERODATE

def parse_duration(datetime):
    s = (datetime - ZERODATE).total_seconds()
    return f"{int(s //3600)}h {int((s % 3600) // 60)}m {int(s % 60)}s"

async def vc_join(member: DBMember):
    now = datetime.now(TZ).replace(tzinfo=None)

    # converts time to string, then adds it to the database
    member.update_field("lastjoined", now)

    if not member.get("firstjoined"):
        member.update_field("firstjoined", now)

async def vc_leave(member: DBMember):
    now = datetime.now(TZ).replace(tzinfo=None)
    last_joined = member.get("lastjoined", as_dt=True)

    # only works if user had previously joined
    if last_joined:
        duration = now - last_joined

        # checks if duration spent is the most the user has spent
        longest_vc_time = member.get("longestvctime", as_dt=True)
        if (ZERODATE + duration) > longest_vc_time:
            member.update_field("longestvctime", str(ZERODATE + duration))

        # adds the elapsed duration to total time spent in vc and resets last joined
        member.update_field("totalvctime", str(member.get("totalvctime", as_dt=True) + duration))
        member.update_field("lastjoined")

def daily_task(WHEN: time):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            name = func.__name__
            # make sure loop doesn't start after the target time as then
            # it will immediately send the first time as negative seconds will make the sleep yield instantly
            now = datetime.utcnow()
            if now.time() > WHEN: 
                tomorrow = datetime.combine(now.date() + timedelta(days=1), time(0))
                seconds = (tomorrow - now).total_seconds()  # Seconds until tomorrow (midnight)
                print(f'({datetime.now(TZ).time()})({name}) waiting for UTC midnight ({round(seconds/3600, 2)} hours from now) before starting loop')

                await asyncio.sleep(seconds) # sleep until tomorrow and then the start the loop

            while True:
                now = datetime.utcnow()
                target_time = datetime.combine(now.date(), WHEN)
                seconds_until_target = (target_time - now).total_seconds()
                print(f'({datetime.now(TZ).time()})({name}) starting task in {round(seconds_until_target/3600, 2)} hours')
                # Sleep until we hit the target time
                await asyncio.sleep(seconds_until_target)  
                
                await func(*args, **kwargs) # the task

                tomorrow = datetime.combine(now.date() + timedelta(days=1), time(0))
                seconds = (tomorrow - now).total_seconds()  # Seconds until tomorrow (midnight)
                print(f"({datetime.now(TZ).time()})({name}) task completed, sleeping for {round(seconds/3600, 2)} hours")

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

@daily_task(BDAY_CHECK)
async def check_bdays(bot):
    for id in DB.list_collection_names():
        collection = DBGuild(id)
        for db_member in collection.get_all_members({"birthday": {"$ne": ""}}):
                now = datetime.now(TZ).date()
                bday = db_member.get("birthday", as_dt=True).date()

                # checks if both the month and day are the same
                if (bday.month, bday.day) == (now.month, now.day):
                    try:
                        await bot.wait_until_ready()
                        guild = bot.get_guild(int(id))
                        channel = discord.utils.get(guild.channels, name="general")

                        await channel.send(embed=build_embed(
                            title=f":birthday: Happy Birthday, {db_member.name}! :birthday: ",
                            desc=f"Everybody say your Happy Birthdays to <@{db_member.id}>! Today is **{bday.strftime('%B %d')}**."
                        ))
                    except AttributeError:
                        pass