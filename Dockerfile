FROM python:3.10-slim-buster

WORKDIR /usr/app

COPY Pipfile Pipfile.lock ./

RUN pip install pipenv openpyxl gunicorn&& \
    pipenv --bare install --system --ignore-pipfile --dev 

COPY . .
