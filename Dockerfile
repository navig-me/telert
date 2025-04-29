FROM python:3.12-slim

# Install dependencies for audio notifications and utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    mpg123 \
    alsa-utils \
    pulseaudio \
    libnotify-bin \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy package files
COPY . .

# Install telert with optional dependencies and FastAPI for server mode
RUN pip install --no-cache-dir -e .[audio,desktop] fastapi uvicorn

# Create a directory for config
RUN mkdir -p /root/.config/telert

# Create a directory for server data (if using server mode)
RUN mkdir -p /app/data

# Default port for server mode
EXPOSE 8000

# Copy the server script
COPY packaging/docker/server.py /app/

# Set the entrypoint script
COPY packaging/docker/entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Use the entrypoint script to handle different modes
ENTRYPOINT ["/app/entrypoint.sh"]

# Default to help mode
CMD ["--help"]