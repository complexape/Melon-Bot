import os
import random
from io import BytesIO
import json

import discord
from discord.ext import commands
import pytz
from PIL import Image, ImageSequence
import requests

from helpers.input_helpers import *
from constants import TIMEZONE


tz = pytz.timezone(TIMEZONE)

class Fun(commands.Cog, name="fun"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def sauce(self, ctx, code=None):
        if not code:
            code =  f'{random.randrange(1, 350000):06}'
        elif not check_if_num(code, 6):
            return
        await ctx.send(f"||https://nhentai.to/g/{code}||")
    
    @commands.command()
    async def ohmy(self, ctx, user: discord.Member = None):
        if user == None:
            user = ctx.author

        asset = user.avatar_url_as(size=128)
        data = BytesIO(await asset.read())
        final_path = f'temp/ohmygif{user.id}.gif'
        animated_gif = Image.open("media/ohmygoodness.gif")
        img = Image.open(data).convert("RGBA").resize((220, 220), Image.ANTIALIAS)

        frames = []
        for frame in ImageSequence.Iterator(animated_gif):
            frame = frame.copy()
            final_img = Image.new('RGBA', animated_gif.size, (0, 0, 0, 0))
            final_img.paste(frame, (0,0))
            final_img.paste(img, (270,195), mask=img)
            frames.append(final_img)
        frames[0].save(final_path, save_all=True, append_images=frames[1:]) 

        await ctx.send(file=discord.File(final_path))
        os.remove(final_path)

    @commands.command()
    async def quote(self, ctx, name=None):
        with open("media\quotes.json") as f:
            data = json.load(f)

        if name == None or name.lower() not in list(data.keys()):
            name = random.choice(list(data.keys()))
        
        await ctx.send(f"'{random.choice(data[name])}'\n -{name}")
    
    @commands.command()
    async def w(self, ctx):
        response = requests.get("https://api.waifu.pics/sfw/waifu")
        await ctx.send(response.json()["url"])
        

        

def setup(bot):
    bot.add_cog(Fun(bot))