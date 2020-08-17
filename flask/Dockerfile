FROM python:3.7.2-stretch
WORKDIR /app
ADD . /app
RUN pip install -r requirements.txt
RUN pip install python-dotenv
RUN export APP_SETTINGS=/client-volume/data/production_config.cfg
CMD ["uwsgi", "app.ini"]
