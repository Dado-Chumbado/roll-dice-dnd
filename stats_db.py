import datetime
import json
from peewee import *

with open("./secrets.json", "r") as env:
    ENV = json.load(env)

pg_db = PostgresqlDatabase(ENV['db'], user=ENV['user'], password=ENV['pass'],
                           host=ENV['host'], port=ENV['port'])


class PlayerStats(Model):
    id = AutoField()
    player_id = BigIntegerField()
    channel = CharField()

    total_dices_rolled = IntegerField(default=0)

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

    sum_dices_number_rolled = BigIntegerField(default=0)

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
    pg_db.create_tables([PlayerStats, Roll])


try:
    setup_db()
except:
    pass


def update_player_stats(player_id, channel, dice, value, critical, fail):
    try:
        player, created = PlayerStats.get_or_create(player_id=player_id, channel=channel)
    except:
        raise

    try:
        player.total_dices_rolled += 1
        player.sum_dices_number_rolled += value
        if dice == "d20":
            player.total_d20_values_rolled += value
            player.total_d20_rolled += 1
            if critical:
                player.total_d20_critical_rolled += 1
            if fail:
                player.total_d20_fails_rolled += 1

        if dice == "d4":
            player.total_d4_values_rolled += value
            player.total_d4_rolled += 1

        if dice == "d6":
            player.total_d6_values_rolled += value
            player.total_d6_rolled += 1

        if dice == "d8":
            player.total_d8_values_rolled += value
            player.total_d8_rolled += 1

        if dice == "d10":
            player.total_d10_values_rolled += value
            player.total_d10_rolled += 1

        if dice == "d12":
            player.total_d12_values_rolled += value
            player.total_d12_rolled += 1

        if dice == "d100":
            player.total_d100_values_rolled += value
            player.total_d100_rolled += 1

        player.save()
    except Exception as e:
        pg_db.rollback()
        raise


def insert_roll(player_id, channel, dice_str, value, critical=False, fail=False):
    try:
        Roll.create(player_id=player_id, channel=channel, dice=dice_str, value=value, critical=critical, fail=fail)
        update_player_stats(player_id, channel, dice_str, value, critical, fail)
    except Exception as e:
        pg_db.rollback()
        raise


def get_general_status_per_channel(player_id, channel):
    p = PlayerStats.get(PlayerStats.player_id == player_id, channel=channel)
    return p


async def show_general_info(bot, context, player_id, channel):
    ps = get_general_status_per_channel(player_id, channel)
    text = f"```Voce rolou um total de {ps.total_dices_rolled} dados! \n"
    text += f"D20 rolado {ps.total_d20_rolled} vezes! " \
            f"com {ps.total_d20_critical_rolled} criticos e {ps.total_d20_fails_rolled} falhas.\n"
    text += f"A soma total dos seus d20's é {ps.total_d20_values_rolled}.\n"
    text += f"Total de outros dados\n"
    if ps.total_d4_rolled:
        text += f" D4 rolado {ps.total_d4_rolled} vezes. A soma total é {ps.total_d4_values_rolled} \n"
    if ps.total_d6_rolled:
        text += f" D6 rolado {ps.total_d6_rolled} vezes. A soma total é {ps.total_d6_values_rolled} \n"
    if ps.total_d8_rolled:
        text += f" D8 rolado {ps.total_d8_rolled} vezes. A soma total é {ps.total_d8_values_rolled} \n"
    if ps.total_d10_rolled:
        text += f" D10 rolado {ps.total_d10_rolled} vezes. A soma total é {ps.total_d10_values_rolled} \n"
    if ps.total_d12_rolled:
        text += f" D12 rolado {ps.total_d12_rolled} vezes. A soma total é {ps.total_d12_values_rolled} \n"
    if ps.total_d100_rolled:
        text += f" D100 rolado {ps.total_d100_rolled} vezes. A soma total é {ps.total_d100_values_rolled} \n"

    text += f"O total de todos os dados rolados é: {ps.sum_dices_number_rolled}```"
    print(text)
    await context.send(text)


