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
        self.dice_base = dice
        self.ready = False
        self.process()

    def process(self, done=False):
        self.result = sum(self.get_list_of_result())
        self.debug = [{'value': d, 'critical': d == int(self.dice_base), 'fail': d == 1} for d in self.get_list_of_result()]
        self.ready = done

    def get_list_of_result(self):
        return [dice[0] for dice in self.list_of_result if dice[1]]

    def __str__(self):
        return f"{self.verbose} => {self.list_of_result}"

    def __repr__(self):
        return self.__str__()

    def get_json(self):
        return self.__dict__

    def larger(self):
        return max(self.get_list_of_result())

    def smaller(self):
        return min(self.get_list_of_result())

    def set_validation_adv(self, adv=True):
        if self.ready:
            return
        try:
            dice = self.get_list_of_result()
            if adv:
                value = max(dice)
            else:
                value = min(dice)

            for index, dice in enumerate(dice):
                # Check if dice is the target OR if we have the same value in more dice, so ignore the first!
                if dice != value or dice.count(value) > 1 and index > 0:
                    self.list_of_result[index][1] = False
                    if len(self.list_of_result) == 2:
                        break
            self.process(True)
        except Exception as e:
            print(e)


async def _roll_dice(times, dice):
    if int(times) > 40:
        times = 40

    return [random.randint(1, int(dice)) for _ in range(int(times))]


async def _roll_luck_dice():
    luck_faces = [1, 18, 19, 20, 18, 19, 20, 18, 19, 20, 18, 19, 20, 18, 19, 20, 18, 19, 20, 1]
    return [random.choice(luck_faces)]


async def process(context, dice_data, ignore_d20=False, reroll=None, luck=None):
    repeat = await parse_repeat(dice_data)
    if repeat:
        repeat = int(repeat[0])
        if repeat > 10:
            repeat = 10
        if "x" in dice_data:
            dice_data = dice_data.split("x")[1]
        else:
            dice_data = dice_data.split("*")[1]
    else:
        repeat = 1

    import re
    if re.findall('^(20)(?=[\+\-])', dice_data) and not ignore_d20:
        # Missing a `d`
        print(f"Missing a `d` in command: {dice_data}")
        dice_data = 'd'+dice_data
        print(f"Fixed to: {dice_data}")

    try:
        if int(dice_data):
            # Only modifier
            if re.findall('-(\d+)?', dice_data):
                dice_data = f'd20-{dice_data}'
            else:
                dice_data = f'd20+{dice_data}'

            dice_data = dice_data.replace("++", "+").replace("--", "-")
            print(f"Fixed to: {dice_data}")
    except:
        pass

    dice_positive, dice_negative = await parse_dice(dice_data)
    additional = await parse_additional(dice_data, dice_positive, dice_negative)
    dice_list = []

    for _ in range(0, repeat):
        dice_list.append(await calculate_dice(context, dice_positive, dice_negative, additional, ignore_d20, reroll, luck))
    return dice_list


async def parse_dice(data):
    import re

    parsed_negative = re.findall('-(\d+)?d(\d+)?', data)
    parsed_positive = re.findall('(\d+)?d(\d+)?', data)
    for pn in parsed_negative:
        if pn in parsed_positive:
            parsed_positive.remove(pn)
    return parsed_positive, parsed_negative


async def parse_repeat(data):
    import re
    return re.findall('(\d+)(?=\*)', data) + re.findall('(\d+)(?=x)', data)


async def parse_additional(data, positive_die, negative_die):
    try:
        for item in positive_die:
            dice = f"{item[0]}d{item[1]}"
            data = data.replace(f"+{dice}", "")
            if dice in data:
                data = data.replace(dice, "")

        for item in negative_die:
            dice = f"{item[0]}d{item[1]}"
            data = data.replace(f"-{dice}", "")
            if dice in data:
                data = data.replace(dice, "")

        return data
    except:
        raise


async def roll_and_reroll(number, dice, reroll, luck=False):
    number = number if number else 1
    if luck:
        results = first_results = [[dice, True] for dice in await _roll_luck_dice()]
    else:
        results = first_results = [[dice, True] for dice in await _roll_dice(number, dice)]
    roll_again = 0
    for index, dice_rolled in enumerate(first_results):
        if reroll and dice_rolled[0] <= int(reroll.split("r")[1]):
            # Set the first roll as not active
            results[index][1] = False
            # Reroll the new dice
            roll_again += 1

    # for some reason I need to run this in another loop to avoid a infinity looping running
    for _ in range(roll_again):
        new_dice = await _roll_dice(1, dice)
        results.append([new_dice[0], True])

    return Die(number, dice, results)


async def calculate_dice(context, dice_positive, dice_negative, additional, ignore_d20=False, reroll=None, adv=None, luck=False):
    '''
        Context => Discord context to capture player name and channel name
        dice_positive => List with quantity and dice size to roll [[1, 6], [2, 4]] (1d6 + 2d4)
        dice_negative => List with quantity and dice size to roll [[1, 6], [2, 4]] (1d6 + 2d4)
        additional => Additional math for the roll to be evalueted with the result (+2-1)
        ignore_d20 => Bool, ignore any d20 rolls in the list
        reroll => String with minimal number to reroll once (r2) -> Will re-roll once results for FIRST dice <= 2.
    '''
    # ignore_d20 Used to roll without d20 for adv
    result_die = []
    result_minus_die = []
    only_dice = 0
    try:
        for i, d in enumerate(dice_positive):
            number, dice = d
            if ignore_d20 and dice == "20":
                continue

            rolled = await roll_and_reroll(number, dice, reroll if i == 0 else None, luck)
            if adv is not None:
                rolled.set_validation_adv(adv)

            result_die.append(rolled)
            only_dice += rolled.result

        for number, dice in dice_negative:
            if ignore_d20 and dice == "20":
                continue
            rolled = await roll_and_reroll(number, dice, None)
            result_minus_die.append(rolled)
            only_dice -= rolled.result

        additional_eval = 0
        if additional:
            additional_eval = eval(additional)

        result = {"result_die": result_die,
                  "result_minus_die": result_minus_die,
                  "result_final": only_dice+additional_eval,
                  "only_dice": only_dice,
                  "additional": additional,
                  "additional_eval": additional_eval}

        # Register the dice history (Maybe move this to another place?)
        if STATS_ENABLE:
            for die_result in result['result_die']:
                for die in die_result.debug:
                    insert_roll(context.author.id, context.channel.name, f"d{die_result.dice_base}", int(die['value']), die['critical'], die['fail'])
                    # save_roll.delay(context.author.id, context.channel.name, f"d{die_result.dice_base}", int(die['value']), die['critical'], die['fail'])

        return result
    except Exception as e:
        print(f"Exp: {e}")
        raise
