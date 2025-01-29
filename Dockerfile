FROM python:3.12

ENV PYTHONUNBUFFERED 1
ENV DJANGO_ENV dev
ENV DOCKER_CONTAINER 1
RUN mkdir /app
WORKDIR /app
# EXPOSE 8000

COPY requirements.txt .
RUN apt-get update && apt-get install -y build-essential libmagic-dev libjpeg-dev libgif-dev libcairo2-dev pkg-config libpq-dev python3-dev
RUN pip install -r requirements.txt

COPY manage.py .
# COPY apps apps

# CMD python manage.py collectstatic --no-input
# CMD gunicorn apps.wsgi:application -b 0.0.0.0:8000
