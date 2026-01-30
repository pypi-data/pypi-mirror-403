FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (NO Azure CLI - will be installed by /init)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    ca-certificates \
    gnupg \
    lsb-release \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (for MCP servers)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install --upgrade pip uv

# Copy project files (including build hook and encryption scripts)
COPY pyproject.toml README.md hatch_build.py ./
COPY src/ src/
COPY scripts/ scripts/

# Install triagent in development mode (skip encryption for tests)
# Set fallback version for Docker builds (no .git directory available)
ARG SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0+docker
RUN TRIAGENT_SKIP_ENCRYPT=1 SETUPTOOLS_SCM_PRETEND_VERSION=${SETUPTOOLS_SCM_PRETEND_VERSION} uv pip install --system -e ".[dev]"

# Copy tests (optional, for running tests in container)
COPY tests/ tests/

# Create non-root user with sudo access (for Azure CLI install)
RUN useradd -m -u 1000 tester && \
    echo "tester ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    chown -R tester:tester /app
USER tester

# Set npm global directory for non-root user (critical for detection after install)
ENV NPM_CONFIG_PREFIX=/home/tester/.npm-global
ENV PATH=$PATH:/home/tester/.npm-global/bin

# Create triagent config directory and npm global directory
RUN mkdir -p /home/tester/.triagent /home/tester/.npm-global

# Default command
CMD ["bash"]
