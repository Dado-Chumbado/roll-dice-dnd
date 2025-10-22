import os
import random
from dataclasses import dataclass


@dataclass
class Dice:
    value: int          # The value rolled on the die
    is_active: bool     # Whether the roll is considered in the total
    is_critical: bool   # Whether the roll is a critical hit (max value)
    is_fail: bool       # Whether the roll is a failure (minimum value)

    def __str__(self):
        return str(f"{self.value} {self.is_active}")


class RolledDice:
    def __init__(self, die_size, rolled_dice):
        self.results = []
        self.dice_base = die_size

        self.recalculate_results(rolled_dice)

    def recalculate_results(self, roll: list):
        for value in roll:
            is_critical = value == self.dice_base
            is_fail = value == 1
            # All rolls are active by default
            self.results.append(Dice(value, True, is_critical, is_fail))

    @property
    def total(self) -> int:
        return sum([die.value for die in self.results if die.is_active])

    @property
    def quantity(self) -> int:
        return len(self.results)

    @property
    def quantity_active(self) -> int:
        return len(self.get_list_valid_values())

    def get_list_valid_values(self) -> list:
        return [r.value for r in self.results if r.is_active]

    def get_list_valid_dice(self, active=None) -> list:
        if active:
            return [dice for dice in self.results if dice.is_active == active]
        else:
            return [dice for dice in self.results]

    def larger(self):
        return max(self.get_list_valid_values())

    def smaller(self):
        return min(self.get_list_valid_values())

    def disable_smaller(self):
        """
        Disables the smallest active die. When multiple dice have the same value,
        preserves the dice at the ends (first/last positions) when possible.
        """
        active_dice = [(i, d) for i, d in enumerate(self.results) if d.is_active]
        if not active_dice:
            return
            
        # Find the smallest active value
        min_value = min(d.value for _, d in active_dice)
        
        # Get all positions of dice with the minimum value
        min_positions = [i for i, d in active_dice if d.value == min_value]
        
        # If we have multiple minimum values, prefer disabling middle positions
        if len(min_positions) > 1:
            # Skip first and last positions if possible
            middle_positions = min_positions[1:-1] if len(min_positions) > 2 else min_positions
            position_to_disable = middle_positions[0] if middle_positions else min_positions[0]
        else:
            position_to_disable = min_positions[0]
            
        self.results[position_to_disable].is_active = False

    def set_advantage(self, advantage=True, double_adv=False):
        """ Disable rolls that are not the target.

            if advantage is True, the target is the larger value
            if advantage is False, the target is the smaller value
        """
        target = self.larger() if advantage else self.smaller()
        all_values = self.get_list_valid_values()

        # If all dice have the same result, disable all less the last
        if len(set(all_values)) == 1:
            # All dice have the same result, so disable the first and return
            self.results[0].is_active = False
            if double_adv:
                self.results[1].is_active = False
            return

        if not advantage:
            if self.results[0].value > target:
                self.results[0].is_active = False
            else:
                self.results[1].is_active = False
            return

        found_target = False
        for roll_result in self.results:
            if roll_result.value == target and not found_target:
                found_target = True
                continue

            if roll_result.value <= target:
                roll_result.is_active = False
                if double_adv:
                    double_adv = False
                    continue
                break


    def apply_critical(self):
        """
        Apply critical hit logic by maximizing the first dice result.

        """
        total_dice_to_maximize = len(self.results) / 2
        for i in range(int(total_dice_to_maximize)):
            self.results[i].value = self.dice_base
            self.results[i].is_critical = True
            self.results[i].is_active = True
            self.results[i].is_fail = False

    async def apply_reroll(self, reroll_threshold: int):
        current_dice_len = len(self.results)
        for index in range(current_dice_len):
            if self.results[index].value <= reroll_threshold:
                self.results[index].is_active = False  # Mark original roll as inactive
                new_roll = await _roll_dice(1, self.dice_base)
                self.recalculate_results(new_roll)  # Add reroll result

        return self

    def __str__(self):
        return str(self.__repr__())

    def __repr__(self):
        return f"{self.quantity}d{self.dice_base}"


async def _roll_dice(times: int, dice: int) -> list:
    """
    Rolls dice multiple times and returns the results.

    Args:
        times (int): Number of times to roll the dice.
        dice (int): The number of sides on the dice.

    Returns:
        list: A list of integers representing the results of each dice roll.
    """
    # Get dice limit from environment variables, default to a safe value (e.g., 100) if not found
    limit = int(os.getenv("limit_of_dice_per_roll", 100))

    # Ensure times and dice are valid
    times = max(1, times)  # No negative rolls allowed
    dice = max(2, dice)  # Dice must have at least 2 side

    # Roll the dice, ensuring we respect the limit
    return [random.randint(1, dice) for _ in range(min(times, limit))]

async def generate_dice_roll(number_of_dice, dice_size, reroll='', critical=False) -> RolledDice:

    # Step 1: Roll the dice
    results = await _roll_dice(number_of_dice, dice_size)
    rolled_dice = RolledDice(dice_size, results)

    # Step 2: Apply critical logic (if critical is True)
    if critical:
        rolled_dice.apply_critical()

    # Step 3: Apply reroll logic (if reroll is specified)
    if reroll:
        reroll_threshold = int(reroll.split('r')[1])
        rolled_dice = await rolled_dice.apply_reroll(reroll_threshold)

    # Return final Roll object
    return rolled_dice


class Roll:
    def __init__(self, dice_data: str, additional: str = ""):
        self.dice_expression = dice_data
        self.rolled_sum_dice = []  # To store positive rolls
        self.rolled_subtract_die = []  # To store negative rolls
        self.additional_eval = 0
        self.additional = additional

    def add_rolled_dice_sum(self, rolled_dice):
        self.rolled_sum_dice.append(rolled_dice)

    def add_rolled_dice_subtract(self, rolled_dice):
        self.rolled_subtract_die.append(rolled_dice)

    @property
    def amount_of_dice_rolled(self):
        return len(self.rolled_sum_dice) + len(self.rolled_subtract_die)

    @property
    def total_dice_result(self) -> int:
        return (sum(rolled_dice.total for rolled_dice in self.rolled_sum_dice)
                - sum(rolled_dice.total for rolled_dice in self.rolled_subtract_die))

    @property
    def total_roll(self):
        return self.total_dice_result + self.additional_eval

    def __str__(self):
        return str(self.__repr__())

    def __repr__(self):
        return f"Rolled: {self.total_dice_result}"
