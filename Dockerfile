FROM python:3.8-slim-buster

COPY install-packages.sh .
RUN ./install-packages.sh

COPY ./app /app
WORKDIR /app
VOLUME /recordings
RUN pip install -r requirements.txt
CMD python ./twitch_recorder.py