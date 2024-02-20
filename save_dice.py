import json
import re
from slugify import slugify

ROOT_DATA = '/data/'


class DiceItem:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return f"{self.name} {self.value}"

    def __repr__(self):
        return self.__str__()

    def get_json(self):
        return self.__dict__


class DiceTable:

    def __init__(self, player_id):
        self.player_id = player_id
        self.dice_table = []
        self.file_name = f'{ROOT_DATA}{self.player_id}.db'
        self.load_dice_table()

    def load_dice_table(self):
        try:
            f = open(self.file_name)
        except FileNotFoundError:
            self._save_dice_table([])
            f = open(self.file_name)
        except Exception as e:
            print(f"Exception in load file {e}")
            return []

        data = json.load(f)
        if not data:
            return []
        self.dice_table = []
        for i in data:
            self.dice_table.append(DiceItem(i['name'], i['value']))

    def _save_dice_table(self, data):
        with open(self.file_name, 'w') as f:
            f.truncate(0)
            json.dump([i.get_json() for i in data], f)

    async def add(self, name, value):
        # Capitalize the first letter of the name
        name = name.capitalize()
        self.dice_table.append(DiceItem(name, value))
        self.dice_table = sorted(self.dice_table, key=lambda x: x.name, reverse=False)
        self._save_dice_table(self.dice_table)

    async def reset(self):
        self.dice_table = []
        self._save_dice_table(self.dice_table)

    async def remove_index(self, index):
        self.dice_table.remove(self.dice_table[index-1])
        self._save_dice_table(self.dice_table)

    async def show(self, context):
        if len(self.dice_table) == 0:
            return await context.send("Nenhum dado registrada")

        text = f"{context.author.nick} tem os seguintes dados: \n"
        text += "```ml\n"
        # Determine the maximum length of names for proper alignment
        max_name_length = max(len(item.name) for item in self.dice_table)
        for i, item in enumerate(self.dice_table):
            text += f"{i + 1}: {item.name:<{max_name_length}} {item.value} \n"
        text += "```"

        return await context.send(text)

