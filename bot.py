import os

import discord
from discord.ext import commands
from discord_slash import SlashCommand

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=os.getenv("prefix"))
slash = SlashCommand(bot, sync_commands=True)

@bot.event
async def on_command_error(context, error):
    raise error

@bot.event
async def on_ready():
    if not hasattr(bot, 'AppInfo'):
        bot.AppInfo = await bot.application_info()
    print(f'{bot.user} has logged in.')

if __name__ == "__main__":
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            extension = file[:-3]
            try:
                bot.load_extension(f"cogs.{extension}")
                print(f"Loaded extension '{extension}'")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                print(f"Failed to load extension {extension}\n{exception}")

bot.run(os.getenv("bot_token"))
