import os
import json
import re
from slugify import slugify

# ROOT_DATA get relative path from here + data/
ROOT_DATA = os.path.join(os.path.dirname(__file__), 'data/')


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
    file_name = f'{ROOT_DATA}{slugify(channel)}.db'
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
    file_name = f'{ROOT_DATA}{slugify(channel)}.db'
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    with open(file_name, 'w') as f:
        f.truncate(0)
        json.dump([i.get_json() for i in data], f)


class InitTable:

    current = 1
    initiative_table = []
    initiative_last_msg = None

    async def add(self, channel, name, value, dex=0):
        self.initiative_table = load_initiative_table(channel)
        # Capitalize the first letter of the name
        name = name.capitalize()
        self.initiative_table.append(InitItem(name, int(value), int(dex)))
        self.initiative_table = sorted(self.initiative_table, key=lambda x: x.total, reverse=True)
        save_initiative_table(channel, self.initiative_table)

    async def reset(self, channel):
        self.initiative_table = []
        self.current = 1
        save_initiative_table(channel, self.initiative_table)

    async def add_condition(self, channel, index, condition):
        if not self.initiative_table:
            self.initiative_table = load_initiative_table(channel)
        self.initiative_table[index-1].condition = condition
        save_initiative_table(channel, self.initiative_table)

    async def remove_condition(self, channel, index):
        if not self.initiative_table:
            self.initiative_table = load_initiative_table(channel)
        self.initiative_table[index-1].condition = ""
        save_initiative_table(channel, self.initiative_table)

    async def remove_index(self, channel, index):
        if not self.initiative_table:
            self.initiative_table = load_initiative_table(channel)
        self.initiative_table.remove(self.initiative_table[index-1])

        # Adjust the current index if necessary
        print(index, self.current, len(self.initiative_table))
        if index < self.current:
            self.current -= 1

        if self.current > len(self.initiative_table) or self.current < 1:
            self.current = 1

        save_initiative_table(channel, self.initiative_table)

    async def next(self, channel):
        self.initiative_table = load_initiative_table(channel)
        self.current += 1
        if self.current > len(self.initiative_table):
            self.current = 1
        return self.initiative_table[self.current - 1]

    async def previous(self, channel):
        self.initiative_table = load_initiative_table(channel)
        self.current -= 1
        if self.current < 1:
            self.current = len(self.initiative_table)
        return self.initiative_table[self.current - 1]

    async def show(self, channel, context):
        self.initiative_table = load_initiative_table(channel)

        if len(self.initiative_table) == 0:
            return await context.send("Nenhuma iniciativa registrada")

        text = "```ml\n"
        # Determine the maximum length of names for proper alignment
        max_name_length = max(len(item.name) for item in self.initiative_table)
        print(f"Current position: {self.current}")
        for i, item in enumerate(self.initiative_table):
            condition = f"|{item.condition}|" if item.condition else ""
            signal = "+" if item.dex > 0 else "-"
            item_dex_str = item.dex if item.dex > 0 else item.dex * -1
            spacer = " " if item.value < 10 else ""
            is_current = "> " if i == self.current - 1 else ""
            # Adjust the formatting here
            text += f"{is_current}{i + 1}: {item.name:<{max_name_length}} [{item.value}]{spacer} {signal} {item_dex_str:<2} = Total: {item.total:<2} {condition}\n"
        text += "```"

        return await context.send(text)


async def clean_dex(value):
    negative = True if "-" in value else False
    return int(re.sub('[^0-9]', '', value)), negative
