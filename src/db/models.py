import os
from dotenv import load_dotenv
import datetime
import peewee
from peewee import *
import logging

logger = logging.getLogger(__name__)
load_dotenv()

pg_db = PostgresqlDatabase(os.getenv("db"), user=os.getenv("user"), password=os.getenv("pass"),
                           host=os.getenv("host"), port=os.getenv("port"))


class PlayerStats(Model):
    id = AutoField()
    player_id = BigIntegerField()
    display_name = CharField()
    # channel = CharField()
    #
    # total_dice_rolled = IntegerField(default=0)
    #
    # total_d20_rolled = IntegerField(default=0)
    # total_d20_values_rolled = BigIntegerField(default=0)
    # total_d20_critical_rolled = IntegerField(default=0)
    # total_d20_fails_rolled = IntegerField(default=0)
    #
    # total_d4_rolled = IntegerField(default=0)
    # total_d4_values_rolled = IntegerField(default=0)
    # total_d6_rolled = IntegerField(default=0)
    # total_d6_values_rolled = IntegerField(default=0)
    # total_d8_rolled = IntegerField(default=0)
    # total_d8_values_rolled = IntegerField(default=0)
    # total_d10_rolled = IntegerField(default=0)
    # total_d10_values_rolled = IntegerField(default=0)
    # total_d12_rolled = IntegerField(default=0)
    # total_d12_values_rolled = IntegerField(default=0)
    # total_d100_rolled = IntegerField(default=0)
    # total_d100_values_rolled = IntegerField(default=0)
    #
    # sum_dice_number_rolled = BigIntegerField(default=0)

    class Meta:
        database = pg_db


class RollDb(Model):
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
        table_name = "roll"


def setup_db():
    logger.info("Setting up DB")
    if not bool(os.getenv("save_stats_db")):
        logger.info(f"Using DB to save stats: {os.getenv("save_stats_db") == False}")
        return True

    logger.info("Connecting and preparing DB")
    pg_db.connect()
    try:
        pg_db.create_tables([PlayerStats, RollDb])
    except peewee.OperationalError:
        pass
    except Exception as e:
        logger.error(f"Exception setup_db {e}")
        raise
    finally:
        pg_db.close()


try:
    setup_db()
finally:
    if os.getenv("save_stats_db"):
        pg_db.close()
