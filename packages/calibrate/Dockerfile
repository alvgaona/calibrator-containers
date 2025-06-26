FROM python:3.11-slim AS build

WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy workspace dependency files
COPY pyproject.toml uv.lock /app/

# Copy packages directory
COPY packages/ /app/packages/

# Install dependencies for the entire workspace
RUN uv sync --frozen --no-dev

FROM python:3.11-slim AS production

WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv in production image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the virtual environment and workspace from build stage
COPY --from=build /app/.venv /app/.venv
COPY --from=build /app/pyproject.toml /app/pyproject.toml
COPY --from=build /app/packages /app/packages

# Make sure we can find the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Expose the FastAPI port
EXPOSE 8000

# Run the FastAPI server using uv to ensure proper workspace package resolution
CMD ["uv", "run", "--package", "calibrate", "uvicorn", "calibrate.main:app", "--host", "0.0.0.0", "--port", "8000"]
