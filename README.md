# Simple roll dice with Advantage and Disadvantage options for discord

Roll n die 

## Get our own bot

To get your own bot, follow these steps:
- download or clone this repository.
- copy the `config.json.tpl` file to `config.json`
- edit the `config.json` file

- follow steps for the service you want (see below)

### Discord bot

- copy the `secrets.json.tpl` file to `secrets.json`
- edit the `secrets.json` file
- replace `<your_discord_token>` by your discord token
- save the file and quit
- start the bot with the command `python3 discord_client.py`

[comment]: <> (docker build . -t roll-dice && docker run -d roll-dice)

New version: 
docker-compose up -d