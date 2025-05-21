import datetime
import logging
from contextlib import contextmanager
from enum import Enum
from collections import defaultdict
from db.models import PlayerStats, RollDb, pg_db

logger = logging.getLogger(__name__)


class DiceType(Enum):
    D20 = "d20"
    D4 = "d4"
    D6 = "d6"
    D8 = "d8"
    D10 = "d10"
    D12 = "d12"
    D100 = "d100"

expected_avg = {
    "d4": 2.5,
    "d6": 3.5,
    "d8": 4.5,
    "d10": 5.5,
    "d12": 6.5,
    "d20": 10.5,
    "d100": 50.5,
}

@contextmanager
def connect_db():
    try:
        if pg_db.is_closed():
            pg_db.connect()
            should_close = True
        else:
            should_close = False

        yield

    except Exception as e:
        logging.error(f"Error in connect db: {e}")
        raise

    finally:
        if should_close:
            pg_db.close()

def insert_roll(player_id, channel, dice_str, value, critical=False,
                fail=False):
    with connect_db():
        RollDb.create(player_id=player_id, channel=channel, dice=dice_str,
                      value=value, critical=critical, fail=fail)

def get_display_name(player_id, channel):
    try:
        return PlayerStats.get(PlayerStats.player_id == player_id).display_name
    except PlayerStats.DoesNotExist as e:
        logging.error(f"Player name not found in database: {e}")
        return f"Player name not found: {player_id}"

async def show_player_stats(context,
                            channel,
                            start_date=None,
                            end_date=None,
                            specific_player=None):
    try:
        player_id = specific_player or context.author.id

        with connect_db():
            if not start_date or not end_date:
                start_range = datetime.datetime.now().date() - datetime.timedelta(days=1)
                end_range = datetime.datetime.now()
            else:
                start_range = datetime.datetime.strptime(start_date, '%Y-%m-%d')
                end_range = datetime.datetime.strptime(end_date, '%Y-%m-%d')

            rs = RollDb.select().where(
                RollDb.created.between(start_range, end_range),
                RollDb.channel == channel,
                RollDb.player_id == player_id
            )

            dice_rolls = defaultdict(list)
            total_value = 0
            total_rolls = 0
            d20_critical = 0
            d20_fails = 0

            for r in rs:
                total_rolls += 1
                total_value += r.value
                dice_rolls[r.dice].append(r.value)
                if r.dice == DiceType.D20.value:
                    if r.critical:
                        d20_critical += 1
                    if r.fail:
                        d20_fails += 1

        avg = total_value / total_rolls if total_rolls else 0
        display_name = get_display_name(player_id, channel)

        stats = f"```🎲 Stats for {display_name}\n"
        stats += f"Total rolls: {total_rolls}\n"
        stats += f"Total rolled value: {total_value}\n"
        stats += f"Average per roll: {avg:.2f}\n"

        stats += f"💥 Critical hits (d20 only): {d20_critical}\n"
        stats += f"💢 Failures (d20 only): {d20_fails}\n"

        stats += f"\n🎯 Rolls by Dice:\n"
        for dice, values in dice_rolls.items():
            count = len(values)
            total = sum(values)
            average = total / count if count else 0
            stats += f"  - {dice.upper()}: {count} rolls, sum {total}, avg {average:.2f}\n"

        stats += "```"
        await context.send(stats)
    except Exception as e:
        logging.error(f"An error occurred while fetching player stats: {e}")
        await context.send("An error occurred while fetching player stats.")

