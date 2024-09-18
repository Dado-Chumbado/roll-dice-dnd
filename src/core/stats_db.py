import os
from dotenv import load_dotenv
import datetime
import peewee
from peewee import *


load_dotenv()

pg_db = PostgresqlDatabase(os.getenv("db"), user=os.getenv("user"), password=os.getenv("pass"),
                           host=os.getenv("host"), port=os.getenv("port"))


class PlayerStats(Model):
    id = AutoField()
    player_id = BigIntegerField()
    display_name = CharField()
    channel = CharField()

    total_dice_rolled = IntegerField(default=0)

    total_d20_rolled = IntegerField(default=0)
    total_d20_values_rolled = BigIntegerField(default=0)
    total_d20_critical_rolled = IntegerField(default=0)
    total_d20_fails_rolled = IntegerField(default=0)

    total_d4_rolled = IntegerField(default=0)
    total_d4_values_rolled = IntegerField(default=0)
    total_d6_rolled = IntegerField(default=0)
    total_d6_values_rolled = IntegerField(default=0)
    total_d8_rolled = IntegerField(default=0)
    total_d8_values_rolled = IntegerField(default=0)
    total_d10_rolled = IntegerField(default=0)
    total_d10_values_rolled = IntegerField(default=0)
    total_d12_rolled = IntegerField(default=0)
    total_d12_values_rolled = IntegerField(default=0)
    total_d100_rolled = IntegerField(default=0)
    total_d100_values_rolled = IntegerField(default=0)

    sum_dice_number_rolled = BigIntegerField(default=0)

    class Meta:
        database = pg_db


class Roll(Model):
    id = AutoField()
    player_id = BigIntegerField(default=0)
    channel = CharField()
    dice = CharField()
    value = IntegerField(default=0)
    critical = BooleanField(default=False)
    fail = BooleanField(default=False)
    created = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = pg_db


def setup_db():
    pg_db.connect()
    try:
        pg_db.create_tables([PlayerStats, Roll])
    except peewee.OperationalError:
        pass


try:
    setup_db()
finally:
    pg_db.close()


def update_player_stats(player_id, display_name, channel, start_date=None, end_data=None):
    try:
        pg_db.connect()
        player, created = PlayerStats.get_or_create(player_id=player_id, channel=channel)
    except Exception as e:
        pg_db.close()
        print(f"update_player_stats: {e}")
        raise

    try:
        # for dice in Dice
        player.display_name = display_name
        player.total_d20_values_rolled = player.total_d20_rolled = player.total_d20_critical_rolled = \
            player.total_d20_fails_rolled = player.total_dice_rolled = player.sum_dice_number_rolled = \
            player.total_d4_values_rolled = player.total_d4_rolled = \
            player.total_d6_values_rolled = player.total_d6_rolled = \
            player.total_d8_values_rolled = player.total_d8_rolled = \
            player.total_d8_values_rolled = player.total_d8_rolled = \
            player.total_d10_values_rolled = player.total_d10_rolled = \
            player.total_d12_values_rolled = player.total_d12_rolled = \
            player.total_d100_values_rolled = player.total_d100_rolled = 0

        if start_date:
            start_range = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            end_range = datetime.datetime.strptime(end_data, '%Y-%m-%d')
            rolls = Roll.select().where(Roll.created > start_range, Roll.created < end_range, Roll.channel == channel, Roll.player_id == player_id, )
        else:
            rolls = Roll.select().where(Roll.player_id == player_id, Roll.channel == channel)

        for r in rolls:
            player.total_dice_rolled += 1
            player.sum_dice_number_rolled += r.value

            if r.result == "d20":
                player.total_d20_values_rolled += r.value
                player.total_d20_rolled += 1
                if r.critical:
                    player.total_d20_critical_rolled += 1
                if r.fail:
                    player.total_d20_fails_rolled += 1

            if r.result == "d4":
                player.total_d4_values_rolled += r.value
                player.total_d4_rolled += 1

            if r.result == "d6":
                player.total_d6_values_rolled += r.value
                player.total_d6_rolled += 1

            if r.result == "d8":
                player.total_d8_values_rolled += r.value
                player.total_d8_rolled += 1

            if r.result == "d10":
                player.total_d10_values_rolled += r.value
                player.total_d10_rolled += 1

            if r.result == "d12":
                player.total_d12_values_rolled += r.value
                player.total_d12_rolled += 1

            if r.result == "d100":
                player.total_d100_values_rolled += r.value
                player.total_d100_rolled += 1

        player.save()
    except Exception as e:
        pg_db.close()
        raise
    pg_db.close()
    return player


