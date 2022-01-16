import discord
from discord.ext import commands
from discord_slash.context import MenuContext
from discord_slash.model import ContextMenuType
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option, create_choice
import pymongo

from helpers.album_helpers import BotSearchPaginator, GuildAlbum
from utils.album_manager import display_post, retrieve_post, InvalidUsageError, CommandCancelled, wait_for_msg

from constants import VALID_TYPES


class Images(commands.Cog, name="images"):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_slash_command_error(self, ctx: SlashContext, error):
        if hasattr(ctx.command, 'on_error'):
            return
        elif isinstance(error, CommandCancelled):
            await ctx.message.delete()
            await ctx.reply("Command cancelled.", hidden=True)
        elif isinstance(error, InvalidUsageError):
            await ctx.reply(str(error), hidden=True)
        else:
           raise error

    @cog_ext.cog_slash(
        name="createpost",
        description="Create a post to add to this guild's album.",
        options=[
            create_option(name="name", description="A name for this post.", option_type=3, required=True),
            create_option(name="description", description="A description for this post.", option_type=3, required=False),
            create_option(name="tags", description="Tags for this post, separated by a comma (,)", option_type=3, required=False),
            create_option(
                name="access_role",
                description="Role-lock this post? All posts are public OR already locked to a role set by an admin by default.",
                option_type=8, required=False),
            create_option(
                name="is_nsfw", 
                description="Flag this post as NSFW? (Posts are SFW by default.)",
                option_type=5, required=False)
        ])
    async def _createpost(self, ctx: SlashContext, name: str, 
            description = "", tags = None, access_role: discord.Role = None, is_nsfw = False
    ):
        album = GuildAlbum(ctx)
        if is_nsfw and not ctx.channel.is_nsfw():
            raise InvalidUsageError("You can only create NSFW posts in NSFW channels!")
        elif name in list(album.collection.find({}, {"name": 1})):
                raise InvalidUsageError(f"A post by the name of '{name}' already exists.")

        await ctx.send(
            embed=discord.Embed(
                title =f"Please respond here with your **attachments** and/or **discord message links** containg attachments. (sep. by spaces (' '))",
                colour=discord.Colour.red(), 
                description=f"A response without attachments will cancel the post.\nValid file types: {', '.join(VALID_TYPES)}"), 
                hidden=True)

        resp = await wait_for_msg(ctx)
        attachments = resp.attachments

        for link in resp.content.split(" "):
            if "https://discord.com/channels/" in link:
                ids = link.split('/')
                channel = ctx.guild.get_channel(int(ids[5]))
                if channel:
                    message = await channel.fetch_message(int(ids[6]))
                    if message and len(attachments) <= 20:
                        attachments.extend(message.attachments)

        try:
            if len(attachments) == 0:
                raise InvalidUsageError("No attachments found, nothing posted. (Did you send file urls instead of attachments?)")

            # verifies that each file's content type is either an image, video, or audio
            elif not all([any(map(a.content_type.__contains__ or [], VALID_TYPES)) for a in attachments]):
                raise InvalidUsageError(f"Your post can only contain **{', '.join(VALID_TYPES)}** files.")

            else:
                await ctx.reply("Adding your files...", hidden=True)
                attachments_msg = await ctx.author.send(files=[await a.to_file() for a in attachments])
                await resp.delete()

                document = await album.create_post(attachments_msg.attachments, name, tags,
                    description, is_nsfw, access_role)
                await ctx.reply(f"**{ctx.author.display_name}** created a post.")
                await display_post(self.bot, ctx, document)

        except InvalidUsageError as e:
            await resp.delete()
            raise e

    @cog_ext.cog_slash(
        name="searchposts",
        description="Search for a post in this guild's album.",
        options=[
            create_option(name="sort_by", description="Sort your results by:", option_type=3, required=False, choices=[
                create_choice(name="Newest", value="new"),
                create_choice(name="Oldest", value="old"),
                create_choice(name="Most popular", value="popular")
            ]),
            create_option(name="name", description="Filter by name.", option_type=3, required=False),
            create_option(name="author", description="Filter by the author of the post", option_type=6, required=False),
            create_option(name="tag", description="Filter by a tag.", option_type=3, required=False),
            create_option(name="max_results", description="Limit the number of results (1-25)",option_type=4, required=False),
            create_option(name="starred_only", description="Only show posts you've starred?", option_type=5, required=False),
        ])
    async def _searchposts(self, ctx: SlashContext, 
        sort_by= None, name = None, tag = None, author: discord.Member = None, 
        max_results = 100, starred_only = False,
    ):
        album = GuildAlbum(ctx)

        # adds any of the user's specified filters
        filters = []
        filters.append({"name": { "$regex": name, "$options": "i" }}) if name else None
        filters.append({"tags": tag}) if tag else None
        filters.append({"author": author.id}) if author else None
        filters.append({"stars": ctx.author_id}) if starred_only else None
        results = album.search_collection(filters, max(min(25, max_results), 1))

        # applies the sort to the results and sorts by newest if no sort specified
        sorted_results = list(results.sort(*{
                "new": ["date", pymongo.DESCENDING],
                "old": ["date", pymongo.ASCENDING],
                "popular": ["stars", pymongo.DESCENDING]
            }.get(sort_by, ["date", pymongo.DESCENDING])
        ))

        if len(sorted_results) < 1:
            raise InvalidUsageError("No posts found. (Check your spelling?)")
        elif len(sorted_results) == 1:
            msg = await ctx.send(f"One post found.", hidden=True)
            post_document = sorted_results[0]
        else:
            msg = await ctx.send(f"{len(sorted_results)} posts found.")
            selection = BotSearchPaginator(ctx, sorted_results)
            post_document = await selection.wait_for_response()
            await msg.delete()
        
        await display_post(self.bot, ctx, post_document)
    
    @cog_ext.cog_slash(name="randompost", description="Show a random post frm this guild")
    async def _randompost(self, ctx: SlashContext):
        album = GuildAlbum(ctx)
        rand_post = list(album.search_collection(limit=1, get_random=True))[0]

        await ctx.reply("Found one!", hidden=True)
        await display_post(self.bot, ctx, rand_post)

    @cog_ext.cog_context_menu(target=ContextMenuType.MESSAGE, name="Star this Post!")
    async def _starthispost(self, ctx: MenuContext):   
        album = GuildAlbum(ctx)
        post, id = retrieve_post(ctx, album)

        if ctx.author_id in post["stars"]:
            raise InvalidUsageError("You've already given this post a star.")
        else:
            # adds the author's id to the target post's list of stars
            album.collection.update_one({ "_id": id }, {"$push": {"stars": ctx.author_id}})
            await ctx.target_message.add_reaction("🌟")
            await ctx.send(f"You've given **{ctx.target_message.embeds[0].title}** a star.", hidden=True)
            await ctx.target_message.reply(f"**{ctx.author.name} Starred this post!**  :star2: ", mention_author=False)

    @cog_ext.cog_context_menu(target=ContextMenuType.MESSAGE, name="Show Entire Post")
    async def _showentirepost(self, ctx: MenuContext):
        album = GuildAlbum(ctx)
        post, _ = retrieve_post(ctx, album)
        await display_post(self.bot, ctx, post, hidden=True, no_pagination=True)

def setup(bot):
    bot.add_cog(Images(bot))