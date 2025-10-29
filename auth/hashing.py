"""
Password hashing/verification using Passlib's bcrypt.

- hash_password(): turns a plaintext password into a salted bcrypt hash for safe storage.
- verify_password(): compares a plaintext password against the stored hash.

Notes:
- salt: a small random string added before hashing so identical passwords produce different hashes.
- salted bcrypt hash = hash + embedded salt; each hash is unique even for the same password.
- salt + cost factor = randomness + configurable CPU cost (harder to brute-force).
- Never store plaintext passwords.
- bcrypt automatically handles salt + cost factor.
- pwd_context lets us swap/upgrade hashing schemes later without changing call sites.
"""

from passlib.context import CryptContext
# bcrypt_sha256 mitigates the 72-byte limit by pre-hashing with sha256
pwd_context = CryptContext(
    schemes=["bcrypt_sha256"],
    deprecated="auto",
)

def hash_password(p: str) -> str:
    return pwd_context.hash(p)

def verify_password(p: str, h: str) -> bool:
    return pwd_context.verify(p, h)

"""
Password hashing/verification using Passlib.

- Uses 'bcrypt_sha256' to avoid bcrypt's 72-byte password limit.
- hash_password(): plaintext -> salted hash (with sha256 pre-hash).
- verify_password(): plaintext vs stored hash.

Notes:
- Never store plaintext passwords.
- Passlib manages salt & cost; we can tune rounds centrally here later.
"""

