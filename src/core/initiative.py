import os
import json
from slugify import slugify

ROOT_DATA = os.path.join(os.getcwd(), 'data/')


class InitItem:
    def __init__(self, name, value, dex=0, condition=""):
        self.name = name
        self.value = value
        self.dex = dex
        self.condition = condition

    @property
    def total(self):
        return self.value + self.dex

    def __str__(self):
        return f"{self.name} {self.total}"

    def __repr__(self):
        return self.__str__()

    def get_json(self):
        return self.__dict__


class InitiativeFile:
    def __init__(self, path=ROOT_DATA):
        self.path = path

    def get_filename(self, channel):
        return os.path.join(self.path, f"{slugify(channel)}.db")

    def load_initiative_table(self, channel):
        file_name = self.get_filename(channel)
        try:
            f = open(file_name)
        except FileNotFoundError:
            self.save_initiative_table(channel, [])
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

    def save_initiative_table(self, channel, data):
        file_name = self.get_filename(channel)
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        with open(file_name, 'w') as f:
            f.truncate(0)
            json.dump([i.get_json() for i in data], f)


class InitTable:

    current = 1
    initiative_table = []
    initiative_last_msg = None

    def __init__(self, path=ROOT_DATA, channel=''):
        self.initiative_file = InitiativeFile(path)
        self.load_init_table(channel)
    
    def load_init_table(self, channel: ''):
        if channel:
            self.initiative_table = self.initiative_file.load_initiative_table(
                channel)

    async def add(self, channel, name, value, dex="0"):
        self.load_init_table(channel)
        # Capitalize the first letter of the name
        name = name.capitalize()
        self.initiative_table.append(InitItem(name, int(value), int(eval(dex))))
        self.initiative_table = sorted(self.initiative_table, key=lambda x: x.total, reverse=True)
        await self._save(channel)

    async def reset(self, channel):
        self.initiative_table = []
        self.current = 1
        await self._save(channel)

    async def add_condition(self, channel, index, condition):
        if not self.initiative_table:
            self.load_init_table(channel)
        self.initiative_table[index-1].condition = condition
        await self._save(channel)

    async def remove_condition(self, channel, index):
        await self.add_condition(channel, index, '')

    async def remove_index(self, channel, index):
        if not self.initiative_table:
            self.load_init_table(channel)
        self.initiative_table.remove(self.initiative_table[index-1])

        # Adjust the current index if necessary
        if index < self.current:
            self.current -= 1

        if self.current > len(self.initiative_table) or self.current < 1:
            self.current = 1

        await self._save(channel)

    async def next(self, channel):
        self.load_init_table(channel)
        self.current += 1
        if self.current > len(self.initiative_table):
            self.current = 1
        return self.initiative_table[self.current - 1]

    async def previous(self, channel):
        self.load_init_table(channel)
        self.current -= 1
        if self.current < 1:
            self.current = len(self.initiative_table)
        return self.initiative_table[self.current - 1]

    async def _save(self, channel):
        self.initiative_file.save_initiative_table(channel,
                                                   self.initiative_table)

    async def show(self, channel, context):
        self.load_init_table(channel)

        if len(self.initiative_table) == 0:
            return await context.send("No initiative found")

        # Determine the maximum length of names for proper alignment
        max_name_length = max(len(item.name) for item in self.initiative_table)
        # Set minimum column width for names to keep table aligned
        max_name_length = max(max_name_length, 10)

        # Header for the table
        header = f"{'ID':<5} {'Name':<{max_name_length}} {'Init':<5} {'Dex':<5} {'Total':<5} {'Condition'}"
        separator = "-" * (len(header) + 5)  # Adjust the separator length

        # Start with the table header
        table = f"```ml\n{header}\n{separator}\n"

        # Populate the table rows
        for i, item in enumerate(self.initiative_table):
            condition = f"{item.condition}" if item.condition else ""
            signal = "+" if item.dex >= 0 else "-"
            item_dex_str = abs(item.dex)
            is_current = ">" if i == self.current - 1 else " "

            # Format each row of the table
            table += (
                f"{is_current} {i + 1:<3} {item.name:<{max_name_length}} "
                f"{item.value:<5} {signal} {item_dex_str:<3} {item.total:<5} {condition}\n"
            )

        table += "```"  # Close the code block

        # Send the table as a message
        return await context.send(table)
