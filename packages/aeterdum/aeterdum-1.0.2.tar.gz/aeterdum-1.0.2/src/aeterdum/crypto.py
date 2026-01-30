import hashlib
import math
import json
from typing import List, Any, Dict

def sha256(data: str) -> str:
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def compute_log_hash(prev_hash: str, event: str, actor: str, timestamp: str, payload: Any) -> str:
    """
    Computes the SHA-256 hash of a log entry to verify integrity.
    Uses canonical JSON stringification (sorted keys, no spaces).
    """
    data = {
        "prev_hash": prev_hash,
        "event": event,
        "actor": actor,
        "timestamp": timestamp,
        "payload": payload
    }
    # Matches Go's json.Marshal: Sort keys, no separator spaces
    canonical_json = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return sha256(canonical_json)

def compute_merkle_root(proof: List[str], leaf_hash: str, index: int, total_leaves: int) -> str:
    current_hash = leaf_hash
    current_index = index
    current_total = total_leaves
    proof_idx = 0

    while current_total > 1:
        if current_total % 2 == 1:
            # Odd number of leaves
            if current_index == current_total - 1:
                # Promoted
                current_total = math.ceil(current_total / 2)
                current_index = math.floor(current_index / 2)
                continue
        
        if proof_idx >= len(proof):
            raise ValueError("Merkle proof is too short")
        
        sibling = proof[proof_idx]
        proof_idx += 1

        if current_index % 2 == 0:
            # Left
            current_hash = sha256(current_hash + sibling)
        else:
            # Right
            current_hash = sha256(sibling + current_hash)
        
        current_total = math.ceil(current_total / 2)
        current_index = math.floor(current_index / 2)
    
    
    return current_hash

def verify_signature(public_key_hex: str, signature_hex: str, message: str) -> bool:
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        
        public_key_bytes = bytes.fromhex(public_key_hex)
        signature_bytes = bytes.fromhex(signature_hex)
        message_bytes = message.encode('utf-8')

        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_key.verify(signature_bytes, message_bytes)
        return True
    except Exception as e:
        # print(f"Signature verification failed: {e}")
        return False
