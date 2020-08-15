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
		spc = '      '
		lines = []

		lines.append('It\'s {0.turn.name}\'s turn!'.format(self)) # line 0
		lines.append(f':blue_square:{spc}:regional_indicator_a::regional_indicator_b::regional_indicator_c::regional_indicator_d::regional_indicator_e:') # line 1
		lines.append('') # line 2
		lines.append(f':one:{spc}') # line 3
		for i in range(1,6): lines[3] += colors[self.board[(i,1)]]
		lines.append(f':two:{spc}') # line 4
		for i in range(1,6): lines[4] += colors[self.board[(i,2)]]
		lines.append(f':three:{spc}') # line 5
		for i in range(1,6): lines[5] += colors[self.board[(i,3)]]
		lines.append(f':four:{spc}') # line 6
		for i in range(1,6): lines[6] += colors[self.board[(i,4)]]
		lines.append(f':five:{spc}') # line 7
		for i in range(1,6): lines[7] += colors[self.board[(i,5)]]

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

		# creating game board
		game_board = await games[reaction.message.id].channel.send(games[reaction.message.id].board_msg())
		games[reaction.message.id].message = game_board
		return
		
	# editing embed
	embed=discord.Embed(title='Game of E', description='Waiting for players... [{0}/{1.player_count}]'.format(len(games[reaction.message.id].players),games[reaction.message.id]), color=0x00ff2a)
	embed.add_field(name='React to join!', value='✅', inline=False)

	waiting = await games[reaction.message.id].message.edit(embed=embed)

@client.event
async def on_message(message):

	if message.author.bot: return # bot check
	msg = message.content.lower()

	# ------------ check if message is a move
	letters = ['a','b','c','d','e']
	numbers = ['1','2','3','4','5']

	try:
		if (len(msg) == 2 and msg[0] in letters and msg[1] in numbers) or (len(msg) == 3 and msg[0] in ['-','|'] and msg[1] in letters and msg[2] in numbers):
			# check if message is in game channel and is author's turn
			for game in games:
				if games[game].channel == message.channel and games[game].turn == message.author:
					# taking turn

					# ------------ placing
					if len(msg) == 2:
						# converting letter,number into tuple
						coords = (int(numbers[letters.index(msg[0])]),int(msg[1]))

						# check if board spot is taken
						if games[game].board[coords] == 0:
							# changing board
							games[game].board[coords] = games[game].players.index(message.author)+1

						else: break

					# ------------ switching
					if len(msg) == 3:
						target_coords = (int(numbers[letters.index(msg[1])]),int(msg[2]))
						
						# ------------ horizontal switch
						if msg[0] == '-':
							# out of bounds check
							if target_coords[0] in [1,5]: break

							# target is owned by player
							if games[game].board[target_coords] != games[game].players.index(message.author)+1: break

							# sides are same check
							l_coord, r_coord = (target_coords[0]-1, target_coords[1]), (target_coords[0]+1, target_coords[1])
							if games[game].board[l_coord] != games[game].board[r_coord]: break

							# changing board
							games[game].board[target_coords] = games[game].board[l_coord] # center

							games[game].board[l_coord] = games[game].players.index(message.author)+1 # left
							games[game].board[r_coord] = games[game].players.index(message.author)+1 # right

							
						# ------------ vertical switch
						elif msg[0] == '|':
							# out of bounds check
							if target_coords[1] in [1,5]: break

							# target is owned by player
							if games[game].board[target_coords] != games[game].players.index(message.author)+1: break

							# sides are same check
							u_coord, d_coord = (target_coords[0], target_coords[1]-1), (target_coords[0], target_coords[1]+1)
							if games[game].board[u_coord] != games[game].board[d_coord]: break

							# changing board
							games[game].board[target_coords] = games[game].board[u_coord] # center

							games[game].board[u_coord] = games[game].players.index(message.author)+1 # up
							games[game].board[d_coord] = games[game].players.index(message.author)+1 # down

					# ------------ 3 in a row/column

					# vertical 3
					def vertical():
						for y in range(2,5):
							for x in range(1,6):
								if games[game].board[(x,y)] != 0 and games[game].board[(x,y-1)] == games[game].board[(x,y)] and games[game].board[(x,y)] == games[game].board[(x,y+1)]:
									for i in range(1,6):
										games[game].board[(x,i)] = games[game].board[(x,y)]

					# horizontal 3
					def horizontal():
						for x in range(2,5):
							for y in range(1,6):
								if games[game].board[(x,y)] != 0 and games[game].board[(x-1,y)] == games[game].board[(x,y)] and games[game].board[(x,y)] == games[game].board[(x+1,y)]:
									for i in range(1,6):
										games[game].board[(i,y)] = games[game].board[(x,y)]

					# looping
					previous = None
					while previous != games[game].board:
						previous = dict(games[game].board)

						vertical()
						horizontal()

					v_h = dict(games[game].board)

					horizontal()
					vertical()

					if v_h != games[game].board:
						await message.channel.send('EXECUTE NUKE')
						
						
					# ------------ ending turn
					games[game].turn = games[game].players[games[game].players.index(message.author)-1]

					await games[game].message.edit(content=games[game].board_msg())
					await message.delete()

					break
	except IndexError:
		pass

	# process as command
	await client.process_commands(message)


client.run(token)