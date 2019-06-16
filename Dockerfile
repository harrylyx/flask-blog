FROM python:3.5.6-alpine

RUN pip3 install --upgrade pip

RUN apk add --no-cache --update python3-dev  gcc build-base

RUN adduser -D flaskblog

WORKDIR /home/flaskblog

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn

COPY app app
COPY migrations migrations
COPY manage.py config.py boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP manage.py

RUN chown -R flaskblog:flaskblog ./
USER flaskblog

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]


