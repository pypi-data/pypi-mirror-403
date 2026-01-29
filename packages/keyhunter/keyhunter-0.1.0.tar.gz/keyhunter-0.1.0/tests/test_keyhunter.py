from keyhunter.keyhunter import b58encode


def test_b58encode() -> None:
    # Generate cases: https://learnmeabitcoin.com/technical/keys/base58/
    assert b58encode(b"\x00\x00\x00\x01") == "1112"
    assert b58encode(b"\x05\xab\xcd") == "2uUx"
    assert b58encode(b"\x10\xff\x00\xab\xbc") == "2vDZMDM"
