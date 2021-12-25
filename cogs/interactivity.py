import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option
import youtube_dl
from youtube_dl.utils import DownloadError

from utils.displays import build_embed


class Interactivity(commands.Cog, name="interactivity"):
    def __init__(self, bot):
        self.bot = bot
        self.ydl = youtube_dl.YoutubeDL()
    
    @cog_ext.cog_slash(
        name="poll",
        description="Create a poll embed for members to vote for in this server.",
        options=[
            create_option(name="title", description="Your poll embed's title.", option_type=3, required=True),
            create_option(name="channel", description="The channel you want your poll embed to be posted in.",option_type=7, required=True),
            create_option(name="image", description="A URL for an image.", option_type=3, required=False)
        ])
    async def _poll(self, ctx: SlashContext, title: str, channel: discord.channel, image: str = None):
        embed = build_embed(title=title)
        try:
            embed.set_image(url=image)
            if isinstance(channel, discord.TextChannel):
                message = await channel.send(embed=embed)
                await message.add_reaction("👍")
                await message.add_reaction("👎")
                await ctx.reply("Success!", hidden=True)
            else:
                await ctx.reply("Your channel must be a text channel.", hidden=True)
        except discord.errors.HTTPException:
            await ctx.reply(f"'{image}' is not a valid URL.", hidden=True)
            return

    @cog_ext.cog_slash(
        name="ytlink",
        description="Sends you links to easily download your favourite YouTube videos. (audio and MP4)",
        options=[
            create_option(name="link", description="A YouTube video URL.", option_type=3, required=True),
        ])
    async def _ytlink(self, ctx: SlashContext, link):
        if not ("/playlist?list=" in link or "list="  and "/watch" in link):
            try:
                r = self.ydl.extract_info(link, download=False)
            except DownloadError:
                await ctx.reply(f'"{link}" is not valid.', hidden=True)
                return

            urls = [format['url'] for format in r['formats']]
            embed = build_embed(title=f"Download links for: {r['title']}", thumb_url=r["thumbnail"])
            embed.add_field(name=f"Download MP4:", value=f"[link here]({urls[-1]})")
            embed.add_field(name=f"Download Audio:", value=f"[link here]({urls[3]})")
            await ctx.author.send(embed=embed)
        else:
            await ctx.reply("Playlists are not allowed.", hidden=True)

def setup(bot):
    bot.add_cog(Interactivity(bot))
