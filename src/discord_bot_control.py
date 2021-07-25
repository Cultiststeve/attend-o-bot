import logging
import random
from typing import Optional, Dict, List
import traceback
import sys

import discord
from discord.ext import commands, tasks
from fuzzywuzzy import process as fuzzy_process

from src.teamspeak_querying import TeamspeakQueryControl
from src.sql_interaction import SQLInteraction
from utils import get_args

args = get_args()

# Set intents, default for now
intents = discord.Intents.default()
intents.typing = False
intents.presences = False

# Create our bot, as global
bot = commands.Bot(command_prefix='?', description="51st Attendance prototype bot", intents=intents)

# Need a teamspeak query control class
teamspeak_query_controller: Optional[TeamspeakQueryControl] = None  # Created by main program
# selenium_controller: Optional[SeleneiumController] = None
sql_controller: Optional[SQLInteraction] = None

# If defined as a list, only do attendance for clients in that channel
cid_list = None


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


@bot.command()
async def roll(ctx, dice: str):
    """Rolls a dice in NdN format.

    Debug function
    """
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        await ctx.send('Format has to be in NdN!')
        return

    result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
    await ctx.send(result)


# ------------ Main commands to use ------------

class AttendanceFunctions(commands.Cog):
    def __init__(self, cog_bot: commands.Bot):
        self.logger = logging.getLogger("main.discord_bot_control.AttendanceFunctions")
        self.bot = cog_bot
        self.current_event_id: Optional[int] = None
        self.ts3_keep_aliver.start()  # Sends a keep alive to the ts3 every 200 secs

        self.channel_whitelist: List = []
        self.set_target_channels_inner(target_channels="Server 1, Server 2")

    def cog_unload(self):
        self.ts3_keep_aliver.cancel()
        self.take_attendance.cancel()

    @staticmethod
    async def log_and_discord_print(ctx, message, level=logging.INFO):
        logging.log(level=level, msg=message)
        await ctx.send(message)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command.
        Parameters
        ------------
        ctx: commands.Context
            The context used for command invocation.
        error: commands.CommandError
            The Exception raised.
        """

        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return

        # This prevents any cogs with an overwritten cog_command_error being handled here.
        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        ignored = (commands.CommandNotFound,)

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return

        if isinstance(error, commands.DisabledCommand):
            await ctx.send(f'{ctx.command} has been disabled.')

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send(f'{ctx.command} can not be used in Private Messages.')
            except discord.HTTPException:
                pass

        # For this error example we check to see where it came from...
        elif isinstance(error, commands.BadArgument):
            if ctx.command.qualified_name == 'tag list':  # Check if the command being invoked is 'tag list'
                await ctx.send('I could not find that member. Please try again.')

        else:
            # All other Errors not returned come here. And we can just print the default TraceBack.
            logging.error(f'Ignoring exception in command {ctx.command}: {error}')
            await ctx.send(f"Error while processing {ctx.command} : {error}")  # inform user
            # traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    @tasks.loop(seconds=200)
    async def ts3_keep_aliver(self):
        self.logger.debug("Sending keepalive to ts3")
        teamspeak_query_controller.keep_conn_alive()

    @commands.command()
    async def current_state(self, ctx):
        """Debug function, list intresting state variable values"""
        await self.log_and_discord_print(ctx, f"```{self.take_attendance.is_running()=}\n"
                                              f"{self.current_event_id=}\n"
                                              f"{self.channel_whitelist=}\n"
                                              f"```")

    def set_target_channels_inner(self, target_channels: str):
        target_channels = target_channels.split(sep=',')
        self.channel_whitelist = teamspeak_query_controller.get_children_named_channels(
            target_channel_names=target_channels)


    @commands.command()
    async def set_target_channels(self, ctx, target_channels: str):
        """Set the whitelist of target channels for attendance

        Args:
            target_channels(str), comma seperated list of channel names, all surrounded by ""
        """
        self.set_target_channels_inner(target_channels)
        await self.log_and_discord_print(ctx, message=f"Set channel whitelist to {self.channel_whitelist}")

    @tasks.loop(seconds=5)
    async def take_attendance(self, ctx_started_from):
        """While running, this function monitors everyone in teamspeak in the right channels"""
        await self.log_and_discord_print(ctx_started_from, "Searching for members in teamspeak...")
        all_clients = teamspeak_query_controller.list_all_clients()
        all_channels = teamspeak_query_controller.list_all_channels()
        pass

    @commands.command()
    async def start_new_event_attendance(self, ctx, event_name: str):
        """Create a new event, and start taking attendance on the current channels

        Args:
            event_name (str): The name of the event, for display on forums
        """
        logging.debug(f"Got cmd: start_new_event_attendance")
        if self.take_attendance.is_running():
            await self.log_and_discord_print(ctx, "Already taking attendance, please stop existing")
            return

        self.current_event_id = sql_controller.create_event(event_name)
        await self.log_and_discord_print(ctx,
                                         f"Created new event with name {event_name} and id {self.current_event_id}. "
                                         f"Now taking attendance for this event, for channels {1}")

        self.take_attendance.start(ctx)

    @commands.command()
    async def start_existing_event_attendance(self, ctx, event_id: int):
        """Start taking attendance for an existing event, given the event id

        Args:
            event_id (int): event Id to take attendance for

        """
        logging.debug(f"Got cmd: start_existing_event_attendance with {event_id}")
        if self.take_attendance.is_running():
            await self.log_and_discord_print(f"Already taking attendance for event id {self.current_event_id}. "
                                             f"Please stop this first")
            return
        # TODO
        self.current_event_id = event_id
        self.take_attendance.start(ctx)

    @commands.command()
    async def stop_event_attendance(self, ctx):
        """Stops the bot if attendance taking is currently underway, and prints a summary."""
        logging.debug(f"Got cmd: stop_event_attendance")
        if self.take_attendance.is_running():
            self.take_attendance.stop()
            await ctx.send(f"Stopped taking attendance for {self.current_event_id}")
            self.current_event_id = None
        else:
            await self.log_and_discord_print(ctx, "Not currently taking attendance.")

    @commands.command()
    async def list_clients(self, ctx):
        """
        Replys with a list of clients on the teamspeak server
        :param ctx:
        :param teamspeak_query_controller:
        :return:
        """
        clients = teamspeak_query_controller.list_all_clients()
        await self.log_and_discord_print(ctx, format_clients_for_humans(clients))


def format_clients_for_humans(clients: list):
    clients = [f"{x['client_nickname']} - Client ID:{x['clid']}" for x in clients]
    return clients
#
#

#
#
# @bot.command()
# async def take_attendance(ctx, event_id: str):
#     selenium_controller.go_to_admin_page(event_id)
#
#     clients = teamspeak_query_controller.list_all_clients()
#
#     website_names = selenium_controller.get_name_list()
#
#     for client in clients:
#
#         # If we have a channel list, filter clients not in channels
#         if cid_list and client["cid"] not in cid_list:
#             # await ctx.send(f"{client['client_nickname']} not in cid list, not attending.")
#             continue
#
#         # Find closest match in selenium list
#         enlistment_name, match_percent = fuzzy_process.extractOne(query=client["client_nickname"], choices=website_names)
#         logging.debug(f"Match for {client['client_nickname']} = {enlistment_name} - {match_percent}")
#         if match_percent < args.get("fuzzy_match_distance"):
#             await ctx.send(f"**Did not find a close enough match for {client['client_nickname']}, "
#                            f"you must add this person manually**")
#             continue
#
#         if selenium_controller.tick_box_for_name(enlistment_name):
#             await ctx.send(f"Marked {client['client_nickname']}={enlistment_name} as attending")
#         else:
#             logging.error(f"After fuzzy matching, could not tick box for {enlistment_name=} for {client['client_nickname']}")
#             await ctx.send(f"Did not find a matching name for {client['client_nickname']}={enlistment_name}."
#                            f"This should not happen after fuzzy matching, sorry.")
#
#     selenium_controller.click_submit()
#     await ctx.send("Finished taking attendance!")
#
#
# @bot.command()
# async def get_clids(ctx):
#     channel_list = teamspeak_query_controller.list_all_channels()
#     readable_list = []
#     for channel in channel_list:
#         readable_dict = dict((k, channel[k]) for k in ["cid", "channel_name"] if k in channel)
#         readable_list.append(readable_dict)
#
#     for channel in readable_list:
#         await ctx.send(channel)
#
#
# @bot.command()
# async def set_clids(ctx, clids: str):
#     global cid_list
#     logging.info(f"Setting clids. Input: {clids}")
#     clids = clids.split(sep=",")
#     # clids = [int(x) for x in clids]
#     cid_list = clids
#     await ctx.send(f"Set channel whitelist to {cid_list}")
#
#
#
# # @bot.event
# # async def on_message(message):
# #     print(message)
# #     if message.content == 'test':
# #         await message.channel.send('Testing 1 2 3!')
# #
# #     await bot.process_commands(message)
