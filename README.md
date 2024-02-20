# Discord bot to roll dice and control initiative table

## Features

- Roll dice
  - Roll a single die
  - Roll multiple dice
  - Roll with advantage
  - Roll with disadvantage
- Roll initiative
  - Add and remove players from initiative table
  - Add conditions to players
  - Sort initiative table


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

[comment]: <> (docker compose up -d)

## Running using docker compose

- run the command `docker-compose up -d`