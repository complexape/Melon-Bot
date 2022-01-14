import discord

from constants import TZ

def build_embed(title, desc="", img_url=None, thumb_url=None, has_time=False):
    embed = discord.Embed(
        title = title,
        description = desc,
        colour = discord.Colour.random()
    )
    if img_url:
        embed.set_image(url=img_url)
    if thumb_url:
        embed.set_thumbnail(url=thumb_url)
    if has_time:
        embed.set_footer(text=f"(Note: Dates are in {TZ.zone})")
    return embed