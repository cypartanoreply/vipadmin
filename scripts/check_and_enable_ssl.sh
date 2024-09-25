#!/bin/bash

DOMAIN=${DOMAIN_NAME}

SSL_CERT="/etc/nginx/ssl/live/$DOMAIN/fullchain.pem"
SSL_KEY="/etc/nginx/ssl/live/$DOMAIN/privkey.pem"
SSL_CONF="/etc/nginx/conf.d/ssl.conf"
SSL_TEMPLATE="/etc/nginx/conf.d/ssl.conf.template"

# Check if both SSL certificate and key exist
if [ -f "$SSL_CERT" ] && [ -f "$SSL_KEY" ]; then
    echo "SSL certificate and key for $DOMAIN found. Applying configuration."
    # If both files exist, copy the SSL template to the active configuration
    cp "$SSL_TEMPLATE" "$SSL_CONF"
else
    echo "SSL certificate or key for $DOMAIN missing. Removing active SSL configuration."
    # If either file is missing, remove the active SSL configuration
    rm -f "$SSL_CONF"
fi