def insert_roll(player_id, channel, dice_str, value, critical=False, fail=False):
    pg_db.connect()
    Roll.create(player_id=player_id, channel=channel, dice=dice_str, value=value, critical=critical, fail=fail)
    pg_db.close()


async def show_general_info(context):
    try:
        ps = update_player_stats(context.author.id, context.author.display_name, context.channel.name)

        text = f"```Voce rolou um total de {ps.total_dice_rolled} dados! \n"
        text += f"D20 rolado {ps.total_d20_rolled} vezes! " \
                f"com {ps.total_d20_critical_rolled} criticos e {ps.total_d20_fails_rolled} falhas.\n"
        text += f"A soma dos seus d20's é {ps.total_d20_values_rolled}.\n"
        text += f"Total de outros dados\n"
        if ps.total_d4_rolled:
            text += f" D4 rolado {ps.total_d4_rolled} vezes. A soma é {ps.total_d4_values_rolled} \n"
        if ps.total_d6_rolled:
            text += f" D6 rolado {ps.total_d6_rolled} vezes. A soma é {ps.total_d6_values_rolled} \n"
        if ps.total_d8_rolled:
            text += f" D8 rolado {ps.total_d8_rolled} vezes. A soma é {ps.total_d8_values_rolled} \n"
        if ps.total_d10_rolled:
            text += f" D10 rolado {ps.total_d10_rolled} vezes. A soma é {ps.total_d10_values_rolled} \n"
        if ps.total_d12_rolled:
            text += f" D12 rolado {ps.total_d12_rolled} vezes. A soma é {ps.total_d12_values_rolled} \n"
        if ps.total_d100_rolled:
            text += f" D100 rolado {ps.total_d100_rolled} vezes. A soma é {ps.total_d100_values_rolled} \n"

        text += f"O total de todos os dados rolados é: {ps.sum_dice_number_rolled}```"
        print(text)
        await context.send(text)
    except Exception as e:
        pg_db.close()
        await context.send(e)


def get_session_stats(channel, date=None, end=None):
    pg_db.connect()
    if not date:
        start_range = datetime.datetime.now().date() - datetime.timedelta(days=1)
        end_range = datetime.datetime.now()
    else:
        start_range = datetime.datetime.strptime(date, '%Y-%m-%d')
        if end:
            end_range = datetime.datetime.strptime(end, '%Y-%m-%d')
        else:
            end_range = start_range + datetime.timedelta(days=1)

    print(f"Filtering per date: {start_range} until {end_range}")
    rs = Roll.select().where(Roll.created > start_range, Roll.created < end_range, Roll.channel == channel)
    d20s = rs.where(Roll.dice == "d20")

    d20s_critical = d20s.where(Roll.critical == True).count()
    d20s_fail = d20s.where(Roll.fail == True).count()

    rolled_d20_by_player = Roll.select(Roll.player_id, fn.COUNT(Roll.player_id)) \
        .where(Roll.created > start_range, Roll.created < end_range, Roll.channel == channel, Roll.dice == "d20") \
        .group_by(Roll.player_id).order_by(fn.COUNT(Roll.player_id).desc())

    critics = Roll.select(Roll.player_id, fn.COUNT(Roll.critical)) \
        .where(Roll.created > start_range, Roll.created < end_range, Roll.channel == channel, Roll.dice == "d20",
               Roll.critical == True) \
        .group_by(Roll.player_id).order_by(fn.COUNT(Roll.critical).desc())

    fails = Roll.select(Roll.player_id, fn.COUNT(Roll.critical)) \
        .where(Roll.created > start_range, Roll.created < end_range, Roll.channel == channel, Roll.dice == "d20",
               Roll.fail == True) \
        .group_by(Roll.player_id).order_by(fn.COUNT(Roll.critical).desc())

    total_rolled = Roll.select(fn.SUM(Roll.value)).where(Roll.created > start_range, Roll.created < end_range,
                                                         Roll.channel == channel)[0].sum
    pg_db.close()
    return [d20s_critical, d20s_fail, critics, fails, total_rolled, rolled_d20_by_player]


