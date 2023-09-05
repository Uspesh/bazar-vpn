FROM python:3.11.0rc1

ENV PYTHONBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN mkdir /vpn

WORKDIR /vpn

COPY . .

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN chmod +x /vpn/docker/app.sh
RUN chmod +x /vpn/docker/celery.sh

#RUN python3 /vpn/src/main.py

CMD ["/vpn/docker/app.sh"]