import os
from celery import Celery

app = Celery('back',
             broker=os.getenv('BROKER_URL'),
             include=['back.tasks'])
app.conf.task_default_queue = 'dices'

if __name__ == '__main__':
    app.start()
