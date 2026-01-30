#!/bin/bash
# Get host IPv4 address (works cross-platform).
# This script is used to retrieve the IPv4 address of the host machine inside a Docker container.
# Usage: ./get_firewall_host.sh

# Function to get the first non-loopback IPv4 address
get_ipv4() {
    local ipv4=""

    # Method 1: Try docker host if available (Docker Desktop for Mac/Windows)
    if [ -z "$ipv4" ] && [ -n "$(command -v getent)" ]; then
        ipv4=$(getent hosts host.docker.internal 2>/dev/null | awk '{print $1}' | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' | head -n 1)
    fi

    # Method 2: Use default gateway (Linux Docker)
    if [ -z "$ipv4" ] && [ -n "$(command -v ip)" ]; then
        ipv4=$(ip route 2>/dev/null | grep -E '^default via' | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | head -n 1)
    fi

    # Method 3: Try to resolve via /etc/hosts
    if [ -z "$ipv4" ]; then
        ipv4=$(grep -E "host\.docker\.internal" /etc/hosts 2>/dev/null | awk '{print $1}' | head -n 1)
    fi

    # Method 4: Fallback - use hostname -I
    if [ -z "$ipv4" ] && [ -n "$(command -v hostname)" ]; then
        ipv4=$(hostname -I 2>/dev/null | awk '{print $1}')
    fi

    echo "$ipv4"
}

# Get and print the IPv4 address
HOST_IP=$(get_ipv4)
echo "$HOST_IP"
