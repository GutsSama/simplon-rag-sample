FROM python:3.14-slim-bookworm

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (without installing the project itself)
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code
COPY . .

# Install the project
RUN uv sync --frozen --no-dev

# Expose port
EXPOSE 8000

# Start the application
CMD ["uv", "run", "python", "main.py"]
