# First stage: build with Poetry and dependencies
FROM python:3.12-slim AS builder

# Set environment variables for Poetry installation
ENV POETRY_VERSION=1.8.4 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install curl and Poetry
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && curl -sSL https://install.python-poetry.org | python3 -
# Set working directory and install dependencies
WORKDIR /app
COPY pyproject.toml poetry.lock ./

# resolve possible changes in pyproject.toml file
RUN /root/.local/bin/poetry lock --no-update
RUN /root/.local/bin/poetry install --only main --no-root --no-interaction --no-ansi --sync

# Second stage: copy the dependencies and source code to a minimal image
FROM python:3.12-slim AS final

# Copy installed dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
WORKDIR /app
COPY ./src .
USER 1001
# Expose port and define entry point
EXPOSE 5000
CMD ["python", "main.py"]
