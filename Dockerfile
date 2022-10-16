FROM python:3.9-slim

LABEL author="Rafael Sandrini" maintainer="rafael@sandrini.com.br"

RUN mkdir -p /app 

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y libpq-dev python-dev gcc python3-psycopg2

RUN pip3 install -r requirements.txt