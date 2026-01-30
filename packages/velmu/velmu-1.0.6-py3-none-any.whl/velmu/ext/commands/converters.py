from ...models import Member, User, Channel, Role, Guild, Message, Invite


class Converter:
    async def convert(self, ctx, argument):
        raise NotImplementedError('Derived classes must implement convert.')

class MemberConverter(Converter):
    async def convert(self, ctx, argument):
        if not ctx.guild:
            raise Exception("MemberConverter only works in guilds.")

        user_id = None
        # 1. Check ID (UUID support: length check only, no isdigit)
        if len(argument) > 5 and not argument.startswith('<'):
             user_id = argument
        elif argument.startswith('<@') and argument.endswith('>'):
            # <@123> or <@!123>
            content = argument[2:-1]
            if content.startswith('!'):
                content = content[1:]
            if '|' in content: # <@123|username> style
                 content = content.split('|')[0]
            user_id = content
        
        if user_id:
             # Try Cache
             member = ctx.guild.get_member(user_id)
             if member:
                 return member
             
             # Try API
             try:
                 return await ctx.guild.fetch_member(user_id)
             except Exception:
                 # If explicit ID/Mention passed but failed, we might still want to try name matching if ID was not really an ID?
                 # No, if it looks like an ID/Mention, we commit to that.
                 pass

        # 3. Check Username / Nickname (Name Matching)
        arg_lower = argument.lower()
        # Remove leading @ if present (e.g. "@User")
        if arg_lower.startswith('@'):
            arg_lower = arg_lower[1:]
            
        for member in ctx.guild.members:
            if member.username.lower() == arg_lower or (member.nick and member.nick.lower() == arg_lower):
                return member
                
        raise BadArgument(f'Member "{argument}" not found. Please use ID, Mention or Name.')

class ChannelConverter(Converter):
    async def convert(self, ctx, argument):
        if not ctx.guild:
             raise Exception("ChannelConverter only works in guilds.")
        channel_id = None
        # 1. Check ID
        if len(argument) > 5 and argument.isdigit():
            channel_id = argument
        # 2. Check Mention <#123>
        if argument.startswith('<#') and argument.endswith('>'):
            channel_id = argument[2:-1]
        # 2. UUID or ID (Lax check for Velmu UUIDs)
        elif len(argument) > 5:
            channel_id = argument

        if channel_id:
            # Try Cache
            channel = ctx.guild.channels.get(channel_id) if ctx.guild else ctx.bot.get_channel(channel_id)
            if channel: return channel
            
            # Try Fetch
            try:
                # If in guild, fetch from guild to ensure context? 
                # Actually bot.fetch_channel is fine
                return await ctx.bot.fetch_channel(channel_id)
            except:
                # Catch api errors
                pass
                
        # 3. Name Match (in Guild)
        if ctx.guild:
            for channel in ctx.guild.channels.values():
                if channel.name == argument:
                    return channel

        raise BadArgument(f'Channel "{argument}" not found.')

class UserConverter(Converter):
    async def convert(self, ctx, argument):
        user_id = None
        # 1. Mention
        if argument.startswith('<@') and argument.endswith('>'):
            content = argument[2:-1]
            if content.startswith('!'): content = content[1:]
            user_id = content.split('|')[0]
        # 2. UUID or ID
        elif len(argument) > 5:
            user_id = argument

        if user_id:
            # Try Cache
            user = ctx.bot.get_user(user_id)
            if user: return user
            # Try Fetch
            try:
                return await ctx.bot.fetch_user(user_id)
            except:
                pass
        
        raise BadArgument(f'User "{argument}" not found. Use ID or Mention.')

class RoleConverter(Converter):
    async def convert(self, ctx, argument):
        if not ctx.guild:
            raise Exception("RoleConverter only works in guilds.")

        role_id = None
        
        # 1. Mention <@&ID>
        if argument.startswith('<@&') and argument.endswith('>'):
            role_id = argument[3:-1]
        # 2. UUID or ID
        elif len(argument) > 5:
            role_id = argument

        if role_id:
            role = ctx.guild.get_role(role_id)
            if role: return role
            
            # Roles should be in cache if guild is loaded. 
            # If not, try fetching all roles to refresh cache
            try:
                # print(f"[DEBUG] Fetching roles for guild {ctx.guild.id}...")
                roles = await ctx.guild.fetch_roles()
                # print(f"[DEBUG] Fetched {len(roles)} roles. IDs: {[r.id for r in roles]}")
                role = ctx.guild.get_role(role_id)
                if role: return role
            except Exception as e:
                # print(f"[DEBUG] fetch_roles failed: {e}") 
                pass
        
        # 3. Name Match
        for role in ctx.guild.roles.values():
            if role.name == argument:
                return role
                
        raise BadArgument(f'Role "{argument}" not found.')

class GuildConverter(Converter):
    async def convert(self, ctx, argument):
        guild_id = None
        if len(argument) > 5:
            guild_id = argument
            
        if guild_id:
            guild = ctx.bot.get_guild(guild_id)
            if guild: return guild
            try:
                return await ctx.bot.fetch_guild(guild_id)
            except:
                pass
                
        raise BadArgument(f'Guild "{argument}" not found.')

class MessageConverter(Converter):
    async def convert(self, ctx, argument):
        # Format: MessageID or ChannelID-MessageID or Link
        # Only support MessageID (current channel) or ChannelID-MessageID 
        
        message_id = argument
        channel = ctx.channel
        
        # print(f"[DEBUG] Converting Message: {argument} in channel {channel.id}")

        # Try fetch from channel
        try:
            msg = await channel.fetch_message(message_id)
            # print(f"[DEBUG] Message found: {msg.id}")
            return msg
        except Exception as e:
            # print(f"[DEBUG] fetch_message failed: {e}")
            raise BadArgument(f'Message "{argument}" not found.')

class InviteConverter(Converter):
    async def convert(self, ctx, argument):
        # Extract code from URL or raw code
        code = argument
        if 'velmu/invite/' in code:
            code = code.split('invite/')[-1]
            
        try:
            return await ctx.bot.fetch_invite(code)
        except:
            raise BadArgument(f'Invite "{argument}" not found or invalid.')
