# Example Dockerfile for deploying an agent using agent-framework-lib from PyPI
# This is a minimal production-ready setup

FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for Playwright and general operation
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy your agent code
COPY pyproject.toml ./
COPY your_agent.py ./

# Install agent-framework-lib with desired extras
# Available extras: [llamaindex], [microsoft], [mongodb], [s3], [minio], [multimodal], [all]
RUN uv pip install --system agent-framework-lib[all]

# Install your project dependencies
RUN uv sync --system

# Run post-install to setup Playwright browsers and Deno (lazy install on first use)
# This is optional - they will auto-install on first use if not done here
RUN python -c "from agent_framework.utils.post_install import post_install; post_install()"

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run your agent
CMD ["python", "your_agent.py"]
