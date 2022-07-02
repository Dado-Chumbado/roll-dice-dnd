import random


class Die:
    def __init__(self, number, dice, results):
        self.verbose = f"{number}d{dice}"
        self.list_of_result = results
        self.dice_base = dice
        self.result = sum(results)

    def __str__(self):
        return f"{self.verbose} => {self.list_of_result}"

    def __repr__(self):
        return self.__str__()

    def get_json(self):
        return self.__dict__


async def roll_dice(times, dice):
    if int(times) > 20:
        times = 20

    return [random.randint(1, int(dice)) for _ in range(int(times))]


async def process(dices_data):
    print(f"dices_data: {dices_data}")

    repeat = await parse_repeat(dices_data)
    if repeat:
        repeat = int(repeat[0])
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
        dices_list.append(await calculate_dices(dices_positive, dices_negative, additional))
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
    return re.findall('(\d)(?=\*)', data)


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


async def calculate_dices(dices_positive, dices_negative, additional):
    result_sum_dies = []
    result_minus_dies = []
    only_dices = 0
    try:
        for number, dice in dices_positive:
            number = number if number else 1
            results = await roll_dice(number, dice)
            only_dices += sum(results)
            result_sum_dies.append(Die(number, dice, results))

        for number, dice in dices_negative:
            number = number if number else 1
            results = await roll_dice(number, dice)
            only_dices -= sum(results)
            result_minus_dies.append(Die(number, dice, results))

        additional_eval = 0
        if additional:
            additional_eval = eval(additional)

        dies_verbose = "".join([f"+{die.verbose}" for die in result_sum_dies])
        dies_verbose += "".join([f"-{die.verbose}" for die in result_minus_dies])

        return {"result_sum_dies": result_sum_dies,
                "result_minus_dies": result_minus_dies,
                "result_final": only_dices+additional_eval,
                "only_dices": only_dices,
                "additional": additional,
                "additional_eval": additional_eval,
                "dies_verbose": dies_verbose}
    except Exception as e:
        print(f"Exp: {e}")


async def get_best_result(dice_result):
    text = ""
    dice_1 = dice_2 = ""
    if dice_result[0] == 20 or dice_result[0] == 1:
        dice_1 = "!"
    if dice_result[1] == 20 or dice_result[1] == 1:
        dice_2 = "!"

    if dice_result[0] >= dice_result[1]:
        text += f"[ {dice_result[0]}{dice_1},  ~~{dice_result[1]}{dice_2}~~ ]"
        result = dice_result[0]
    else:
        text += f"[ ~~{dice_result[0]}{dice_1}~~, {dice_result[1]}{dice_2} ]"
        result = dice_result[1]

    if dice_result[0] == 1 and dice_result[1] == 1 or dice_result[0] == 20 and dice_result[1] == 20:
        text += f" ¯\_(ツ)_/¯ \n"

    return int(result), text