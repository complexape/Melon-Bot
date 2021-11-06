import discord
from discord.ext import commands

from helpers.input_helpers import *


class Interactivity(commands.Cog, name="interactivity"):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def vote(self, ctx):
        def check(msg):
            return msg.author.id == ctx.author.id and msg.channel.id == ctx.channel.id
        def check_img(msg):
            return check and 'https://cdn.discordapp.com/attachments/' in msg.content or msg.content == "NO"

        q1 = await ctx.send("What is your voting question/statement?: ")
        title = await self.bot.wait_for('message', check=check, timeout=300)
        q2 = await ctx.send("What's your image (discord urls only)? (type 'NO' for none): ")
        img = await self.bot.wait_for('message', check=check_img, timeout=300)

        embed = discord.Embed(
            title=title.content, 
            color=0xff0066,
        )
        if img.content != "NO": embed.set_image(url=img.content)
    
        await ctx.channel.delete_messages([q1, q2, title, img])
        message = await ctx.send(embed=embed)
        await message.add_reaction("👍")
        await message.add_reaction("👎")

def setup(bot):
    bot.add_cog(Interactivity(bot))