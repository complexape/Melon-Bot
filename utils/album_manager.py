from bson.objectid import ObjectId
from discord.ext.commands.help import Paginator
from discord_slash.context import MenuContext, SlashContext
import discord
from discord.ext import commands
from ButtonPaginator import Paginator

class InvalidUsageError(commands.CommandError):
    pass

class CommandCancelled(commands.CommandError):
    pass

def retrieve_post(ctx: MenuContext, album):
    if len(ctx.target_message.embeds) < 1:
        raise InvalidUsageError("No Post Embed found.")
    else:
        id = ObjectId(ctx.target_message.embeds[0].footer.text.split(' ')[1])
        post = album.collection.find_one({ "_id":  id})
        
        if not post:
            raise InvalidUsageError("No post found.")

        return post, id

async def display_post(
    bot: commands.Bot, ctx: SlashContext, post_document, 
    channel: discord.TextChannel = None, hidden = False, no_pagination = False, 
):
    # the command context member can only access this post they have the access role,
    # are the author or have the guild's manage messages permission
    if (post_document["access_role_id"] and
                post_document["access_role_id"] not in [role.id for role in ctx.author.roles] and
                post_document["author_id"] != ctx.author_id and
                not ctx.author.guild_permissions.manage_messages):
            raise InvalidUsageError("You don't have permission to do that.")

    embeds = []
    for url in post_document["urls"]:
        embed = discord.Embed(
            title=f"{post_document['name']}", 
            description=post_document['description'] or "(No description provided.)",
            colour=discord.Colour.random(),
            timestamp=post_document['date'],
        )
        embed.add_field(name=":star2: Stars", value=len(post_document["stars"]))
        embed.add_field(name=":bookmark: Tags", value=" • ".join(post_document["tags"]) or "(none)")
        embed.add_field(name=f"Attachment: ({url[2]})", value=f"\n[Click here to View]({url[0]})", inline=False)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"ID: {post_document['_id']}")
        if "image" in url[1]: # Discord's API only allows you attach images to embeds
            embed.set_image(url=url[0])
        if post_document["is_nsfw"] == True:
            embed.title += " - (NSFW)"
        embeds.append(embed)
    
    if len(post_document["urls"]) == 1:
        if not channel:
            await ctx.reply(embed=embeds[0], hidden=hidden)
        else:
            await channel.send(embed=embed)
    else:
        if no_pagination:
            if channel:
                for embed in embeds:
                    await channel.send(embed=embed)
            else:
                await ctx.reply(embeds=embeds, hidden=hidden)
        else:
            await Paginator(bot=bot, ctx=ctx, embeds=embeds, timeout=100).start()
