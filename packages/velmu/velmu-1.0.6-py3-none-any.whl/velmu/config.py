import os

# Base URLs
# Default to Production, but allow overrides via env vars for local dev
API_BASE_URL = os.getenv('VELMU_API_URL', 'http://localhost:4000/api')
GATEWAY_URL = os.getenv('VELMU_WS_URL', 'http://localhost:4000')
