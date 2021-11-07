import os
import asyncio
from datetime import datetime, timedelta, time

import discord
from pymongo import MongoClient
import pytz

from constants import DBNAME, TIMEZONE

db_client = MongoClient(os.getenv("mongodb_url"))
db = db_client[DBNAME]

WHEN = time(8, 0, 0)
dt_offset = datetime(1900, 1, 1)
tz = pytz.timezone(TIMEZONE)

async def format_dtstring(str):
    date_time = datetime.strptime(str,"%Y-%m-%d %H:%M:%S.%f")
    delta_t = date_time - dt_offset
    s = delta_t.total_seconds()
    return "`{}h {}m {}s`".format(
        int(s //3600), 
        int((s % 3600) // 60), 
        int(s % 60)
    )

# returns true if user's profile and guild already exist
async def check_guild_member(member, guildid = None):
    if not guildid: guildid = member.guild.id 
    guild_collection = None
    if str(guildid) in db.list_collection_names():
        guild_collection = db[str(guildid)]
        if guild_collection.count_documents({ '_id': member.id }, limit = 1) != 0:
            return True
    else:
        guild_collection = db.create_collection(str(guildid))
        print("creating guild collection")
    if not guild_collection.count_documents({ '_id': member.id }, limit = 1) != 0:  
        print("creating user post")
        post = {
            "_id": member.id, 
            "name": member.name, 
            "totalvctime": "1900-01-01 00:00:00.01",
            "longestvctime": "1900-01-01 00:00:00.01",
            "lastjoined": "",
            "firstjoined": "",
            "birthday": ""
        }
        guild_collection.insert_one(post)
    return False

async def user_leave(user, collection):
  now = datetime.now(tz).replace(tzinfo=None)
  t_delta = now-datetime.strptime(collection.find_one({"_id": user["_id"]})["lastjoined"], "%Y-%m-%d %H:%M:%S.%f")

  # returns if user has yet to join 
  if collection.find_one({"_id": user["_id"]})["lastjoined"] == "": return

  # updates longest vc time 
  if t_delta+dt_offset > datetime.strptime(user["longestvctime"], "%Y-%m-%d %H:%M:%S.%f"):
    collection.update_one({ "_id": user["_id"]}, { "$set": { "longestvctime":str(t_delta+dt_offset) } })

  # adds t_delta to total and resets last joined
  collection.update_one({ "_id": user["_id"]}, { "$set": { "totalvctime": str(datetime.strptime(user["totalvctime"], "%Y-%m-%d %H:%M:%S.%f") + t_delta) } })
  collection.update_one({ "_id": user["_id"]}, { "$set": { "lastjoined": "" } })

async def daily_check(bot):
  print(f"({(datetime.now(tz))}) running daily check")
  for name in db.list_collection_names():
    collection = db[name]
    if collection == None:
      continue
    for user in collection.find():
      try:
        if datetime.strptime(user["birthday"], '%m/%d/%Y').replace(year=2000) == datetime(2000, datetime.today().month, datetime.today().day):
          print(f"today is the birthday of {user['name']}")
          try:
            await bot.wait_until_ready()
            guild = bot.get_guild(int(name))
            channel = discord.utils.get(guild.channels, name="general")
            embed = discord.Embed(
              title=f":birthday: Happy Birthday, {user['name']}! :birthday: ", 
              color=0xfff700,
              description="Everybody say your Happy Birthdays to <@{}>! Today is {}.".format(user["_id"], datetime.now(tz).date())
            )
            await channel.send(embed=embed)
          except AttributeError:
              pass
      except ValueError:
          pass

async def background_task():
    now = datetime.utcnow()
    if now.time() > WHEN:  # Make sure loop doesn't start after {WHEN} as then it will send immediately the first time as negative seconds will make the sleep yield instantly
        tomorrow = datetime.combine(now.date() + timedelta(days=1), time(0))
        seconds = (tomorrow - now).total_seconds()  # Seconds until tomorrow (midnight)
        print(f'({datetime.now(tz).replace(tzinfo=None)}) waiting for utc midnight ({seconds/60} minutes from now) before starting loop')
        await asyncio.sleep(seconds)   # Sleep until tomorrow and then the loop will start 
    while True:
        now = datetime.utcnow()
        target_time = datetime.combine(now.date(), WHEN)
        seconds_until_target = (target_time - now).total_seconds()
        print(f'({datetime.now(tz).replace(tzinfo=None)}) starting task in {seconds_until_target/60} minutes')
        await asyncio.sleep(seconds_until_target)  # Sleep until we hit the target time
        await daily_check()  

        tomorrow = datetime.combine(now.date() + timedelta(days=1), time(0))
        seconds = (tomorrow - now).total_seconds()  # Seconds until tomorrow (midnight)
        print(f"({datetime.now(tz).replace(tzinfo=None)}) tasks completed, sleeping for {seconds/60} minutes")
        await asyncio.sleep(seconds)   # Sleep until tomorrow and then the loop will start a new iteration
