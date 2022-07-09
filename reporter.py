import discord
from discord.ext import commands, tasks
from gatherer import Channel_gatherer
from captcha_handler import Captcha_handler
import io
import time
import json
import threading
import asyncio
import nest_asyncio
from queue import Queue
import sys
from os.path import exists

nest_asyncio.apply()

PATH = 'names.list'
REPORT_CHANNEL_ID = 976504870251155455 #change this

with open('self.token','r') as file:
	self_token = file.read().strip()

def format_msg(channels):
	msg = '['
	for i in range(len(channels)):
		my_dict = {'name':channels[i][0],'topic':channels[i][1],'visible':channels[i][2]}
		msg += json.dumps(my_dict,indent=4)
		if i != len(channels) - 1:
			msg += ',\n'
	msg += ']'
	return msg

def format_list(names):
	msg = '\n**Guilds tracking list**:\n```diff\n'
	for i in range(len(names)):
		msg += f'+	{i} - {names[i]}\n'
	msg += '```'
	return msg

def format_file(channels,name):
		msg = format_msg(channels)
		msg_b = bytes(msg,'utf-8')
		file = io.BytesIO(msg_b)
		file = discord.File(file,filename=name+'.json')
		return file

def save_names(names):
	with open(PATH,'w') as file:
		for name in names:
			file.write(name+'\n')

def save_blacklist(channel_blacklist):
	with open('blacklist.txt','w') as file:
		for channel_id in channel_blacklist:
			file.write(str(channel_id)+'\n')

