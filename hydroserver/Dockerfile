FROM python:3.8-slim

WORKDIR /app

RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install psycopg2

COPY ./requirements.txt .
RUN pip install -r requirements.txt
RUN pip install gunicorn

COPY . .

EXPOSE 80

CMD ["gunicorn", "-b", "api:80", "hydroserver:app"]
#CMD ["flask", "run", "-p", "80"]

