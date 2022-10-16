import os
from celery import Celery
from stats_db import insert_roll

app = Celery('.',
             broker=os.getenv('BROKER_URL'),
             include=['tasks'])
app.conf.task_default_queue = 'dices'

if __name__ == '__main__':
    app.start()


@app.task(bind=True)
def save_roll(self, author, channel, dice_str, value, critical=False, fail=False):
    try:
        # print(context.author.id, context.channel.name, dice_str, value, critical, fail)
        # context.author.id, context.author.display_name, context.channel.name,
        insert_roll(author, channel, dice_str, value, critical, fail)
    except Exception as e:
        print(e)
        # logger.error('exception raised, it would be retry after 5 seconds')
        raise self.retry(exc=e, countdown=5)
