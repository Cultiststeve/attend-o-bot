import logging
import random
from typing import Optional, Dict

import discord
from discord.ext import commands

from src.teamspeak_querying import TeamspeakQueryControl
from src.selenium_interaction import SeleneiumController

# Set intents, defaulty for now
intents = discord.Intents.default()
intents.typing = False
intents.presences = False

# Create our bot, as global
bot = commands.Bot(command_prefix='?', description="51st Attendance prototype bot", intents=intents)

# Need a teamspeak query control class
teamspeak_query_controller: Optional[TeamspeakQueryControl] = None  # Created by main program
selenium_controller: Optional[SeleneiumController] = None


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


def format_clients_for_humans(clients: list):
    clients = [f"{x['client_nickname']} - Client ID:{x['clid']}" for x in clients]
    return clients


@bot.command()
async def list_clients(ctx):
    """
    Just reply with a list of clients on the teamspeak server
    :param ctx: 
    :param teamspeak_query_controller: 
    :return: 
    """
    if not teamspeak_query_controller:
        err_str = "No teamspeak query controller available"
        logging.error(err_str)
        await ctx.send(f"Internal error {err_str}")

    clients = teamspeak_query_controller.list_all_clients()

    await ctx.send(format_clients_for_humans(clients))



@bot.command()
async def take_attendance(ctx, event_id: str):
    selenium_controller.go_to_admin_page(event_id)

    clients = teamspeak_query_controller.list_all_clients()

    for client in clients:
        if selenium_controller.tick_box_for_name(client["client_nickname"]):
            await ctx.send(f"Ticked box for {client['client_nickname']}")
        else:
            await ctx.send(f"Did not find a matching name for {client['client_nickname']}")


# @bot.event
# async def on_message(message):
#     print(message)
#     if message.content == 'test':
#         await message.channel.send('Testing 1 2 3!')
#
#     await bot.process_commands(message)
