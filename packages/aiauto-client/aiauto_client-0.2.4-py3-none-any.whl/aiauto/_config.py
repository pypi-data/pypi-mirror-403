import os

# Base URL for aiauto services (path-based routing)
# Single hostname used for all services: API, dashboard, gRPC storage
# Format: scheme://host:port (port is required)
# Example: "https://aiauto.pangyo.ainode.ai:443" or "https://192.168.1.100:8080"
AIAUTO_BASE_URL = os.environ.get("AIAUTO_BASE_URL", "https://aiauto.pangyo.ainode.ai:443")

# Skip SSL certificate verification (for self-signed certificates)
# Set to "true", "1", or "yes" to disable SSL verification
# WARNING: Only use in development/internal environments with self-signed certificates
AIAUTO_INSECURE = os.environ.get("AIAUTO_INSECURE", "").lower() in ("true", "1", "yes")
