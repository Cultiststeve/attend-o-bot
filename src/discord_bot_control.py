import random

import discord
from discord.ext import commands

from src.teamspeak_querying import TeamspeakInfoGetter

query_acc_user = "generic_user_1"
query_acc_password = "eVRrzG07"
teamspeak_getter = TeamspeakInfoGetter(query_username=query_acc_user,
                                       query_password=query_acc_password)


intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='?', description="description", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


@bot.command()
async def roll(ctx, dice: str):
    """Rolls a dice in NdN format."""
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        await ctx.send('Format has to be in NdN!')
        return

    result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
    await ctx.send(result)


@bot.command()
async def list_clients(ctx):
    clients = teamspeak_getter.list_all_clients()
    await ctx.send(clients)


# @bot.event
# async def on_message(message):
#     print(message)
#     if message.content == 'test':
#         await message.channel.send('Testing 1 2 3!')
#
#     await bot.process_commands(message)