class Channel_Reporter(commands.Cog):

	running = True
	channel = None
	bot = None
	events = {}
	threads = []
	names = []
	refresh_ctx = None
	channel_blacklist = []

	def __init__(self ,bot : commands.bot.Bot ,intents: discord.Intents, application_id: int):
		self.bot = bot
	
	@tasks.loop(seconds=0.25)
	async def on_change_loop(self):
		'''
		Listening for events on the gatherer thread
		'''
		event = self.on_change[0]
		queue = self.on_change[1]
		
		for thread in self.threads:
			if not thread.is_alive():
				self.threads.remove(thread)
				await self.init_gatherer()
		
		if not queue.empty():
			package = await queue.get()
			channel = package[0]
			kind = package[1]
			await self.handle_changes(channel,kind)
			#event.clear()

	def start_thread(self, events : list ,names : list):
		async def run():
			captcha_handler = Captcha_handler()
			client = Channel_gatherer(captcha_handler = captcha_handler)

			client.events = events
			client.names = names
			client.on_change = self.on_change
			client.proxy = 'de.proxiware.com:29549'
			
			client.run(self_token)
			
		asyncio.run(run())
		
	async def init_gatherer(self):
		#start thread
		print('-- Starting gatherering threads --')
		thread = threading.Thread(target=self.start_thread, args=(self.events,self.names,), daemon=True)
		thread.start()
		self.threads.append(thread)
	

	@commands.Cog.listener()
	async def on_ready(self):
		'''
		After login init proccess. load names.guilds,channels and start thread(s)
		'''	
		print(self.bot.guilds)
		if not len(self.threads): # check if a desconect happened (on_ready is called again)
			print('-- Bot initiated --')
			self.load_names()
			self.on_change = [threading.Event(),asyncio.Queue()]#for on_change communication
			for command in self.get_commands(): #dic of command : [event queue] 
				self.events[command.name] = [threading.Event(),Queue()]
				if command.name == 'refresh':
					self.refresh_ctx = command#get command 
			self.channel =  self.bot.get_channel(REPORT_CHANNEL_ID)
			try:
				await self.init_gatherer()#start thread
			except Exception as e:
				print(e)
				self.bot.close()
			self.load_blacklist()	
			await self.load_guilds()
			await self.send_msg(f'Bot initiated!')
			self.on_change_loop.start()
		
	async def handle_changes(self,channel,kind):
		'''
		Formats and sends channel changes as json to channel
		'''
		await self.load_guilds()
		for guild in self.guilds_temp:
			if channel.guild.name == guild.name:
				if channel.id not in self.channel_blacklist:#blacklist check

					hidden  = channel.permissions_for(channel.guild.me).view_channel
					channel_name = channel.name
					channel_type = channel.type.name
					channel_topic = ''

					if channel_type == 'text' or channel_type == 'forum' or channel_type == 'stage':
						channel_topic = channel.topic
					
					channel_temp = [[channel_name,channel_topic,hidden]]
						
					file = format_file(channel_temp,channel.guild.name+f'-{kind}')
					await self.send_msg(f'Channel (**{channel.id}**) **{kind}d** on **__{guild.name}__**!"',file)
		


	async def send_msg(self,msg,file=None):
		await self.channel.send(msg,file = file)
	
	def load_blacklist(self):
		self.channel_blacklist = []
		if not exists('blacklist.txt'):
			with open('blacklist.txt','w') as file:
				pass	
		with open('blacklist.txt','r') as file:
			for channel_id in file:
				channel_id = channel_id.split('\n')[0]
				if len(channel_id):
					self.channel_blacklist.append(int(channel_id.strip()))
	
	def load_names(self):
		self.names = []
		if not exists(PATH):#create file
			with open(PATH,'w') as file:
				pass
		with open(PATH,'r') as file:
			for name in file:
				name = name.split('\n')[0]
				if len(name):
					self.names.append(name.strip())
	
	async def load_guilds(self):
		command_name = 'refresh'
		queue,event = self.gather_com(command_name)
		guilds = queue.get()
		self.guilds_temp = guilds
		 	

	def gather_com(self,command_name):
		event = self.events[command_name][0]
		queue = self.events[command_name][1]
		event.set()#send event to thread execute command
		return queue,event

	@commands.command()
	async def ban(self,ctx):
		'''
		>>ban [channel_id]
		# Blacklists a channel
		'''
		channel_id = int(ctx.message.content[5:].strip())
		if channel_id not in self.channel_blacklist:
			self.channel_blacklist.append(channel_id)
			save_blacklist(self.channel_blacklist)
			await self.send_msg(f'>**{channel_id}** blacklisted!')
			print(f'{channel_id} blacklisted')
		else:
			await self.send_msg(f'>**{channel_id}** already blacklisted!')
	
	@commands.command()
	async def unban(self,ctx):

		'''
		>>unban [channel_id]
		# Unblacklists a channel
		'''
		channel_id = int(ctx.message.content[7:].strip())
		if channel_id in self.channel_blacklist:
			self.channel_blacklist.remove(channel_id)
			save_blacklist(self.channel_blacklist)
			await self.send_msg(f'>**{channel_id}** unblacklisted!')
			print(f'{channel_id} unblacklisted')
		else:
			await self.send_msg(f'>**{channel_id}** is not blacklisted!')
	@commands.command()
	async def refresh(self,ctx):
		'''
		>>refresh
		# Returns .txt files with all channels informations from all guilds on track list
		'''
		command_name = ctx.command.name
		queue,event = self.gather_com(command_name)
		guilds = queue.get()
		self.guilds_temp = guilds
		for guild in guilds:
			file = format_file(guild.channels,guild.name)
			await self.send_msg(f'Full **__{guild.name}__** channel list :',file) 	

	@commands.command()
	async def add(self,ctx):
		'''
		>>add [invite link/guild name]
		
		# Adds a guild to track list
		# (Use invite link if self-bot is not already member of guild) 
		'''
		command_name = ctx.command.name
		queue,event = self.gather_com(command_name)
		temp_str = ctx.message.content[5:].strip()
		queue.put(temp_str)

		while event.is_set():#wait gatherer finish refreshing
			pass
		
		temp_name = queue.get()
		print(temp_name,self.names)
		if not len(temp_name):
			await self.send_msg(f'> __**{temp_str}**__ not found!')
		elif temp_name in self.names:
			await self.send_msg(f'> __**{temp_name}**__ is already on track list!')
		else:
			self.names.append(temp_name)
			save_names(self.names)
			await self.send_msg(f'> __**{temp_name}**__ added!')	

		self.load_names()
		await self.load_guilds()
	@commands.command(name='del')
	async def  dell(self,ctx):
		'''
		>>del [guild name]
		# Deletes a guild from the track list
		'''
		temp_name = ctx.message.content[5:].strip()
		command_name = ctx.command.name
		queue,event = self.gather_com(command_name)
		queue.put(temp_name)

		if temp_name in self.names:
			self.names.remove(temp_name)
			save_names(self.names)
			await self.channel.send(f'> __**{temp_name}**__ deleted!')
		else:
			await self.channel.send(f'> __**{temp_name}**__ not found!')
		self.load_names()
	
	@commands.command()
	async def list(self,ctx):
		'''
		>>list
		# Lists track list
		'''
		self.load_names()
		msg = format_list(self.names)
		await self.channel.send(msg)

	@commands.Cog.listener()
	async def on_command_error(self,ctx,error):
		pass