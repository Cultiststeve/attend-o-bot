import datetime
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
    logging.info(f'Logged in as {bot.user} (ID: {bot.user.id}). Bot is ready!')


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

        self.channel_whitelist: List = []
        self.set_target_channels_inner(target_channels="Server 1, Server 2")

        self.current_event_id: Optional[int] = None
        self.current_event_name: Optional[str] = None
        # During an event, keep track of when we first saw clids
        self.first_seen = {}  # key is clid, val is first seen time (or true if added to attendnace)
        self.matched = {}  # key is ts name, val is db name
        self.not_matched = set()  # Set of ts usernames

        # Need to store names, for queries if people leave
        self.limbo_names = {}  # key is clid, val is tsnickname

        self.ts3_keep_aliver.start()  # Sends a keep alive to the ts3 every 200 secs

    def cog_unload(self):
        self.ts3_keep_aliver.cancel()
        self.scan_for_attendance.cancel()

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
            logging.error(traceback.extract_stack())
            await ctx.send(f"Error while processing {ctx.command} : {error}")  # inform user
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    @tasks.loop(seconds=200)
    async def ts3_keep_aliver(self):
        teamspeak_query_controller.keep_conn_alive()

    @commands.command()
    async def current_state(self, ctx):
        """Debug function, list interesting state variable values"""
        await self.log_and_discord_print(ctx, f"```"
                                              f"{self.scan_for_attendance.is_running()=}\n"
                                              f"{self.current_event_id=} - {self.current_event_name=}\n"
                                              f"{self.channel_whitelist=}\n"
                                              f"{self.first_seen=}\n"
                                              f"{self.limbo_names=}\n"
                                              f"```")

    def set_target_channels_inner(self, target_channels: str):
        target_channels = target_channels.split(sep=',')
        channel_list = teamspeak_query_controller.get_children_named_channels(
            target_channel_names=target_channels)
        for chan in channel_list:
            self.channel_whitelist.append(chan.get("cid"))

    @commands.command()
    async def set_target_channels(self, ctx, target_channels: str):
        """Set the whitelist of target channels for attendance

        Args:
            target_channels(str), comma seperated list of channel names, all surrounded by ""
        """
        self.set_target_channels_inner(target_channels)
        await self.log_and_discord_print(ctx, message=f"Set channel whitelist to {self.channel_whitelist}")

    @tasks.loop(seconds=15)
    async def scan_for_attendance(self, ctx_started_from):
        """While running, this function monitors everyone in teamspeak in the right channels"""
        self.logger.debug("Searching for members in teamspeak")
        all_clients = teamspeak_query_controller.list_all_clients()
        self.logger.debug(f"Found {len(all_clients)} on server")
        for client in all_clients:
            cldbid = client.get("client_database_id")  # Use this, moar unique
            cid = client.get("cid")
            if cid not in self.channel_whitelist:
                continue

            client_nickname = client.get('client_nickname')
            # TODO ignore the attendance bot + music bots?
            if cldbid in self.first_seen.keys():
                if self.first_seen[cldbid] == True:
                    continue  # Already added to attendance, no further processing needed
                if self.first_seen[cldbid] + datetime.timedelta(minutes=args.get("time_to_attend")) \
                        < datetime.datetime.now():
                    # We saw them over X min ago, add to db
                    await self.log_and_discord_print(ctx_started_from,
                                                     f"Saw {client_nickname} over {args.get('time_to_attend')} "
                                                     f"min ago - attempting to match to database name")
                    success = await self.add_client_to_attendance(ctx_started_from, client)
                    self.first_seen[cldbid] = True
                    self.limbo_names.pop(cldbid)
            else:  # if first sighting
                self.first_seen[cldbid] = datetime.datetime.now()
                self.limbo_names[cldbid] = client_nickname
                await self.log_and_discord_print(ctx_started_from, f"First sight of {cldbid}:{client_nickname}.",
                                                 level=logging.DEBUG)
        self.logger.debug("Finished scanning")

    async def add_client_to_attendance(self, ctx, client: dict):
        ts_client_username = client["client_nickname"]
        all_sql_users = sql_controller.get_all_users()
        sql_usernames = [x["member_name"] for x in all_sql_users]

        # Find a matching username in the DB, for the TS client
        sql_username_matching, match_percent = fuzzy_process.extractOne(query=ts_client_username,
                                                                        choices=sql_usernames)
        self.logger.debug(f"Found best match for {ts_client_username} = {sql_username_matching=} with score {match_percent}")

        if match_percent < args.get("fuzzy_match_distance"):
            await self.log_and_discord_print(ctx,
                                             f"**Did not find a close enough match for TS user {ts_client_username}, "
                                             f"you must add this person manually**")
            self.not_matched.add(ts_client_username)
            return False
        else:
            # We have a matching sql usernames
            id_member = [x["id_member"] for x in all_sql_users if x["member_name"] == sql_username_matching]
            assert len(id_member) == 1  # sql usernames must be unique
            id_member = id_member[0]
            self.logger.debug(f"Matched {client} to {id_member}:{sql_username_matching}")
            sql_controller.add_attendee_to_event(id_event=self.current_event_id, id_member=id_member)
            self.matched[ts_client_username] = sql_username_matching
            await self.log_and_discord_print(ctx,
                                             f"Found a match for TS name: {ts_client_username} = Database name: {sql_username_matching}.\n"
                                             f"Added to event {self.current_event_name}")
            return True

    @commands.command()
    async def start_new_event_attendance(self, ctx, event_name: str):
        """Create a new event, and start taking attendance on the current channels

        Args:
            event_name (str): The name of the event, for display on forums
        """
        logging.debug(f"Got cmd: start_new_event_attendance")
        if self.scan_for_attendance.is_running():
            await self.log_and_discord_print(ctx, "Already taking attendance, please stop existing")
            return
        self.current_event_id = sql_controller.create_event(event_name)
        self.current_event_name = event_name
        await self.log_and_discord_print(ctx,
                                         f"Created new event with name {event_name} and id {self.current_event_id}. "
                                         f"Now taking attendance for this event, for channels {1}")

        self.scan_for_attendance.start(ctx)

    @commands.command()
    async def start_existing_event_attendance(self, ctx, event_id: int):
        """Start taking attendance for an existing event, given the event id

        Args:
            event_id (int): event Id to take attendance for

        """
        logging.debug(f"Got cmd: start_existing_event_attendance with {event_id}")
        if self.scan_for_attendance.is_running():
            await self.log_and_discord_print(f"Already taking attendance for event id {self.current_event_id}. "
                                             f"Please stop this first")
            return

        self.current_event_id = event_id
        self.current_event_name = sql_controller.get_event_name_for_id(self.current_event_id)
        self.scan_for_attendance.start(ctx)

    @commands.command()
    async def stop_event_attendance(self, ctx):
        """Stops the bot if attendance taking is currently underway, and prints a summary."""
        logging.debug(f"Got cmd: stop_event_attendance")
        if self.scan_for_attendance.is_running():
            self.scan_for_attendance.stop()
            await ctx.send(f"Stopped taking attendance for {self.current_event_id}")

            await self.do_event_summary(ctx)
            # Clear out the globals
            self.current_event_id = None
            self.current_event_name = None
            self.first_seen = {}
            self.matched = {}
            self.not_matched = {}
            self.limbo_names = {}
        else:
            await self.log_and_discord_print(ctx, "Not currently taking attendance.")

    async def do_event_summary(self, ctx):
        # TODO promotions#
        await ctx.send(f"**Summary for {self.current_event_name} - {self.current_event_id}**")
        str_to_send = "```"
        if len(self.matched) > 0:
            str_to_send += f"Added the a total of {len(self.matched)} matches to the attendance for this event:\n"
            for match in self.matched:
                str_to_send += f"* {match} = {self.matched[match]}\n"
        if len(self.not_matched) > 0:
            str_to_send += f"Could not find a match for a total of {len(self.not_matched)}, " \
                           f"ensure you add them manually:\n"
            for notmatch in self.not_matched:
                str_to_send += f"* {notmatch}\n"
        if len(self.limbo_names) > 0:  # Len of non-processed
            str_to_send += f"The following {len(self.limbo_names)} people were seen but had not attended for enough " \
                           f"time to earn attendance:\n"
            for limbo_clid in self.limbo_names:
                str_to_send += f"* {self.limbo_names.get(limbo_clid)} - first seen at {self.first_seen.get(limbo_clid)}\n"
        str_to_send += "End of summary\n"
        str_to_send += "```"
        await ctx.send(str_to_send)
    pass

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
