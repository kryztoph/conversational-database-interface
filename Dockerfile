FROM python:3.11-slim

WORKDIR /app

# Zscaler certificate (set via: docker compose build --build-arg CERT_FILE=Zscaler_Root_CA.cer)
ARG CERT_FILE=
COPY . /tmp/build-context/
RUN if [ -n "$CERT_FILE" ] && [ -f "/tmp/build-context/$CERT_FILE" ]; then \
    cp "/tmp/build-context/$CERT_FILE" /usr/local/share/ca-certificates/zscaler.crt && \
    update-ca-certificates; \
    fi && \
    rm -rf /tmp/build-context
ENV REQUESTS_CA_BUNDLE=${CERT_FILE:+/etc/ssl/certs/ca-certificates.crt}
ENV SSL_CERT_FILE=${CERT_FILE:+/etc/ssl/certs/ca-certificates.crt}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy and set entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Set entrypoint to check user before running app
ENTRYPOINT ["/docker-entrypoint.sh"]

# Run the chat application
CMD ["python", "chat.py"]
