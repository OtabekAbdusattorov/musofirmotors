FROM python:3.11

ADD main.py translates.py musofirmotors.db ./

RUN pip install pyTelegramBotAPI requests

CMD [ "python", "./main.py", "host", "0.0.0.0", "--port", "80"]