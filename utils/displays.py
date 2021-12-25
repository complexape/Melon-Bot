from datetime import datetime
import discord


def str_to_dt(string):
    return datetime.strptime(string , "%Y-%m-%d %H:%M:%S.%f")

def str_to_date(string):
    return datetime.strptime(string , "%m/%d/%Y").date()

def build_embed(title, desc=None, img_url=None, thumb_url=None):
    embed = discord.Embed(
        title = title,
        description = "empty." if desc in [None, ""] else desc,
        colour = discord.colour.random()
    )
    if img_url:
        embed.set_image(url=img_url)
    if thumb_url:
        embed.set_thumbnail(url=thumb_url)
    return embed