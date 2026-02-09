"""Tests for ID generation."""

from lkr.idgen import decode_base36, encode_base36, generate_id, is_valid_base36


def test_encode_zero():
    assert encode_base36(0) == "0"


def test_encode_decode_roundtrip():
    for n in [0, 1, 35, 36, 1000, 1099511627775]:
        assert decode_base36(encode_base36(n)) == n


def test_encode_known_values():
    assert encode_base36(10) == "a"
    assert encode_base36(35) == "z"
    assert encode_base36(36) == "10"


def test_generate_id_length():
    entry_id = generate_id()
    assert len(entry_id.value) == 8


def test_generate_id_valid_base36():
    for _ in range(100):
        entry_id = generate_id()
        assert is_valid_base36(entry_id.value)


def test_generate_id_uniqueness():
    ids = {generate_id().value for _ in range(1000)}
    assert len(ids) == 1000


def test_is_valid_base36():
    assert is_valid_base36("abc123")
    assert is_valid_base36("0")
    assert is_valid_base36("zzzzzzzz")
    assert not is_valid_base36("")
    assert not is_valid_base36("ABC")
    assert not is_valid_base36("abc-def")
    assert not is_valid_base36("123456789")  # 9 chars


def test_generate_id_has_prefix():
    entry_id = generate_id()
    assert len(entry_id.prefix) == 2
