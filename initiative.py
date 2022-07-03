import json
import re
from slugify import slugify


class InitItem:
    def __init__(self, name, value, dex=0, condition=""):
        self.name = name
        self.value = value
        self.dex = dex
        self.total = value + dex
        self.condition = condition

    def __str__(self):
        return f"{self.name} {self.total}"

    def __repr__(self):
        return self.__str__()

    def get_json(self):
        return self.__dict__


def load_initiative_table(channel):
    file_name = f'{slugify(channel)}.db'
    try:
        f = open(file_name)
    except FileNotFoundError:
        save_initiative_table(channel, [])
        f = open(file_name)
    except Exception as e:
        print(f"Exception in load file {e}")

    data = json.load(f)
    if not data:
        return []
    initiatives = []
    for i in data:
        initiatives.append(InitItem(i['name'], int(i['value']), int(i['dex']), i['condition']))
    return initiatives


def save_initiative_table(channel, data):
    file_name = f'{slugify(channel)}.db'

    with open(file_name, 'w') as f:
        f.truncate(0)
        json.dump([i.get_json() for i in data], f)


class InitTable:

    initiative_table = []

    async def add(self, channel, name, value, dex=0):
        self.initiative_table = load_initiative_table(channel)

        self.initiative_table.append(InitItem(name, int(value), int(dex)))
        self.initiative_table = sorted(self.initiative_table, key=lambda x: x.total, reverse=True)
        save_initiative_table(channel, self.initiative_table)

    async def reset(self, channel):
        self.initiative_table = []
        save_initiative_table(channel, self.initiative_table)

    async def add_condition(self, channel, index, condition):
        self.initiative_table[int(index)-1].condition = condition
        save_initiative_table(channel, self.initiative_table)

    async def remove_condition(self, channel, index):
        self.initiative_table[int(index)-1].condition = ""
        save_initiative_table(channel, self.initiative_table)

    async def remove_index(self, channel, index):
        self.initiative_table.remove(self.initiative_table[int(index)-1])
        save_initiative_table(channel, self.initiative_table)

    async def show(self, channel, context):
        self.initiative_table = load_initiative_table(channel)
        text = "```"
        for i, item in enumerate(self.initiative_table):
            condition = f"|{item.condition}|" if item.condition else ""
            signal = "+" if item.dex > 0 else "-"
            item_dex_str = item.dex if item.dex > 0 else item.dex*-1
            text += f"{i+1}: {item.name} [{item.value}] {signal} {item_dex_str} = Total: {item.total} {condition}\n"
        text += "```"

        # Check how to delete old own messages
        # try:
        #     await context.channel.purge(limit=1)
        # except:
        #     pass

        if len(self.initiative_table) == 0:
            await context.send("Nenhuma iniciativa registrada")
        else:
            await context.send(text)


async def clean_dex(value):
    negative = True if "-" in value else False
    return int(re.sub('[^0-9]', '', value)), negative
