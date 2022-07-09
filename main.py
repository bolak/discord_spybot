import discord
from reporter import Channel_Reporter
from discord.ext import commands
import sys
token = "INSERT YOUR BOT TOKEN HERE"#change this
intents = discord.Intents.default()
app_id = "INSERT YOUR APP ID HERE" #change this
command_prefix = '>>'

def main():

	bot = commands.Bot(command_prefix=command_prefix)
	bot.add_cog(Channel_Reporter(bot = bot, intents=intents, application_id=app_id))
	bot.run(token) 

if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		sys.exit()