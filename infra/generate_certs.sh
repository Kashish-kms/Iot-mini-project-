#!/usr/bin/env bash
set -e

# ==============================================================================
# VeilSense Automated X.509 TLS Certificate Generator
# Generates Root CA, Server (Broker) Certificate, and Client Credentials
# ==============================================================================

CERTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/certs"
mkdir -p "$CERTS_DIR"
cd "$CERTS_DIR"

echo "=== 1. Generating VeilSense Certificate Authority (Root CA) ==="
openssl req -new -x509 -days 3650 -extensions v3_ca \
    -keyout ca.key -out ca.crt \
    -subj "/C=US/ST=Security/L=Cloud/O=VeilSense/CN=VeilSense-Root-CA" \
    -nodes

echo "=== 2. Generating Mosquitto Broker Server Key & CSR ==="
openssl req -new -out server.csr -keyout server.key \
    -subj "/C=US/ST=Security/L=Cloud/O=VeilSense/CN=localhost" \
    -nodes

# Create SAN Extension config
cat > server_san.ext << EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = broker.veilsense.local
DNS.3 = mosquitto
IP.1 = 127.0.0.1
IP.2 = 192.168.1.100
EOF

openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
    -out server.crt -days 730 -extfile server_san.ext

echo "=== 3. Generating ESP32 Edge Client Certificate ==="
openssl req -new -out client.csr -keyout client.key \
    -subj "/C=US/ST=Security/L=Edge/O=VeilSense/CN=ESP32-NODE-01" \
    -nodes

openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
    -out client.crt -days 730

chmod 600 *.key
chmod 644 *.crt

echo "=== TLS Certificates Successfully Generated in $CERTS_DIR ==="
ls -l
