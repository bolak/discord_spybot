import selfcord
import aiohttp
import json
from asyncio import sleep

class Captcha_handler(selfcord.CaptchaHandler):
	token = "INSERT YOUR CAPMONSTER TOKEN HERE" #change this
	user_agent = None
	proxy = { #change this
	'type' : 'http',  
	'addr' : '0.0.0.0',
	'port' : 80,
	'login' : 'username',
	'pwd' : 'password'
	}

	async def fetch_token(self,data, proxy, proxy_auth, /):
		#print(data)
		token = data['captcha_sitekey']
		request = {
			"clientKey" : self.token,
			"task" : {
				"type" : "HCaptchaTask",
				"websiteURL" : "https://discord.com/",
				"websiteKey" : token,
				"isInvisible" : True,
				"data" : data['captcha_rqdata'],
				"proxyType": self.proxy['type'],
				'proxyAddress': self.proxy['addr'],
				'proxyPort': self.proxy['port'],
				'proxyLogin': self.proxy['login'],
				'proxyPassword': self.proxy['pwd'],
				'userAgent': self.user_agent,
			}
		}
		async with aiohttp.ClientSession() as session:
			async with session.post("https://api.capmonster.cloud/createTask", json=request) as r:
				response = json.loads(await r.text())
				task_id = response['taskId']


			request = {
				"clientKey" : self.token,
				"taskId" : task_id
			}
			print(f'captcha taskID {task_id}')
			# keep on looping until getting the token, time efficient.
			while True:
				await sleep(0.3)
				async with session.post("https://api.capmonster.cloud/getTaskResult", json = request) as r:


					response = json.loads(await r.text())
					status = response['status']
					print(f'captcha status:{status}')
					if status == 'processing':
						 pass
					else:
						try:
							return response["solution"]["gRecaptchaResponse"]		
						except Exception:
							print("something wrong is not right")