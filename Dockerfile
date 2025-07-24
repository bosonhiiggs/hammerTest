FROM python:3.12-slim

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE hammer.settings

WORKDIR /app

RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/
EXPOSE 8000
WORKDIR /app/hammer/
RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "hammer.wsgi:application"]