def get_display_name(player_id, channel):
    try:
        return PlayerStats.get(PlayerStats.player_id == player_id, channel=channel).display_name
    except:
        return f"Player name not found: {player_id}"


async def show_session_stats(ctx, channel, date=None, end_date=None):
    try:
        data = get_session_stats(channel, date, end_date)

        date_str = date
        if not date:
            date_str = "Ultima sessao"

        text = f"```"
        text += f"ESTATISTICAS {channel} de {date_str}\n"

        text += f"Total criticos: {data[0]}\n"
        text += f"Total falhas: {data[1]}\n"
        try:
            text += f"Proporcao critico/falha: {data[0]/data[1]:.2f}\n"
        except ZeroDivisionError:
            text += f"Proporcao critico/falha: 0\n"

        if data[2]:
            text += f"Jogador com mais criticos: {get_display_name(data[2][0].player_id, channel)} com {data[2][0].count} criticos!\n"
        if data[3]:
            text += f"Jogador com mais falhas: {get_display_name(data[3][0].player_id, channel)} com {data[3][0].count} falhas!\n"

        luck_table = []
        for r in data[5]:
            player = {"player_id": r.player_id, "count_critical": 0, "count_fail": 0, "average_critical": 0,
                      "average_fail": 0, "d20_rolled": r.count}
            for critical_per_player in data[2]:
                if r.player_id == critical_per_player.player_id:
                    player["average_critical"] = (critical_per_player.count * 100) / r.count
                    player["count_critical"] = critical_per_player.count

            for fails_per_player in data[3]:
                if r.player_id == fails_per_player.player_id:
                    player["average_fail"] = (fails_per_player.count * 100) / r.count
                    player["count_fail"] = fails_per_player.count
            luck_table.append(player)

        luck_player = sorted(luck_table, key=lambda d: d['average_critical'])[-1]
        unluck_player = sorted(luck_table, key=lambda d: d['average_fail'])[-1]

        if luck_player:
            try:
                text += f"Mais sortudo: {get_display_name(luck_player['player_id'], channel)} com {luck_player['count_critical']} criticos! [{luck_player['d20_rolled']} d20 rolados]\n"
            except:
                pass
        if unluck_player:
            try:
                text += f"Mais azarado: {get_display_name(unluck_player['player_id'], channel)} com {luck_player['count_fail']} falhas! [{unluck_player['d20_rolled']} d20 rolados]\n"
            except:
                pass
        text += f"Soma de todos os dados rolados: {data[4]} \n\n"

        for player in luck_table:
            text += f"{get_display_name(player['player_id'], channel)}| d20 rolados => {player['d20_rolled']}. Criticos: {player['average_critical']:.2f}% ({player['count_critical']}) | falha: {player['average_fail']:.2f}% ({player['count_fail']}) \n"

        text += "```"
        pg_db.close()
        await ctx.send(text)
    except Exception as e:
        pg_db.close()
        print(e)
        raise
        # await ctx.send(e)


def force_recalculate_channel(channel):
    # for player in Roll.
    # update_player_stats
    pass
