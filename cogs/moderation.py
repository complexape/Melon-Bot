import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option

from helpers.album_helpers import GuildAlbum
from utils.album_manager import InvalidUsageError


class Moderation(commands.Cog, name="moderation"):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx: SlashContext):
        return ctx.author.guild_permissions.administrator
    
    @cog_ext.cog_slash(name="setdefaultaccessrole", 
        description="All future posts being made will require this role in order to be viewed. (Mod-only Command)",
        options=[ create_option(name="role", description="The target role.", option_type=8, required=True) ],
    )
    async def _set_default_access_role(self, ctx: SlashContext, role: discord.Role):
            album = GuildAlbum(ctx)
            album.edit_property({ "$set": { "global_access_role_id": role.id}})
            await ctx.reply(
                f"The default role required for viewing and editing this **{ctx.guild.name}**'s album has been set to: **{role.name}**" + 
                "\nNote: this will NOT affect the access needed for all current posts.", hidden=True)

    @cog_ext.cog_slash(name="setpostboard", 
        description="All posts will be sent again to this channel. (Mod-only Command)",
        options=[ create_option(name="channel", description="The target channel.", option_type=7, required=True) ],
    )
    async def _set_post_board(self, ctx: SlashContext, *, channel: discord.TextChannel):
        if isinstance(channel, discord.TextChannel):
            album = GuildAlbum(ctx)
            album.edit_property({ "$set": {"post_board_channel": channel.id}})
            await ctx.reply(f"**{channel.name}** has been set to **{ctx.guild.name}**'s post's channel.", hidden=True)
        else:
            raise InvalidUsageError("Text channels only!")

    @cog_ext.cog_slash(name="toggleban", 
        description="Ban/Unban a member from accessing this guild's album. (Mod-only Command)",
        options=[ create_option(name="member", description="The target member.", option_type=6, required=True) ],
    )
    async def _toggle_ban(self, ctx: SlashContext, member: discord.Member):
        if not member.bot and not member.guild_permissions.manage_messages:
            album = GuildAlbum(ctx)
            if member.id not in album.banned_user_ids:
                album.edit_property({ "$push": { "banned_user_ids": member.id}})
                await ctx.reply(f"**{member.name} has been banned from this **{ctx.guild.name}**'s album.", hidden=True)
            else:
                album.edit_property({ "$pull": { "banned_user_ids": member.id}})
                await ctx.reply(f"**{member.name}** has been unbanned from {ctx.guild.name}'s album.", hidden=True)
        else:
            raise InvalidUsageError("This member cannot be banned.")

def setup(bot):
    bot.add_cog(Moderation(bot))