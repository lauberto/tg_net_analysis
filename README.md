# tg_net_analysis
Network analysis of TG channels


## Getting access data
Follow the instructions [here](https://docs.telethon.dev/en/stable/basic/signing-in.html) to get an _API ID_ and and _api key_.

Use an .env file to store your API secrets, making sure that the .env file is not tracked by adding it to .gitignore.

```pip install python-dotenv```

Create a .env file that looks something like:
```
API_ID=1234
API_HASH=abc123
``` 

See how the variables are loaded in the python scrips.