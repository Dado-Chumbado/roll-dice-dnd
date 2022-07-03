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