from discord.ext import commands
from __main__ import send_cmd_help
from .utils.dataIO import dataIO
from .utils import checks
import datetime
import asyncio
import discord
import os

try:
    import psutil
except:
    psutil = False


class Statistics:
    """
    Statistics
    """

    def __init__(self, bot):
        self.bot = bot
        self.settings = dataIO.load_json('data/statistics/settings.json')
        self.refresh_rate = self.settings['REFRESH_RATE']

    def redapi_hook(self, data=None):
        if not data:
            x = self.retrieve_statistics()
            x['avatar'] = self.bot.user.avatar_url if self.bot.user.avatar else self.bot.user.default_avatar_url
            x['uptime'] = self.get_bot_uptime(brief=False)
            x['total_cogs'] = len(self.bot.cogs)
            x['total_commands'] = len(self.bot.commands)
            x['discord_version'] = str(discord.__version__)
            x['id'] = self.bot.user.id
            x['discriminator'] = self.bot.user.discriminator
            x['created_at'] = self.bot.user.created_at.strftime('%B %d, %Y at %H:%M:%S')
            x['loaded_cogs'] = [cog for cog in self.bot.cogs]
            x['prefixes'] = self.bot.settings.prefixes
            x['servers'] = [{'name': server.name, 'members': len(server.members), 'icon_url': server.icon_url} for server in self.bot.servers]
            x['cogs'] = len(self.bot.cogs)
            return x
        else:
            pass

    @commands.command()
    async def stats(self):
        """
        Retreive statistics
        """
        message = await self.embed_statistics()
        await self.bot.say(embed=message)

    @commands.command(pass_context=True)
    async def statsrefresh(self, context, seconds: int=0):
        """
        Set the refresh rate by which the statistics are updated

        Example: [p]statsrefresh 42

        Default: 5
        """

        if not self.refresh_rate:  # If statement incase someone removes it or sets it to 0
            self.refresh_rate = 5

        if seconds == 0:
            message = 'Current refresh rate is {}'.format(self.refresh_rate)
            await send_cmd_help(context)
        elif seconds < 5:
            message = '`I can\'t do that, the refresh rate has to be above 5 seconds`'
        else:
            self.refresh_rate = seconds
            self.settings['REFRESH_RATE'] = self.refresh_rate
            dataIO.save_json('data/statistics/settings.json', self.settings)
            message = '`Changed refresh rate to {} seconds`'.format(
                self.refresh_rate)
        await self.bot.say(message)

    @commands.command(no_pm=True, pass_context=True)
    @checks.serverowner_or_permissions(manage_server=True)
    async def statschannel(self, context, channel: discord.Channel=None):
        """
        Set the channel to which the bot will sent its continues updates.
        Example: [p]statschannel #statistics
        """
        if channel:
            self.settings['CHANNEL_ID'] = str(channel.id)
            dataIO.save_json('data/statistics/settings.json', self.settings)
            message = 'Channel set to {}'.format(channel.mention)
        elif not self.settings['CHANNEL_ID']:
            message = 'No Channel set'
            await send_cmd_help(context)
        else:
            channel = discord.utils.get(
                self.bot.get_all_channels(), id=self.settings['CHANNEL_ID'])
            if channel:
                message = 'Current channel is {}'.format(channel.mention)
                await send_cmd_help(context)
            else:
                self.settings['CHANNEL_ID'] = None
                message = 'No channel set'
                await send_cmd_help(context)
        await self.bot.say(message)

    @commands.command(no_pm=True, pass_context=True)
    @checks.serverowner_or_permissions(manage_server=True)
    async def clearstatschannel(self):
        """
        Clear statistics channel
        """
        self.settings['CHANNEL_ID'] = False
        dataIO.save_json('data/statistics/settings.json', self.settings)
        message = 'Channel cleared'
        await self.bot.say(message)

    async def embed_statistics(self):
        stats = self.retrieve_statistics()
        em = discord.Embed(description='\a\n', color=discord.Color.red())
        avatar = self.bot.user.avatar_url if self.bot.user.avatar else self.bot.user.default_avatar_url
        em.set_author(name='Statistics of {}'.format(stats['name']), icon_url=avatar)

        em.add_field(name='**Uptime**', value='{}'.format(self.get_bot_uptime(brief=True)))

        em.add_field(name='**Users**', value=stats['users'])
        em.add_field(name='**Servers**', value=stats['total_servers'])

        em.add_field(name='**Channels**', value=str(stats['channels']))
        em.add_field(name='**Text channels**', value=str(stats['text_channels']))
        em.add_field(name='**Voice channels**', value=str(stats['voice_channels']))

        em.add_field(name='**Messages received**', value=str(stats['read_messages']))
        em.add_field(name='**Commands run**', value=str(stats['commands_run']))
        em.add_field(name='\a', value='\a')

        em.add_field(name='**Active cogs**', value=str(len(self.bot.cogs)))
        em.add_field(name='**Commands**', value=str(len(self.bot.commands)))
        em.add_field(name='\a', value='\a')

        em.add_field(name='\a', value='\a', inline=False)
        em.add_field(name='**CPU**', value='{0:.1f}%'.format(stats['cpu_usage']))
        em.add_field(name='**Memory**', value='{0:.0f} MB ({1:.1f}%)'.format(stats['mem_v_mb'] / 1024 / 1024, stats['mem_v']))
        em.add_field(name='**Threads**', value='{}'.format(stats['threads']))
        em.set_footer(text='API version {}'.format(discord.__version__))
        return em

    def retrieve_statistics(self):
        name = self.bot.user.name
        users = str(len(set(self.bot.get_all_members())))
        servers = str(len(self.bot.servers))
        commands_run = self.bot.counter['processed_commands']
        read_messages = self.bot.counter['messages_read']
        text_channels = 0
        voice_channels = 0

        process = psutil.Process(os.getpid())

        cpu_usage = process.cpu_percent()

        mem_v = process.memory_percent()
        mem_v_mb = process.memory_info().vms
        threads = process.num_threads()

        io_reads = process.io_counters().read_count
        io_writes = process.io_counters().write_count

        for channel in self.bot.get_all_channels():
            if channel.type == discord.ChannelType.text:
                text_channels += 1
            elif channel.type == discord.ChannelType.voice:
                voice_channels += 1
        channels = text_channels + voice_channels

        stats = {
            'name': name, 'users': users, 'total_servers': servers, 'commands_run': commands_run,
            'read_messages': read_messages, 'text_channels': text_channels,
            'voice_channels': voice_channels, 'channels': channels,
            'cpu_usage': cpu_usage, 'mem_v': mem_v, 'mem_v_mb': mem_v_mb, 'threads': threads,
            'io_reads': io_reads, 'io_writes': io_writes}
        return stats

    def get_bot_uptime(self, *, brief=False):
        # Stolen from owner.py - Courtesy of Danny
        now = datetime.datetime.utcnow()
        delta = now - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        if not brief:
            if days:
                fmt = '{d} days, {h} hours, {m} minutes, and {s} seconds'
            else:
                fmt = '{h} hours, {m} minutes, and {s} seconds'
        else:
            fmt = '{h} H - {m} M - {s} S'
            if days:
                fmt = '{d} D - ' + fmt

        return fmt.format(d=days, h=hours, m=minutes, s=seconds)

    async def reload_stats(self):
        await asyncio.sleep(30)
        while self == self.bot.get_cog('Statistics'):
            try:
                if self.settings['CHANNEL_ID']:
                    msg = await self.embed_statistics()
                    channel = discord.utils.get(
                        self.bot.get_all_channels(), id=self.settings['CHANNEL_ID'])
                    messages = False
                    async for message in self.bot.logs_from(channel, limit=1):
                        messages = True
                        if message.author.name == self.bot.user.name:
                            await self.bot.edit_message(message, embed=msg)
                    if not messages:
                        await self.bot.send_message(channel, embed=msg)
                else:
                    pass
                await asyncio.sleep(self.refresh_rate)
            except:
                print('statistics.py: Something critical went wrong, disabling statistics reloading.')
                break


def check_folder():
    if not os.path.exists('data/statistics'):
        print('Creating data/statistics folder...')
        os.makedirs('data/statistics')


def check_file():
    data = {}
    data['CHANNEL_ID'] = None
    data['REFRESH_RATE'] = 5
    f = 'data/statistics/settings.json'
    if not dataIO.is_valid_json(f):
        print('Creating default settings.json...')
        dataIO.save_json(f, data)


def setup(bot):
    if psutil is False:
        raise RuntimeError('psutil is not installed. Run `pip3 install psutil --upgrade` to use this cog.')
    else:
        check_folder()
        check_file()
        n = Statistics(bot)
        bot.add_cog(n)
        loop = asyncio.get_event_loop()
        loop.create_task(n.reload_stats())
