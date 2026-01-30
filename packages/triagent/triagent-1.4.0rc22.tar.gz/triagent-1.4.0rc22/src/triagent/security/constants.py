"""Security constants for triagent.

IMPORTANT: The EMBEDDED_SALT was generated once and must NEVER be changed.
Changing the salt will make all existing encrypted prompts undecryptable.
"""

# Generated with: python -c "import os; print(os.urandom(32).hex())"
# This salt is unique to this project and must never be changed.
EMBEDDED_SALT = "4706f45db56f7ff356096935ddd65e264b4289bd34f0149056e22ec703ad4c99"
EMBEDDED_SALT_BYTES = bytes.fromhex(EMBEDDED_SALT)

# PBKDF2 configuration
# High iteration count for brute-force resistance
KEY_ITERATIONS = 1_200_000
