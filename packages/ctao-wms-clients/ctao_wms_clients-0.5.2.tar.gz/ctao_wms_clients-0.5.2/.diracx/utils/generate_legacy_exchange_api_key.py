"""Generate LegacyExchangeApiKey."""

import base64
import hashlib
import secrets

token = secrets.token_bytes()
# This is the secret to include in the request by setting the
# /DiracX/LegacyExchangeApiKey CS option in your legacy DIRAC installation
CS_LEGACY_EXCHANGE_API_KEY = base64.urlsafe_b64encode(token).decode()

# This is the environment variable to set on the DiracX server
DIRACX_VARIABLE = (
    f"DIRACX_LEGACY_EXCHANGE_HASHED_API_KEY={hashlib.sha256(token).hexdigest()}"
)
print(CS_LEGACY_EXCHANGE_API_KEY)
print(DIRACX_VARIABLE)
