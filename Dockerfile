FROM python:3.11-slim AS build

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml /app/
COPY uv.lock /app/

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY calibrate/ /app/calibrate/

FROM python:3.11-slim AS production

WORKDIR /app

# Install uv in production image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the virtual environment from build stage
COPY --from=build /app/.venv /app/.venv

# Copy application files
COPY --from=build /app/calibrate /app/calibrate

# Make sure we can find the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Expose the FastAPI port
EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "calibrate.main:app", "--host", "0.0.0.0", "--port", "8000"]
