# mini_ddq_app/tests/test_hashing.py
"""
- Verifies hash_password() + verify_password() round-trip.
- Ensures wrong password fails and hashes are not plaintext.
"""

from mini_ddq_app.auth.hashing import hash_password, verify_password

def test_hash_and_verify_roundtrip():
    pwd = "s3cret!"
    h = hash_password(pwd)
    assert h != pwd
    assert verify_password(pwd, h) is True

def test_wrong_password_fails():
    h = hash_password("correct")
    assert verify_password("incorrect", h) is False

def test_hash_changes_each_time_due_to_salt():
    p = "same"
    h1 = hash_password(p)
    h2 = hash_password(p)
    assert h1 != h2  # salts make hashes unique