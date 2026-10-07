# ==============================================================================
# VeilSense Automated X.509 TLS Certificate Generator (PowerShell)
# ==============================================================================

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$CertsDir = Join-Path $ScriptDir "certs"
New-Item -ItemType Directory -Force -Path $CertsDir | Out-Null
Set-Location $CertsDir

Write-Host "=== 1. Generating VeilSense Certificate Authority (Root CA) ===" -ForegroundColor Cyan
openssl req -new -x509 -days 3650 -extensions v3_ca `
    -keyout ca.key -out ca.crt `
    -subj "/C=US/ST=Security/L=Cloud/O=VeilSense/CN=VeilSense-Root-CA" `
    -nodes

Write-Host "=== 2. Generating Mosquitto Broker Server Key & CSR ===" -ForegroundColor Cyan
openssl req -new -out server.csr -keyout server.key `
    -subj "/C=US/ST=Security/L=Cloud/O=VeilSense/CN=localhost" `
    -nodes

$SanContent = @"
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
"@
Set-Content -Path "server_san.ext" -Value $SanContent

openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial `
    -out server.crt -days 730 -extfile server_san.ext

Write-Host "=== 3. Generating ESP32 Edge Client Certificate ===" -ForegroundColor Cyan
openssl req -new -out client.csr -keyout client.key `
    -subj "/C=US/ST=Security/L=Edge/O=VeilSense/CN=ESP32-NODE-01" `
    -nodes

openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial `
    -out client.crt -days 730

Write-Host "=== TLS Certificates Successfully Generated in $CertsDir ===" -ForegroundColor Green
Get-ChildItem
