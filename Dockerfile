FROM python:3.7-slim

LABEL author="Rafael Sandrini" maintainer="rafael@sandrini.com.br"

RUN mkdir -p /app 

WORKDIR /app

COPY . /app

RUN pip3 install -r requirements.txt

CMD [ "python", "./discord_client.py" ]