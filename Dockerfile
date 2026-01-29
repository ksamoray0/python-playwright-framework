FROM python:3.12-slim

# System deps often needed for Playwright browsers
RUN apt-get update && apt-get install -y \
  wget \
  gnupg \
  ca-certificates \
  libnss3 \
  libatk1.0-0 \
  libatk-bridge2.0-0 \
  libcups2 \
  libdrm2 \
  libxkbcommon0 \
  libxcomposite1 \
  libxdamage1 \
  libxfixes3 \
  libxrandr2 \
  libgbm1 \
  libasound2 \
  libpangocairo-1.0-0 \
  libpango-1.0-0 \
  libgtk-3-0 \
  libxshmfence1 \
  libx11-xcb1 \
  libxcb1 \
  libxext6 \
  libx11-6 \
  fonts-liberation \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only dependency metadata first (better caching)
COPY pyproject.toml /app/pyproject.toml
COPY tests /app/tests

# Install python deps
RUN python -m pip install --upgrade pip \
  && python -m pip install pytest pytest-html playwright pytest-xdist

# Install browsers
RUN python -m playwright install --with-deps

# Default command
CMD ["python", "-m", "pytest"]
