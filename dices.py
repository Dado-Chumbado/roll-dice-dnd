import random
import json
from stats_db import *
with open("./config.json", "r") as env:
    ENV = json.load(env)

STATS_ENABLE = True if ENV["stats"] == "1" else False


class Die:
    def __init__(self, number, dice, results):
        self.verbose = f"{number}d{dice}"
        self.list_of_result = results
        self.debug = [{'value': d, 'critical': d == int(dice), 'fail': d == 1} for d in results]
        self.dice_base = dice
        self.result = sum(results)

    def __str__(self):
        return f"{self.verbose} => {self.list_of_result}"

    def __repr__(self):
        return self.__str__()

    def get_json(self):
        return self.__dict__

    def larger(self):
        return max(self.list_of_result)

    def smaller(self):
        return min(self.list_of_result)


async def _roll_dice(times, dice):
    if int(times) > 20:
        times = 20

    return [random.randint(1, int(dice)) for _ in range(int(times))]


async def process(context, dices_data):
    print(f"dices_data: {dices_data}")

    repeat = await parse_repeat(dices_data)
    if repeat:
        repeat = int(repeat[0])
        if repeat > 10:
            repeat = 9
        if "x" in dices_data:
            dices_data = dices_data.split("x")[1]
        else:
            dices_data = dices_data.split("*")[1]
    else:
        repeat = 1

    import re
    if re.findall('^(20)(?=[\+\-])', dices_data):
        # Missing a `d`
        print(f"Missing a `d` in command: {dices_data}")
        dices_data = 'd'+dices_data
        print(f"Fixed to: {dices_data}")

    try:
        if int(dices_data):
            # Only modifier
            if re.findall('-(\d+)?', dices_data):
                dices_data = f'd20-{dices_data}'
            else:
                dices_data = f'd20+{dices_data}'

            dices_data = dices_data.replace("++", "+").replace("--", "-")
            print(f"Fixed to: {dices_data}")
    except:
        pass

    dices_positive, dices_negative = await parse_dices(dices_data)
    additional = await parse_additional(dices_data, dices_positive, dices_negative)
    dices_list = []
    for _ in range(0, repeat):
        dices_list.append(await calculate_dices(context, dices_positive, dices_negative, additional))
    return dices_list


async def parse_dices(data):
    import re

    parsed_negative = re.findall('-(\d+)?d(\d+)?', data)
    parsed_positive = re.findall('(\d+)?d(\d+)?', data)
    for pn in parsed_negative:
        if pn in parsed_positive:
            parsed_positive.remove(pn)
    return parsed_positive, parsed_negative


async def parse_repeat(data):
    import re
    return re.findall('(\d)(?=\*)', data) + re.findall('(\d)(?=x)', data)


async def parse_additional(data, positive_dies, negative_dies):
    for item in positive_dies:
        dice = f"{item[0]}d{item[1]}"
        data = data.replace(f"+{dice}", "")
        if dice in data:
            data = data.replace(dice, "")

    for item in negative_dies:
        dice = f"{item[0]}d{item[1]}"
        data = data.replace(f"-{dice}", "")
        if dice in data:
            data = data.replace(dice, "")

    return data


async def calculate_dices(context, dices_positive, dices_negative, additional):
    result_dies = []
    result_minus_dies = []
    only_dices = 0
    try:
        for number, dice in dices_positive:
            number = number if number else 1
            results = await _roll_dice(number, dice)
            only_dices += sum(results)
            result_dies.append(Die(number, dice, results))

        for number, dice in dices_negative:
            number = number if number else 1
            results = await _roll_dice(number, dice)
            only_dices -= sum(results)
            result_minus_dies.append(Die(number, dice, results))

        additional_eval = 0
        if additional:
            additional_eval = eval(additional)

        result = {"result_dies": result_dies,
                  "larger": result_dies[0].larger(),
                  "smaller": result_dies[0].smaller(),
                  "result_minus_dies": result_minus_dies,
                  "result_final": only_dices+additional_eval,
                  "only_dices": only_dices,
                  "additional": additional,
                  "additional_eval": additional_eval}

        # Register the dice history
        if STATS_ENABLE:
            for die_result in result['result_dies']:
                for die in die_result.debug:
                    insert_roll(context.author.id, context.channel.name, f"d{die_result.dice_base}", int(die['value']), die['critical'], die['fail'])

        return result
    except Exception as e:
        raise
        print(f"Exp: {e}")
