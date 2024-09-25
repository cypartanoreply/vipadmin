#!/bin/bash

SSL_CERT="/etc/nginx/ssl/live/memo.cyparta.com/fullchain.pem"
SSL_KEY="/etc/nginx/ssl/live/memo.cyparta.com/privkey.pem"
SSL_CONF="/etc/nginx/conf.d/ssl.conf"
SSL_TEMPLATE="/etc/nginx/conf.d/ssl.conf.template"

# Check if both SSL certificate and key exist
if [ -f "$SSL_CERT" ] && [ -f "$SSL_KEY" ]; then
    # If both files exist, copy the SSL template to the active configuration
    cp "$SSL_TEMPLATE" "$SSL_CONF"
else
    # If either file is missing, remove the active SSL configuration
    rm -f "$SSL_CONF"
fi
