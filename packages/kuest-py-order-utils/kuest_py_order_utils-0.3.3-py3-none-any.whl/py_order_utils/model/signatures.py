# ECDSA EIP712 signatures signed by EOAs.
EOA = 0

# EIP712 signatures signed by EOAs that own proxy wallets.
KUEST_PROXY = 1

# EIP712 signatures signed by EOAs that own Gnosis Safe wallets.
KUEST_GNOSIS_SAFE = 2

# EIP-1271 signatures from contract wallets.
KUEST_EIP1271 = 3

# Neutral aliases for consumers who don't want branded constants.
PROXY_WALLET = KUEST_PROXY
GNOSIS_SAFE_WALLET = KUEST_GNOSIS_SAFE
EIP1271_WALLET = KUEST_EIP1271
