from datetime import datetime, time, timedelta
import asyncio
import discord

from helpers.guild import DBGuild
from helpers.member import DBMember
from constants import DB, TZ, ZERODATE

def str_to_dt(string):
  return datetime.strptime(string , "%Y-%m-%d %H:%M:%S.%f")

# time in the database are saved as dates starting from 1900-1-1,
# an offset must be applied to help compensate for this
DATE_OFFSET = str_to_dt(ZERODATE)

def format_time_str(dt_str, to_date=False):
  if to_date:
    return f"`{str(str_to_dt(dt_str).date())}`"
  else:
    s = (str_to_dt(dt_str) - DATE_OFFSET).total_seconds()
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
    duration = now - str_to_dt(last_joined)

    # checks if duration spent is the most the user has spent
    longest_vc_time = str_to_dt(member.get_value("longestvctime"))
    if (DATE_OFFSET + duration) > longest_vc_time:
      member.update_field("longestvctime", str(DATE_OFFSET + duration))

    # adds duration to total time spent in vc and resets last joined entry
    member.update_field("totalvctime", str(str_to_dt(member.get_value("totalvctime")) + duration))
    member.update_field("lastjoined")

async def check_bdays(bot):
  print(f"({(datetime.now(TZ))}) running daily check")
  for id in DB.list_collection_names():
    collection = DBGuild(id)
    if collection:
      for db_member in collection.get_all_members():
        now = datetime.today()
        date = db_member.get_value("birthday")
        if date != "":
          bday = datetime.strptime(date, '%m/%d/%Y')
          if bday == datetime(bday.year, now.month, now.day):
            print(f"today is the birthday of {db_member.name}")
            try:
              await bot.wait_until_ready()
              guild = bot.get_guild(int(id))
              channel = discord.utils.get(guild.channels, name="general")
              await channel.send(embed=discord.Embed(
                title=f":birthday: Happy Birthday, {db_member.name}! :birthday: ", 
                color=0xfff700,
                description=f"Everybody say your Happy Birthdays to <@{db_member.id}>! Today is {datetime.now(TZ).date()}."
              ))
            except AttributeError:
                pass

async def background_task():
    WHEN = time(8, 0, 0)
    now = datetime.utcnow()
    if now.time() > WHEN:  # Make sure loop doesn't start after {WHEN} as then it will send immediately the first time as negative seconds will make the sleep yield instantly
        tomorrow = datetime.combine(now.date() + timedelta(days=1), time(0))
        seconds = (tomorrow - now).total_seconds()  # Seconds until tomorrow (midnight)
        print(f'({datetime.now(TZ).replace(tzinfo=None)}) waiting for utc midnight ({seconds/60} minutes from now) before starting loop')
        await asyncio.sleep(seconds)   # Sleep until tomorrow and then the loop will start 
    while True:
        now = datetime.utcnow()
        target_time = datetime.combine(now.date(), WHEN)
        seconds_until_target = (target_time - now).total_seconds()
        print(f'({datetime.now(TZ).replace(tzinfo=None)}) starting task in {seconds_until_target/60} minutes')
        await asyncio.sleep(seconds_until_target)  # Sleep until we hit the target time
        await check_bdays()

        tomorrow = datetime.combine(now.date() + timedelta(days=1), time(0))
        seconds = (tomorrow - now).total_seconds()  # Seconds until tomorrow (midnight)
        print(f"({datetime.now(TZ).replace(tzinfo=None)}) tasks completed, sleeping for {seconds/60} minutes")
        await asyncio.sleep(seconds)   # Sleep until tomorrow and then the loop will start a new iteration