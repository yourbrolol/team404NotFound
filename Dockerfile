FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# copy requirements from subfolder
COPY ContestKeeper/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy project
COPY ContestKeeper/ .

EXPOSE 8000

RUN python manage.py collectstatic --noinput

CMD ["sh", "-c", "python manage.py migrate && daphne -b 0.0.0.0 -p 8000 ContestKeeper.asgi:application"]
