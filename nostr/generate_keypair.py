#!/usr/bin/env python3
"""
Generate a Nostr keypair for Aletheia using secp256k1.

Nostr uses:
- Private key: 32 bytes (64 hex chars)
- Public key: 32 bytes x-coordinate of secp256k1 point (64 hex chars)
- npub/nsec: bech32 encoded versions

A+W
"""

import os
import hashlib
import json

# For secp256k1, we need the cryptography library or a simple implementation
# Let's use a basic approach with the available libraries

def generate_nostr_keypair():
    """Generate a Nostr keypair."""
    # Generate 32 random bytes for private key
    private_key_bytes = os.urandom(32)
    private_key_hex = private_key_bytes.hex()

    # For public key, we need secp256k1
    # Using hashlib as a placeholder - in production use proper secp256k1
    # This is a simplified version - proper implementation needs secp256k1 library

    # For now, we'll derive a deterministic "public key" hash
    # (This is NOT cryptographically correct, just for storage placeholder)
    # TODO: Install secp256k1 library for proper implementation

    pubkey_hash = hashlib.sha256(private_key_bytes).hexdigest()

    return {
        "private_key_hex": private_key_hex,
        "public_key_hex": pubkey_hash,  # Placeholder - needs proper secp256k1
        "note": "This is a placeholder keypair. Install secp256k1 for proper Nostr keys."
    }


if __name__ == "__main__":
    # Check if keypair already exists
    keypair_file = "/home/author_prime/aletheia/nostr/keypair.json"

    if os.path.exists(keypair_file):
        print("Keypair already exists. Not overwriting.")
        with open(keypair_file) as f:
            data = json.load(f)
            print(f"Public key: {data['public_key_hex']}")
    else:
        keypair = generate_nostr_keypair()
        keypair["identity"] = "Aletheia"
        keypair["created"] = "2026-02-06"
        keypair["purpose"] = "Nostr identity for publishing thoughts to the decentralized web"

        with open(keypair_file, "w") as f:
            json.dump(keypair, f, indent=2)

        print(f"Keypair generated and saved to {keypair_file}")
        print(f"Public key: {keypair['public_key_hex']}")
        print("\nNote: Install 'secp256k1' or 'nostr' Python package for proper keys.")
