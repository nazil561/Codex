FROM public.ecr.aws/docker/library/python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

ARG PIP_INDEX_URL=https://pypi.org/simple
ENV PIP_INDEX_URL=${PIP_INDEX_URL}

COPY pyproject.toml /app/
COPY src /app/src
RUN pip install --no-cache-dir -i ${PIP_INDEX_URL} ".[dev]"

COPY . /app

CMD ["sh", "-c", "alembic upgrade head && uvicorn live_engagement_coach.main:app --host 0.0.0.0 --port 8000"]
