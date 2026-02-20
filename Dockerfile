FROM python:3.13-slim

LABEL author="Rafael Sandrini" maintainer="rafael@sandrini.com.br"

WORKDIR /app


COPY ./src /app/src
COPY pyproject.toml poetry.lock start-bots.sh /app/
COPY ./src/.env /app/src/.env

RUN apt-get update && apt-get install -y libpq-dev gcc python3-psycopg2

RUN pip install poetry && poetry config virtualenvs.create false && poetry install --only main

RUN chmod +x /app/start-bots.sh

CMD ["bash", "/app/start-bots.sh"]
