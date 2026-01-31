import base64


def encode_base64(payload: str) -> str:
    """Encode a string using base64."""
    return base64.b64encode(payload.encode("utf-8")).decode("utf-8")


def decode_base64(payload: str) -> str:
    """Decode a Base64-encoded string to a UTF-8 string."""
    return base64.b64decode(payload).decode("utf-8")

