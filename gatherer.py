import selfcord
import io
import time
import json
from guild import Guild
from selfcord.ext import tasks,commands
import threading
from queue import Queue
import validators
import asyncio

class Channel_gatherer(selfcord.Client):
	
	bot = None
	names = None
	events = []
	first = True
	func_dict = None
	guilds_temp = []
	on_change = None

	def load_names(self):
		self.names = []
		with open('names.list','r') as file:
			for name in file:
				name = name.split('\n')[0]
				if len(name):
					self.names.append(name.strip())
	
	@tasks.loop(seconds=0.25)
	async def commands_loop(self): 
		'''
		Handle thread communication in loop, executes right command and clear thread event
		'''
		for command,_list in self.events.items():
			event = _list[0]
			queue = _list[1]
			if event.is_set():
				print(f'Running {command}')
				await self.func_dict[command](queue)
				event.clear()

	
	async def on_ready(self):
		'''
		After login init proccess. load commands and guilds, start thread handler loop (commands_loop)
		'''
		if self.first:

			user_agent = self.http.user_agent
			self.http.captcha_handler.user_agent = user_agent
			
			self.load_func()
			await self.load_guilds()
			print(f'SB-{self.user} initiated')
			self.first = False
			self.commands_loop.start()
			

	def load_func(self):

		async def refresh(queue):
			'''
			!refresh
			# Returns .txt files with all channels informations from all guilds on track list
			'''
			await self.load_guilds()
			queue.put(self.guilds_temp)
		
		async def add(queue):
			'''
			!add [invite link/guild name]
			
			# Adds a guild to track list
			# (Use invite link if self-bot is not already member of guild) 
			'''
			temp_str = queue.get()
			temp_name = ''
			
			if validators.url(temp_str):#check if it is a invite url
				temp_url = temp_str

				if temp_url[-1] == '/':#for some reason fetch_invite does not like / at the end
					temp_url = temp_url[:-1]
				try:
					invite = await self.fetch_invite(temp_url)
					guild = await invite.use()
					temp_name = guild.name
				except Exception as e:
					print(e)
			else:
				for guild in self.guilds:
					if temp_str == guild.name:
						temp_name = temp_str
			queue.put(temp_name)
			# if temp_name not in self.names and len(temp_name):
			# 	self.names.append(temp_name)

		async def dell(queue):
			temp_name = queue.get()
			if temp_name in self.names:
				self.names.remove(temp_name)
				
		
		self.func_dict = {'refresh':refresh,'add':add,'del':dell}
		
	async def get_channels(self,name):
		channels_temp = []

		for guild in self.guilds:  # iterate guilds list
			if guild.name == name:

				for channel in guild.channels:
					me = guild.me

					hidden  = channel.permissions_for(me).view_channel
					channel_name = channel.name
					channel_type = channel.type.name
					channel_topic = False
					if channel_type == 'text' or channel_type == 'forum' or channel_type == 'stage': # some channel objects have no .topic
						channel_topic = channel.topic
					
					channel_temp = [channel_name,channel_topic,hidden]
					
					channels_temp.append(channel_temp)
		
		return channels_temp

	async def load_guilds(self):
		self.load_names()
		ttg = []
		for name in self.names:
			channels = await self.get_channels(name)
			ttg.append(Guild(name,channels))
		self.guilds_temp = ttg

	async def handle_changes(self,channel,kind):
		'''
		Communication with main thread
		'''
		event = self.on_change[0]
		queue = self.on_change[1]
		package = [channel,kind]
		#print('a')

		#event.set()
		await queue.put(package)

	#listen to discord events
	async def  on_guild_channel_delete(self,channel):
		await self.handle_changes(channel,'delete')
	
	async def on_guild_channel_update(self,before,after):
		await self.handle_changes(after,'update')

	async def  on_guild_channel_create(self,channel):
		await self.handle_changes(channel,'create')
	