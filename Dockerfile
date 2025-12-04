FROM python:3.11-alpine

RUN addgroup -S app && adduser -S app -G app

ENV VIRTUAL_ENV=/app/.deps
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

RUN apk update && apk add --no-cache \
    build-base \
    libffi-dev \
    postgresql-dev \
    postgresql-client \
    && rm -rf /var/cache/apk/*

RUN python3 -m venv $VIRTUAL_ENV

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R app:app /app
RUN chown -R app:app /app/alembic/versions

ENV PYTHONPATH="/app"

# run as root to manage mounted volumes (uploads) then start services
CMD sh -c "\
  mkdir -p \"${MEDIA_ROOT:-/app/uploads}\" && chmod -R 777 \"${MEDIA_ROOT:-/app/uploads}\" && \
  until pg_isready -h db -p 5432; do \
    echo 'Waiting for database...'; \
    sleep 2; \
  done; \
  alembic upgrade head && \
  uvicorn app.main:app --host 0.0.0.0 --port 8000"
