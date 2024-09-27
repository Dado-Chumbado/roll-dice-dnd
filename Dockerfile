FROM python:3.11-slim

LABEL author="Rafael Sandrini" maintainer="rafael@sandrini.com.br"

WORKDIR /app

COPY ./src /app/src
COPY pyproject.toml poetry.lock /app/

RUN apt-get update && apt-get install -y libpq-dev gcc python3-psycopg2

RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-dev

CMD ["poetry", "run", "python3", "/app/src/main.py"]