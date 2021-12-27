import discord


def build_embed(title, desc="", img_url=None, thumb_url=None):
    embed = discord.Embed(
        title = title,
        description = desc,
        colour = discord.Colour.random()
    )
    if img_url:
        embed.set_image(url=img_url)
    if thumb_url:
        embed.set_thumbnail(url=thumb_url)
    return embed