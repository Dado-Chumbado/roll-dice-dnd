import datetime
from contextlib import contextmanager
from peewee import *
from enum import Enum
from db.models import PlayerStats, RollDb, pg_db


class DiceType(Enum):
    D20 = "d20"
    D4 = "d4"
    D6 = "d6"
    D8 = "d8"
    D10 = "d10"
    D12 = "d12"
    D100 = "d100"

@contextmanager
def connect_db():
    pg_db.connect()
    try:
        yield
    except Exception as e:
        print(f"Exception connect_db {e}")
        raise
    finally:
        pg_db.close()


def insert_roll(player_id, channel, dice_str, value, critical=False,
                fail=False):
    with connect_db():
        RollDb.create(player_id=player_id, channel=channel, dice=dice_str,
                      value=value, critical=critical, fail=fail)


def reset_player_stats(player):
    for dice in DiceType:
        setattr(player, f"total_{dice.value}_values_rolled", 0)
        setattr(player, f"total_{dice.value}_rolled", 0)
    player.total_dice_rolled = 0
    player.sum_dice_number_rolled = 0


def update_player_stats(player_id, display_name, channel, start_date=None,
                        end_date=None):
    with connect_db():
        player, created = PlayerStats.get_or_create(player_id=player_id,
                                                    channel=channel)
        player.display_name = display_name
        reset_player_stats(player)

        rolls = RollDb.select().where(RollDb.channel == channel,
                                      RollDb.player_id == player_id)
        if start_date and end_date:
            start_range = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            end_range = datetime.datetime.strptime(end_date, '%Y-%m-%d')
            rolls = rolls.where(RollDb.created.between(start_range, end_range))

        dice_enum = {dice.value for dice in DiceType}
        for r in rolls:
            player.total_dice_rolled += 1
            player.sum_dice_number_rolled += r.value
            if r.dice in dice_enum:
                setattr(player, f"total_{r.dice}_values_rolled",
                        getattr(player,
                                f"total_{r.dice}_values_rolled") + r.value)
                setattr(player, f"total_{r.dice}_rolled",
                        getattr(player, f"total_{r.dice}_rolled") + 1)

                if r.critical:
                    player.total_d20_critical_rolled += 1 if r.dice == DiceType.D20.value else 0
                if r.fail:
                    player.total_d20_fails_rolled += 1 if r.dice == DiceType.D20.value else 0

        player.save()
    return player


async def show_general_info(context, show_critical=True, show_fails=True,
                            specific_dice=None):
    try:
        ps = update_player_stats(context.author.id,
                                 context.author.display_name,
                                 context.channel.name)
        stats = f"```You have rolled a total of {ps.total_dice_rolled} dice! \n"
        stats += f"D20 rolled {ps.total_d20_rolled} times! with {ps.total_d20_critical_rolled} critical hits and {ps.total_d20_fails_rolled} failures.\n"
        stats += f"The sum of your d20's is {ps.total_d20_values_rolled}.\nTotal of other dice:\n"

        # Show specific dice if provided, otherwise show all
        dice_types_to_show = [specific_dice] if specific_dice else DiceType
        for dice in dice_types_to_show:
            rolled_count = getattr(ps, f"total_{dice.value}_rolled")
            if rolled_count:
                stats += f" {dice.value.upper()} rolled {rolled_count} times. The sum is {getattr(ps, f'total_{dice.value}_values_rolled')} \n"

        if show_critical:
            stats += f"Total critical hits for D20: {ps.total_d20_critical_rolled}\n"

        if show_fails:
            stats += f"Total failures for D20: {ps.total_d20_fails_rolled}\n"

        stats += f"The total of all rolled dice is: {ps.sum_dice_number_rolled}```"
        await context.send(stats)
    except Exception as e:
        print(f"An error occurred while fetching stats: {e}")
        await context.send(f"An error occurred while fetching stats: {e}")