def get_session_stats(channel, date=None):
    if not date:
        date = datetime.datetime.now() - datetime.timedelta(days=2)
    rs = Roll.select().where(Roll.created > date, Roll.channel == channel)
    d20s = rs.where(Roll.dice == "d20")

    d20s_critical = d20s.where(Roll.critical == True).count()
    d20s_fail = d20s.where(Roll.fail == True).count()

    rolled_d20_by_player = Roll.select(Roll.player_id, fn.COUNT(Roll.player_id)) \
        .where(Roll.created > date, Roll.channel == channel, Roll.dice == "d20") \
        .group_by(Roll.player_id).order_by(fn.COUNT(Roll.player_id).desc())

    critics = Roll.select(Roll.player_id, fn.COUNT(Roll.critical)) \
        .where(Roll.created > date, Roll.channel == channel, Roll.dice == "d20", Roll.critical == True) \
        .group_by(Roll.player_id).order_by(fn.COUNT(Roll.critical).desc())

    fails = Roll.select(Roll.player_id, fn.COUNT(Roll.critical)) \
        .where(Roll.created > date, Roll.channel == channel, Roll.dice == "d20", Roll.fail == True) \
        .group_by(Roll.player_id).order_by(fn.COUNT(Roll.critical).desc())

    total_rolled = Roll.select(fn.SUM(Roll.value)).where(Roll.created > date, Roll.channel == channel)[0].sum

    return [d20s_critical, d20s_fail, critics, fails, total_rolled, rolled_d20_by_player]


def get_display_name(bot, ctx, player_id):
    # user = bot.get_user(player_id)
    # import discord
    # member = discord.Server.get_member(ctx.message.server, user_id=player_id)
    # print(user)
    # return user.display_name
    return player_id


async def show_session_stats(bot, ctx, channel, date=None):
    data = get_session_stats(channel, date)

    print(f"Total criticos: {data[0]}")
    print(f"Total falhas: {data[1]}")

    text = f"Total criticos: {data[0]}\n"
    text += f"Total falhas: {data[1]}\n"

    if data[2]:
        print(f"Jogador com mais criticos: {get_display_name(bot, ctx, data[2][0].player_id)} com {data[2][0].count} criticos!")
        text += f"Jogador com mais criticos: {get_display_name(bot, ctx, data[2][0].player_id)} com {data[2][0].count} criticos!\n"
    if data[3]:
        print(f"Jogador com mais falhas: {get_display_name(bot, ctx, data[3][0].player_id)} com {data[3][0].count} falhas!")
        text += f"Jogador com mais falhas: {get_display_name(bot, ctx, data[3][0].player_id)} com {data[3][0].count} falhas!\n"

    text += f"Total criticos: {data[0]}\n"
    text += f"Total falhas: {data[1]}\n"

    luck_table = []
    for r in data[5]:
        player = {"player_id": r.player_id, "count_critical": 0, "count_fail": 0, "average_critical": 0,
                  "average_fail": 0, "d20_rolled": r.count}
        for critical_per_player in data[2]:
            if r.player_id == critical_per_player.player_id:
                player["average_critical"] = r.count / critical_per_player.count
                player["count_critical"] = critical_per_player.count

        for fails_per_player in data[3]:
            if r.player_id == fails_per_player.player_id:
                player["average_fail"] = r.count / fails_per_player.count
                player["count_fail"] = fails_per_player.count
        luck_table.append(player)

    critical_percent_per_player = sorted(luck_table, key=lambda d: d['average_critical'])
    fail_percent_per_player = sorted(luck_table, key=lambda d: d['average_fail'])
    luck_player = unluck_player = None

    for cpp in critical_percent_per_player:
        if cpp['average_critical'] > 0:
            luck_player = cpp
            break

    for cpp in fail_percent_per_player:
        if cpp['average_critical'] > 0:
            unluck_player = cpp
            break

    print(f"Mais sortudo: {get_display_name(bot, ctx, luck_player['player_id'])} com {luck_player['count_critical']} criticos! (1/{luck_player['average_critical']}) [{luck_player['d20_rolled']}]\n")
    print(f"Mais azarado: {get_display_name(bot, ctx, unluck_player['player_id'])} com {luck_player['count_fail']} falhas! (1/{luck_player['average_fail']}) [{luck_player['d20_rolled']}]\n")
    print(f"Total rolado: {data[4]} ")

    text += f"Mais sortudo: {get_display_name(bot, ctx, luck_player['player_id'])} com {luck_player['count_critical']} criticos! (1/{luck_player['average_critical']}) [{luck_player['d20_rolled']}]\n"
    text += f"Mais azarado: {get_display_name(bot, ctx, unluck_player['player_id'])} com {luck_player['count_fail']} falhas! (1/{luck_player['average_fail']}) [{luck_player['d20_rolled']}]\n"
    text += f"Soma de todos os dados rolados: {data[4]} "

    print("Criticos por jogador")
    for r in data[2]:
        print(r.player_id, r.count)

    print("Falhas por jogador")
    for r in data[3]:
        print(r.player_id, r.count)

    await ctx.send(text)
