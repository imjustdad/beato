# TODO
- add exception handlers for if either process crashes to restart the process
- change the database write operations to return the newly created document to then use the app_logger.info() call to display the document rather than the formatted string
- implement passing a switch when running the app for the loggers
- ~~fix the pymonogo logger as its set to WARNING to suppress heartbeat logs, but then suppress all other pymonogo logs as well~~
    - configured pymongo.command logger to write to terminal and pymongo.log for database operations
- add exception handlers for praw and pymongo operations for better app stability
- setup a trigger on atlas to send a webhook to a discord webhook for easy notifications
- still would like to setup a simple web app just for funsies for me

# Running the app
i think this is just ```pip install -r requirements.txt``` to install the dependencies...something like that or you can likely just install the two that are in there on your own. and then ```python app.py``` to run the app.

# Discord Notifications
it's not complete. i put something together real quick just to test it out, but it does work if you put a discord webhook url in your environmental variables

# Mongo Atlas
this is setup on a free tier which gives you 512mb of database storage. should be plenty for a long time for what's being stored.
i need to add your email to the project so you can login and see the db as well as update the security settings to allow all traffic which should be fine since it's password protected.

# Rate Limiting
I've configured praw's rate limiter to a maximum of 10 minutes (600 seconds). Mostly because I don't think I can set it higher and because if the rate limit response from reddit exceeds this specified time, praw will throw an exception which is not handled anywhere and will crash the process for an unhandled exception. you get 1000 request per 600 seconds provided by reddit. i ran this for over an hour and never got a rate limit error.

# Logging
logging is a bit wild in here. it's not the most elegant solution, but it mostly works.
- when calling app_logger.info(), will output to the terminal and app.log file while app_logger.debug() will write only to the app.log file.
- praw and praw_core loggers, they were originally writing to terminal, but they're super verbose and should really only do anything when doing something like ```python app.py --debug```, so i've set these loggers to WARNING to simply suppress them for now. 
- ~~pymongo is even more verbose as the heartbeat logs just absolutely spam the terminal. I was working on trying to look for pymongo.command logs (like db operations), but i didn't finish testing this. maybe changing the level to INFO from WARNING might make it work.~~
- I fixed this kind of by just configuring the pymongo.command logger so only database operations are written to the terminal and pymongo.log
    - you don't call the praw/praw_core/pymongo loggers like you do app_logger. you just give it a logger config and it does the rest for you
    - also, the praw.log gets a little goofy sometimes because two separate processes are writing to this log so sometimes logs overlap, but it's never been so bad that it was unreadable.

# Error Handling
so...there's not much error handling. sorry :grimacing:

# Streaming vs Polling
I've setup praw to stream both comments and submissions, however, these streams function on a subreddit level. You're unable to stream comments for a specific submission. I figured this would be ok, since it seems like the interest is to match any given comment rather than comments specifically from a given submission. I've tried to remediate this a bit within the database by storing additional data of the matched streaming comments like which submission it belongs within.

it's worth noting (based on glances)...the app does about 125 request per 600 seconds (10 minutes). not bad, but seems chatty, idk. and streaming is actually not really streaming, praw just abstracts polling reddit's api from you. this ballparks to 60 request per streaming function...probably... kinda lame, but it does give you nice configuration over interacting with the reddit api.

# Multi Processing
You may have noticed there are two praw.Reddit(). one on the stream_submissions() function and one on the stream_comments() function. Reading through the praw documentation, they recommended utilizing multi processing for a very similar use case to what you're trying to do so that you can have one process constantly stream new submissions and another process stream comments. so. hopefully this works alright. EDITORS NOTE: it slaps.

# Script Secrets
so i had a big long thing wrote out here initially, but the gist is you need to setup environmental variables or hard code values in the Environmental Variables region in the app. i setup mine by configuring ```~/.bashrc``` and it works as intended. use the example .example.env file to see what all environmental variables need to be set.

# Systemd
so I kind of assumed you'd be using Linux to run this script. if so, an option would be to create a systemd service. here's one that might work. Also, WSL might be an option, but WSL can be a bit finicky at times. this is not tested btw. 

```bash
[Unit]
Description=Reddit Bot
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/your/script.py
Restart=always
User=yourusername
WorkingDirectory=/path/to/your/script
StandardOutput=append:/var/log/beato_bot.log
StandardError=append:/var/log/beato_bot_error.log

[Install]
WantedBy=multi-user.target
```

# ChatGPT Regex Recommendation
During an early discussion with ChatGPT, I asked about a consolidated regex expression. Below is what it gave me. Don't feel obligated to use this, I just wanted to post it somewhere outside of the code base :smile:

```python
re.search((\s|^)((?:I|ii|iii|IV|V|vi|vii|1|2|3|4|5|6|7)\s*(?:I|ii|iii|IV|V|vi|vii|1|2|3|4|5|6|7)\s*(?:I|ii|iii|IV|V|vi|vii|1|2|3|4|5|6|7)\s*(?:I|ii|iii|IV|V|vi|vii|1|2|3|4|5|6|7)?)|([A-Ga-g](?:#|b)?)(m|7|m7|dim|aug|sus[24]?|6|9|11|13|#9|b5|b9|#5|maj|maj7|maj9|7b5|m7b5)?(\?+|!+|\.+|\,+)?(\s|$))
```