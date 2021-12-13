import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext, manage_commands
from discord_slash.utils.manage_commands import create_option, create_choice
import youtube_dl
from youtube_dl.utils import DownloadError

test_guilds = [779451772573450281]

class Interactivity(commands.Cog, name="interactivity"):
    def __init__(self, bot):
        self.bot = bot
        self.ydl = youtube_dl.YoutubeDL()
    
    @commands.command(description="helps you set up a poll")
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

    @cog_ext.cog_slash(
        name="ytlink",
        description="Sends you links to easily download your favourite YouTube videos. (audio and MP4)",
        guild_ids=test_guilds,
        options=[
            create_option(name="link", description="A YouTube video URL.", option_type=3, required=True),
        ])
    async def _ytlink(self, ctx: SlashContext, link):
        if not ("/playlist?list=" in link or "list="  and "/watch" in link):
            try:
                r = self.ydl.extract_info(link, download=False)
            except DownloadError:
                await ctx.reply(f'"{link}" is not a valid URL.')
                return
            urls = [format['url'] for format in r['formats']]
            embed = discord.Embed(title=f"Download links for: {r['title']}")
            embed.set_thumbnail(url=r["thumbnail"])
            embed.add_field(name=f"Download MP4:", value=f"[link here]({urls[-1]})")
            embed.add_field(name=f"Download Audio:", value=f"[link here]({urls[3]})")
            await ctx.author.send(embed=embed)
        else:
            await ctx.reply("Playlists not allowed.")

def setup(bot):
    bot.add_cog(Interactivity(bot))
