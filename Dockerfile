# syntax=docker/dockerfile:1

# Grab Python, make a directory to store everything
FROM python:3.10.4-slim-buster

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.3.2

# Get Poetry
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg
RUN pip install "poetry==$POETRY_VERSION"

# Copy just the requirements for caching
WORKDIR /app
COPY poetry.lock pyproject.toml ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-root --no-interaction --no-ansi 

# Cop everything else
COPY . .

# Get inside
ENTRYPOINT ["python3"]
CMD ["-u", "main.py"]