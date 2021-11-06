import os
from keep_alive import keep_alive

import discord
from discord.ext.commands import Bot

#remove these when migrating to repl.it 
os.environ["mongodb_url"] = "mongodb+srv://Gordon_Z:Qwertyo123@cluster0.1991g.mongodb.net/discord?retryWrites=true&w=majority"
os.environ["bot_token"] = "NzI0NzQ4NTgwNjM1NTQxNTk3.XvEstg.N_tZ-m3MMppAxpz_obfHQIXgxFk"
os.environ["prefix"] = "m!"

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