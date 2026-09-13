#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Generate a self-signed CA + server key/cert pair for the AIoT MQTT broker.
#
# Usage:
#     bash broker/certs/generate_certs.sh
#
# Outputs (overwritten each run):
#   broker/certs/ca.key     (private CA key — protect this)
#   broker/certs/ca.crt     (shared CA cert; distribute to every MQTT client)
#   broker/certs/server.key (broker private key)
#   broker/certs/server.crt (broker cert, signed by CA, SANs: broker, localhost)
#
# All keys are chmod 600 (readable only by owner).
# ---------------------------------------------------------------------------
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

echo "[certs] Generating self-signed CA in $HERE"

# ---- Clean old artifacts ---------------------------------------------------
rm -f ca.key ca.crt server.key server.csr server.crt server.srl

# ---- CA -------------------------------------------------------------------
openssl genrsa -out ca.key 2048 2>/dev/null
chmod 600 ca.key

openssl req -new -x509 \
    -days 3650 \
    -key ca.key \
    -out ca.crt \
    -subj "/CN=AIoT-CA/O=AIoT-Sim/C=US" \
    -addext "basicConstraints=critical,CA:TRUE" \
    -addext "keyUsage=critical,keyCertSign,cRLSign"

echo "[certs] CA built -> ca.crt"

# ---- Server key + CSR -----------------------------------------------------
openssl genrsa -out server.key 2048 2>/dev/null
chmod 600 server.key

SAN_CONFIG="[req]
distinguished_name=dn
prompt=no
req_extensions=v3_req
[dn]
CN=broker
O=AIoT-Sim
C=US
[v3_req]
basicConstraints=CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=@alt
[alt]
DNS.1=broker
DNS.2=localhost
IP.1=127.0.0.1"

SAN_FILE="$(mktemp)"
printf '%s\n' "$SAN_CONFIG" > "$SAN_FILE"

openssl req -new \
    -key server.key \
    -out server.csr \
    -config "$SAN_FILE"

# ---- Sign server CSR with CA ----------------------------------------------
openssl x509 -req \
    -in server.csr \
    -CA ca.crt \
    -CAkey ca.key \
    -CAcreateserial \
    -out server.crt \
    -days 1825 \
    -sha256 \
    -extfile "$SAN_FILE" \
    -extensions v3_req 2>/dev/null

chmod 644 ca.crt server.crt
rm -f server.csr "$SAN_FILE" server.srl

echo "[certs] Done. Final artifacts:"
ls -l ca.crt ca.key server.crt server.key