def get_session_stats(channel, date=None, end=None):
    with connect_db():
        if not date:
            start_range = datetime.datetime.now().date() - datetime.timedelta(days=1)
            end_range = datetime.datetime.now()
        else:
            start_range = datetime.datetime.strptime(date, '%Y-%m-%d')
            end_range = datetime.datetime.strptime(end, '%Y-%m-%d') if end else start_range + datetime.timedelta(days=1)

        rs = RollDb.select().where(
            RollDb.created.between(start_range, end_range),
            RollDb.channel == channel)

        from peewee import fn, Case

        player_roll_counts = RollDb.select(
            RollDb.player_id,
            fn.COUNT(RollDb.id).alias("total_rolls"),
            fn.SUM(RollDb.value).alias("total_value"),
            fn.SUM(
                Case(None, [((RollDb.critical == True) & (RollDb.dice == "d20"), 1)], 0)
            ).alias("d20_critical"),
            fn.SUM(
                Case(None, [((RollDb.fail == True) & (RollDb.dice == "d20"), 1)], 0)
            ).alias("d20_fails")
        ).where(
            RollDb.created.between(start_range, end_range),
            RollDb.channel == channel
        ).group_by(RollDb.player_id).dicts()

        player_stats = {}
        for r in player_roll_counts:
            player_stats[r['player_id']] = {
                "total_rolls": r.get('total_rolls', 0),
                "total_value": r.get('total_value', 0),
                "d20_critical": r.get('d20_critical', 0),
                "d20_fails": r.get('d20_fails', 0),
                "dice_rolls": defaultdict(list)
            }

        dice_global_stats = defaultdict(list)
        for r in rs:
            if r.player_id in player_stats:
                player_stats[r.player_id]["dice_rolls"][r.dice].append(r.value)
            dice_global_stats[r.dice].append(r.value)

        d20s_critical = sum(p["d20_critical"] for p in player_stats.values())
        d20s_fail = sum(p["d20_fails"] for p in player_stats.values())
        total_rolled = sum(p["total_value"] for p in player_stats.values())

    return {
        'players': player_stats,
        'dice_stats': dice_global_stats,
        'critical_hits': d20s_critical,
        'failures': d20s_fail,
        'total_rolled': total_rolled
    }

async def show_session_stats(ctx, channel, date=None, end_date=None):
    try:
        data = get_session_stats(channel, date, end_date)
        players = data['players']

        text = f"```📊 STATISTICS {channel} from {date or 'Last session'}\n"
        text += f"🎯 Total critical hits: {data['critical_hits']}\n"
        text += f"💀 Total failures: {data['failures']}\n"
        text += f"⚖️ Critical/failure ratio: {data['failures'] and data['critical_hits'] / data['failures']:.2f}\n"

        def calc_luck(player):
            total_diff = 0
            total_rolls = 0
            for d, rolls in player['dice_rolls'].items():
                if d in expected_avg:
                    avg = sum(rolls) / len(rolls)
                    diff = avg - expected_avg[d]
                    total_diff += diff * len(rolls)
                    total_rolls += len(rolls)
            return total_diff / total_rolls if total_rolls else 0

        luckiest = max(players.items(), key=lambda x: calc_luck(x[1]), default=(None, {}))
        unluckiest = min(players.items(), key=lambda x: calc_luck(x[1]), default=(None, {}))

        if luckiest[0] is not None:
            text += f"🍀 Luckiest player: {get_display_name(luckiest[0], channel)} (Avg +{calc_luck(luckiest[1]):.2f})\n"
        if unluckiest[0] is not None:
            text += f"☠️ Unluckiest player: {get_display_name(unluckiest[0], channel)} (Avg {calc_luck(unluckiest[1]):.2f})\n"

        most_rolls = max(players.items(), key=lambda x: x[1]['total_rolls'], default=(None, {}))
        if most_rolls[0] is not None:
            text += f"🎲 Most dice rolled: {get_display_name(most_rolls[0], channel)} with {most_rolls[1]['total_rolls']} rolls\n"

        text += "\n🎲 Dice Usage:\n"
        for dice, values in sorted(data['dice_stats'].items(),
                                   key=lambda x: int(x[0][1:])):
            count = len(values)
            total = sum(values)
            avg = total / count if count else 0
            text += f"  - {dice.upper()}: rolled {count} times, total {total}, average {avg:.2f}\n"

        text += "\n👥 Player Stats:\n"
        for pid, pstats in sorted(players.items(), key=lambda x: x[1]['total_rolls'], reverse=True):
            avg = pstats['total_value'] / pstats['total_rolls'] if pstats['total_rolls'] else 0
            text += f"  - {get_display_name(pid, channel)}: 🎲 Rolls: {pstats['total_rolls']} | 💥 Crits: {pstats['d20_critical']} | 💢 Fails: {pstats['d20_fails']} | 📈 Avg: {avg:.2f} | 💰 Total: {pstats['total_value']}\n"

        text += f"\n💰 Total rolled: {data['total_rolled']}```"
        await ctx.send(text)
    except Exception as e:
        logging.error(f"An error occurred while fetching session stats: {e}")
        await ctx.send("An error occurred while fetching session stats.")
