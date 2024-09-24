#!/bin/bash

# Path to check if SSL certificate exists
CERT_PATH="/etc/nginx/ssl/live/memo.cyparta.com/fullchain.pem"

# Wait for certbot to generate the SSL certificate
while [ ! -f "$CERT_PATH" ]; do
    echo "Waiting for SSL certificate to be generated..."
    sleep 5
done

echo "SSL certificate found! Enabling SSL in Nginx..."

# Replace the nginx config with the SSL-enabled version
cp /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/nginx.conf

# Reload Nginx to apply the new SSL configuration
nginx -s reload

echo "Nginx reloaded with SSL!"
