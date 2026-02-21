#!/bin/bash

# Script to generate self-signed SSL certificates for development

set -e

echo "Generating self-signed SSL certificates for LiveMenu API..."

# Create certs directory if it doesn't exist
mkdir -p nginx/certs

# Generate certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/certs/server.key \
  -out nginx/certs/server.crt \
  -subj "/C=US/ST=State/L=City/O=LiveMenu/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,DNS:api,IP:127.0.0.1"

echo "✅ SSL certificates generated successfully!"
echo "   - Certificate: nginx/certs/server.crt"
echo "   - Private Key: nginx/certs/server.key"
echo ""
echo "⚠️  These are self-signed certificates for development only."
echo "   For production, use certificates from a trusted CA (e.g., Let's Encrypt)."
