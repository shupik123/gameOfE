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

games = {}

spc = '      '

class Game:
	def __init__(self, message, channel: discord.TextChannel, starter: discord.User, count: int):
		self.channel = channel
		self.players = [starter]
		self.player_count = count
		self.message = message
		self.turn = starter
		self.started = False
		self.board = {}
		for i in range(1,6):
			for j in range(1,6):
				self.board[(i,j)] = 0

	def board_msg(self):
		colors = {
			0: ':regional_indicator_e:',
			1: ':red_square:',
			2: ':orange_square:',
			3: ':green_square:'
		}

		# creating the string of emoji's
		lines = []

		lines.append(f':blue_square:{spc}:regional_indicator_a::regional_indicator_b::regional_indicator_c::regional_indicator_d::regional_indicator_e:') # line 0
		lines.append('') # line 1
		lines.append(f':one:{spc}') # line 2
		for i in range(1,6): lines[2] += colors[self.board[(i,1)]]
		lines.append(f':two:{spc}') # line 3
		for i in range(1,6): lines[3] += colors[self.board[(i,2)]]
		lines.append(f':three:{spc}') # line 4
		for i in range(1,6): lines[4] += colors[self.board[(i,3)]]
		lines.append(f':four:{spc}') # line 5
		for i in range(1,6): lines[5] += colors[self.board[(i,4)]]
		lines.append(f':five:{spc}') # line 6
		for i in range(1,6): lines[6] += colors[self.board[(i,5)]]

		# combining lines
		lines_str = ''
		for line in lines:
			lines_str += (line + '\n')

		return lines_str
		
@client.event
async def on_ready():
	# just saying that the bot is on
	print('Client: {0.user.name}#{0.user.discriminator}'.format(client))
	print('Client ID: {0.user.id}\n'.format(client))

@client.command(pass_context = True)
async def help(ctx):
	if ctx.author.bot: return # bot check

	embed=discord.Embed(color=0x62f3ff)
	embed.add_field(name='!help', value='Sends this message.', inline=False)
	embed.add_field(name='!game [players, default=2]', value='Starts a game of E.', inline=False)
	embed.add_field(name='!leave', value='Leaves your current game of E.', inline=False)

	await ctx.send(embed=embed)

@client.command(pass_context = True)
async def leave(ctx):
	# removing player from game
	for game in games:
		if ctx.author in games[game].players:
			await games[game].message.delete()
			del games[game]
			return await ctx.send('{0.author.name} has left the game. Game has been removed.'.format(ctx))
	# no game to remove from
	return await ctx.send('You are not currently in a game.')

@client.command(pass_context = True)
async def game(ctx, players=2):
	if ctx.author.bot: return # bot check

	# in game check
	for game in games:
		if ctx.author in games[game].players:
			return await ctx.send('Error: You are already in a game. Use `e!leave` to leave your current game.')

	# player amount check
	if players not in [2,3]:
		return await ctx.send('Error: You must specify a player amount between 2 and 3.')

	embed=discord.Embed(title='Game of E', description=f'Waiting for players... [1/{players}]', color=0x00ff2a)
	embed.add_field(name='React to join!', value='✅', inline=False)

	waiting = await ctx.send(embed=embed)

	# saving into games
	games[waiting.id] = Game(waiting, ctx.channel, ctx.author, players)

	await waiting.add_reaction('✅')

@client.event
async def on_reaction_add(reaction, user):
	if user.bot: return # bot check
	if reaction.message.id not in games: return # return if not game
	if games[reaction.message.id].started: return # return if game already started
	if games[reaction.message.id].players[0] == user: return # return if host
	if len(games[reaction.message.id].players) >= games[reaction.message.id].player_count: return # return if full

	# adding player
	if user not in games[reaction.message.id].players:
		games[reaction.message.id].players.append(user)
	
	# starting game if full
	if len(games[reaction.message.id].players) == games[reaction.message.id].player_count:
		games[reaction.message.id].started = True
		await games[reaction.message.id].message.delete()
		game_board = await games[reaction.message.id].channel.send(games[reaction.message.id].board_msg())
		games[reaction.message.id].message = game_board
		return
		
	# editing message
	embed=discord.Embed(title='Game of E', description='Waiting for players... [{0}/{1.player_count}]'.format(len(games[reaction.message.id].players),games[reaction.message.id]), color=0x00ff2a)
	embed.add_field(name='React to join!', value='✅', inline=False)

	waiting = await games[reaction.message.id].message.edit(embed=embed)


client.run(token)