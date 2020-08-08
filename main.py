import asyncio
import io
import json
import math
import random

import discord
import requests
from discord.ext import commands
from discord.ext.commands import Bot
from discord.utils import get

with open('private/token.json', 'r') as f:
		token = json.load(f)

client = commands.Bot(command_prefix = 'e!')
client.remove_command('help')

@client.event
async def on_ready():
	# just saying that the bot is on
	print('Client: {0.user.name}#{0.user.discriminator}'.format(client))
	print('Client ID: {0.user.id}\n'.format(client))

@client.command(pass_context = True)
async def help(ctx):
	embed=discord.Embed(color=0x62f3ff)
	embed.add_field(name='!help', value='Sends this message.', inline=False)
	return await ctx.send(embed=embed)

	await ctx.send(embed=embed)

@client.command(pass_context = True)
async def game(ctx, players=2):
	await ctx.send('`if else if else if else`')

client.run(token)