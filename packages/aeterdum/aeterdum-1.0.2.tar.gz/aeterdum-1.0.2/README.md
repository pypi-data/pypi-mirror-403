# Aeterdum Python SDK

Official Python client for [Aeterdum](https://aeterdum.com), the immutable audit log service.

## Installation

```bash
pip install aeterdum
```

## Usage

### Initialization

```python
import os
from aeterdum import Aeterdum

# Recommended: Use environment variable AETERDUM_API_KEY
client = Aeterdum() 

# For specific regions
# client = Aeterdum(base_url="https://eu.aeterdum.com")

# With signature verification
# client = Aeterdum(server_public_key="0be...")

# Or pass explicitly
# client = Aeterdum(api_key="sk_...")
```

### Ingesting Logs

Ingest an event into the immutable ledger.

```python
with Aeterdum() as client:
    log = client.logs.create(
        event="model.trained",
        actor="pipeline_worker_1",
        payload={
            "accuracy": 0.98,
            "dataset": "v2.1"
        },
        metadata={
            "env": "production"
        }
    )
    
    print(f"Log ID: {log['id']}")
```

### Verifying Logs

Verify the cryptographic integrity of any log entry. This performs three checks locally:
1. Recomputes the Merkle Root from the provided proof to ensure inclusion in the log tree.
2. Recomputes the hash of the log payload to ensure the content matches the stored hash (tamper detection).
3. (If public key provided) Verifies the Ed25519 signature of the root to ensure server authenticity.

```python
result = client.logs.verify("log_12345")

if result.get("client_verified"):
    print("Merkle Proof and Payload Verified")

if result.get("signature_verified"):
    print("Digital Signature Valid")
```

```python
result = client.logs.verify("log_2023...")

if result.get("client_verified"):
    print(f"Log verified! Merkle Root: {result['merkle_root']}")
else:
    print("Verification failed.")
```

### Listing Logs

retrieve your audit trail for analysis.

```python
logs = client.logs.list(limit=20)

for log in logs["data"]:
    print(f"{log['timestamp']}: {log['event']}")
```

### Async/Sync
Currently, this SDK provides a synchronous interface using `httpx`.
