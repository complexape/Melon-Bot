import os
from keep_alive import keep_alive

import discord
from discord.ext.commands import Bot

intents = discord.Intents.default()

bot = Bot(command_prefix=os.getenv("prefix"))

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
            

@bot.event
async def on_command_error(context, error):
    raise error

keep_alive()
bot.run(os.getenv("bot_token"))
