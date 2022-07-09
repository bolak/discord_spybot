a spy bot that joins discord servers and alerts you when new hidden channels are created. 
this has generated significant alpha for me during the past year

the bot is made of 2 key parts:
- a self-bot - the bot actually joining the servers
- a reporting bot - an actual bot used for reporting & controlling the bot

how to use:
- add proxy provider settings
- add your reporting bot token in "self.token"
- add your self-bot token (a normal discord account basically)
- add capmonster api key for captcha solving
- add your server & channel id for reporting
- use bot commands to add to your desired servers
- wait for alpha
- PROFIT

there are probably other stuff i messed up while redacting my keys & tokens but idc really

TODO: 
- add message spying function to raise an alert when specific keywords or regex is matched (tx id, eth addys, api keys, etc)
- make code pretty
- docker container
- proper readme

help command example:

```
ninjie: >>help
Channel_Reporter:
  add     >>add [invite link/guild name]
  ban     >>ban [channel_id]
  del     >>del [guild name]
  list    >>list
  refresh >>refresh
  unban   >>unban [channel_id]
​No Category:
  help    Shows this message

Type >>help command for more info on a command.
You can also type >>help category for more info on a category.```
