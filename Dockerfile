FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY apps ./apps
COPY config ./config
COPY manage.py ./
COPY pytest.ini ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir ".[test]"

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