def get_session_stats(channel, date=None, end=None):
    with connect_db():
        if not date:
            start_range = datetime.datetime.now().date() - datetime.timedelta(
                days=1)
            end_range = datetime.datetime.now()
        else:
            start_range = datetime.datetime.strptime(date, '%Y-%m-%d')
            end_range = datetime.datetime.strptime(end,
                                                   '%Y-%m-%d') if end else start_range + datetime.timedelta(
                days=1)

        rs = RollDb.select().where(
            RollDb.created.between(start_range, end_range),
            RollDb.channel == channel)
        d20s = rs.where(RollDb.dice == DiceType.D20.value)

        d20s_critical = d20s.where(RollDb.critical == True).count()
        d20s_fail = d20s.where(RollDb.fail == True).count()

        rolled_d20_by_player = RollDb.select(RollDb.player_id,
                                             fn.COUNT(RollDb.player_id)) \
            .where(RollDb.created.between(start_range, end_range),
                   RollDb.channel == channel,
                   RollDb.dice == DiceType.D20.value) \
            .group_by(RollDb.player_id).order_by(
            fn.COUNT(RollDb.player_id).desc())

        critics = RollDb.select(RollDb.player_id, fn.COUNT(RollDb.critical)) \
            .where(RollDb.created.between(start_range, end_range),
                   RollDb.channel == channel,
                   RollDb.dice == DiceType.D20.value, RollDb.critical == True) \
            .group_by(RollDb.player_id).order_by(
            fn.COUNT(RollDb.critical).desc())

        fails = RollDb.select(RollDb.player_id, fn.COUNT(RollDb.fail)) \
            .where(RollDb.created.between(start_range, end_range),
                   RollDb.channel == channel,
                   RollDb.dice == DiceType.D20.value, RollDb.fail == True) \
            .group_by(RollDb.player_id).order_by(fn.COUNT(RollDb.fail).desc())

        total_rolled = RollDb.select(fn.SUM(RollDb.value)).where(
            RollDb.created.between(start_range, end_range),
            RollDb.channel == channel).scalar() or 0

    return {
        'critical_hits': d20s_critical,
        'failures': d20s_fail,
        'top_critics': critics,
        'top_failures': fails,
        'total_rolled': total_rolled,
        'd20s_by_player': rolled_d20_by_player
    }


def get_display_name(player_id, channel):
    try:
        return PlayerStats.get(PlayerStats.player_id == player_id,
                               PlayerStats.channel == channel).display_name
    except PlayerStats.DoesNotExist:
        return f"Player name not found: {player_id}"


async def show_session_stats(ctx, channel, date=None, end_date=None):
    try:
        data = get_session_stats(channel, date, end_date)

        # Create the header
        date_str = date or "Last session"
        text = f"```STATISTICS {channel} from {date_str}\n"

        # Access values using descriptive keys
        text += f"Total critical hits: {data['critical_hits']}\n"
        text += f"Total failures: {data['failures']}\n"
        text += f"Critical/failure ratio: {data['failures'] and data['critical_hits'] / data['failures']:.2f}\n"

        if data['top_critics']:
            text += f"Player with the most critical hits: {get_display_name(data['top_critics'][0].player_id, channel)} with {data['top_critics'][0].count} critical hits!\n"
        if data['top_failures']:
            text += f"Player with the most failures: {get_display_name(data['top_failures'][0].player_id, channel)} with {data['top_failures'][0].count} failures!\n"

        # Create a table for players' statistics
        luck_table = []
        for r in data['d20s_by_player']:
            player_stats = {
                "player_id": r.player_id,
                "count_critical": next((c.count for c in data['top_critics'] if c.player_id == r.player_id), 0),
                "count_fail": next((f.count for f in data['top_failures'] if f.player_id == r.player_id), 0),
                "average_critical": 0,
                "average_fail": 0,
                "d20_rolled": r.count
            }
            player_stats["average_critical"] = (player_stats["count_critical"] * 100 / r.count) if r.count else 0
            player_stats["average_fail"] = (player_stats["count_fail"] * 100 / r.count) if r.count else 0
            luck_table.append(player_stats)

        # Identify the luckiest and unluckiest players
        luck_player = max(luck_table, key=lambda d: d['average_critical'], default=None)
        unlucky_player = max(luck_table, key=lambda d: d['average_fail'], default=None)

        if luck_player:
            text += f"Luckiest player: {get_display_name(luck_player['player_id'], channel)} with {luck_player['average_critical']:.2f}% critical hits\n"
        if unlucky_player:
            text += f"Unluckiest player: {get_display_name(unlucky_player['player_id'], channel)} with {unlucky_player['average_fail']:.2f}% failures\n"

        text += f"Total rolled: {data['total_rolled']}```"
        await ctx.send(text)
    except Exception as e:
        print(e)
        raise
        await ctx.send("An error occurred while fetching session stats.")
