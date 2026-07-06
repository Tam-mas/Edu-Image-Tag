from edu_image_tag.hashing import sha256_hex, short_hash


def test_sha256_hex_is_deterministic_and_64_chars():
    h = sha256_hex(b"hello")
    assert h == sha256_hex(b"hello")
    assert len(h) == 64
    assert h != sha256_hex(b"world")


def test_short_hash_takes_prefix():
    full = sha256_hex(b"hello")
    assert short_hash(full) == full[:8]
    assert short_hash(full, 12) == full[:12]
