import discord
from discord.ext import commands
import youtube_dl

class Interactivity(commands.Cog, name="interactivity"):
    def __init__(self, bot):
        self.bot = bot
    
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

    @commands.command(description="sends you links to easily download your favourite youtube videos (mp3 or mp4)", usage = '[youtube-url] (video you want to download)')
    async def dl(self, ctx, link):
        # checks if link is a playlist
        if "/playlist?list=" in link or "list="  and "/watch" in link:
            await ctx.send("Playlist not allowed.")
            return
        ydl = youtube_dl.YoutubeDL()
        r = ydl.extract_info(link, download=False)
        urls = [format['url'] for format in r['formats']]
        embed = discord.Embed(title=f"Download links for: {r['title']}")
        embed.set_thumbnail(url=r["thumbnail"])
        embed.add_field(name=f"Download MP4:", value=f"[link here]({urls[-1]})")
        embed.add_field(name=f"Download MP3", value=f"[link here]({urls[2]})")
        await ctx.author.send(embed=embed)



def setup(bot):
    bot.add_cog(Interactivity(bot))