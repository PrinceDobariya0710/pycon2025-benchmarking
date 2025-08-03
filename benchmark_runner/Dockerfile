# Use the official wrk image as our base
FROM openeuler/wrk:latest as wrk

# Use Python slim image for the final stage
FROM python:3.11-slim

# Copy wrk from the official image
COPY --from=wrk /usr/local/bin/wrk /usr/local/bin/wrk

# Install curl, build essentials, and Docker CLI
RUN apt-get update && \
    apt-get install -y curl build-essential ca-certificates gnupg && \
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg && \
    echo \
        "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
        "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
        tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-ce-cli && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install uv for faster Python package management
# RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV UV_SYSTEM_PYTHON=1

# Set up the working directory
WORKDIR /app

# Copy the Python requirements from the correct sub-directory
COPY benchmark_runner/requirements.txt .

# Install dependencies using uv (much faster than pip)
# Install dependencies using uv (much faster than pip)
RUN uv pip install --no-cache -r requirements.txt

# Copy only the benchmark script
COPY benchmark_wrk.py .

# The command to run the benchmark
CMD ["python", "benchmark_wrk.py"]
