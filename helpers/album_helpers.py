import asyncio
from datetime import datetime

import discord
from discord.utils import get
from discord_slash import SlashContext
from disputils import BotEmbedPaginator

from utils.album_manager import InvalidUsageError, CommandCancelled, display_post

from constants import TZ, ALBUM_DB

class GuildAlbum:
    def __init__(self, ctx: SlashContext):
        self.ctx = ctx

        self.collection = self.initalize_guild()

        self.properties = self.collection.find_one({"_id": "0"})
        self.banned_user_ids = self.properties["banned_user_ids"]
        self.access_role_id = self.properties["global_access_role_id"]
        self.post_board_channel  = self.properties["post_board_channel"]

        if self.ctx.author.id in self.banned_user_ids:
            raise InvalidUsageError("You don't have permission to do that.")

    def initalize_guild(self):
        if not str(self.ctx.guild_id) in ALBUM_DB.list_collection_names():
            # creates new guild collection, along with a guild properties document
            ALBUM_DB.create_collection(str(self.ctx.guild_id))
            collection = ALBUM_DB[str(self.ctx.guild_id)]
            collection.insert_one({
                "_id": "0",
                "global_access_role_id": self.ctx.guild.default_role.id,
                "post_board_channel": 0,
                "banned_user_ids": []
            })
        collection = ALBUM_DB[str(self.ctx.guild_id)]
        return collection
    
    async def create_post(self, 
        attachments: list[discord.Attachment], 
        name: str, 
        tag_str: str, 
        description: str = "", 
        is_nsfw: bool = False, 
        access_role: discord.Role = None
    ):
        urls = [[a.proxy_url , a.content_type, a.filename] for a in attachments]
        tags = tag_str.replace(" ", "").split(",") if tag_str else []

        if self.collection.find_one({"urls": { "$size" : len(urls), "$all": urls } }):
            raise InvalidUsageError("Duplicate post detected!")
        elif len(tags) > 15:
            raise InvalidUsageError("Too many tags added.")

        document = {
            "urls": urls,
            "name": name,
            "tags": list(filter(None, tags)),
            "description": description,
            "author_id": self.ctx.author_id,
            "access_role_id": access_role.id if access_role else self.access_role_id,
            "date": datetime.now(TZ),
            "is_nsfw": is_nsfw,
            "stars": []
        }
        self.collection.insert_one(document)

        if self.post_board_channel != 0:
            channel = get(self.ctx.guild.channels, id=int(self.post_board_channel))
            await display_post(self.ctx.bot, self.ctx, document, channel=channel, no_pagination=True)

        return document

    def edit_property(self, update: dict):
        self.collection.find_one_and_update(filter={"_id": "0"}, update=update)

    def search_collection(self, 
        my_filters: list[dict] = [], limit: int = 100, get_random: bool = False
    ):
        filters = [{"_id": { "$ne": "0"}}]

        # results which the requester does not have their access_id and
        # are not their author are filtered out (does not apply for moderators)
        if not self.ctx.author.guild_permissions.manage_messages:
            my_role_ids = [role.id for role in self.ctx.author.roles]
            filters.append({
                "$or": [ 
                    {"access_role_id": {"$in": my_role_ids}},
                    {"author_id": self.ctx.author_id}]
            })
        
        # only displays nsfw posts in nsfw channels
        if not self.ctx.channel.is_nsfw():
            filters.append({"is_nsfw": False})

        if get_random:
            return self.collection.aggregate(
                [{"$match": {"$and": filters + my_filters} }, { "$sample": { "size": max(1, limit) } }]
            )
        else:
            return self.collection.find(filter = {"$and": filters + my_filters}).limit(limit)

class BotSearchPaginator(BotEmbedPaginator):
    def __init__(self, ctx: SlashContext, results: list[dict]):
        CHUNK_SIZE = 10
        embeds = []
        chunks = [results[i:i+CHUNK_SIZE] for i in range(0, len(results), CHUNK_SIZE)]
        i = 0
        for chunk in chunks:
            embed = discord.Embed(
                title="Please respond with the __**number**__ next to your post.",
                colour=discord.Colour.random()
            )
            for post in chunk:
                i += 1
                embed.add_field(
                    name=f"{i}. {post['name']}", 
                    value=f" {post['date'].strftime('%Y/%m/%d, %H:%M')}, stars: {len(post['stars'])}", 
                    inline=False)
            embeds.append(embed)
        super().__init__(ctx, embeds)
        self._input_dict = {i: result for i, result in enumerate(results, 1)}
    

    async def wait_for_response(self):
        def check(msg):
            return msg.author.id == self._ctx.author_id and msg.channel.id == self._ctx.channel_id
        async def msg_wait_task(self):
            msg = await self._ctx.bot.wait_for("message", check=check)
            await self.quit()
            return msg

        if len(self.pages) > 1:
            tasks = [ 
                asyncio.create_task(msg_wait_task()), 
                asyncio.create_task(self.run())]
            ret , unfinished =  await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in unfinished:
                task.cancel()
            response = ret.pop().result()

            # response is not a discord message if the user exited the paginated embed first
            if not isinstance(response, discord.Message):
                raise CommandCancelled
        else:
            result_embed = await self._ctx.send(embed=self.pages[0])
            try:
                response = await self._ctx.bot.wait_for("message", timeout=120.0, check=check)
            except asyncio.TimeoutError:
                raise CommandCancelled
            await result_embed.delete()
        
        await response.delete()
        if not response.content.isdigit():
            raise CommandCancelled
        return self._input_dict.get(int(response.content), 1)