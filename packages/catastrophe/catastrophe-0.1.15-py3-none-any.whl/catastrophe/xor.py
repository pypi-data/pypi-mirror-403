def xor(data, key):
    if isinstance(data, str):
        data = data.encode("utf-8")
    if isinstance(key, str):
        key = key.encode("utf-8")

    if not key:
        raise ValueError("key must not be empty")

    out = bytearray()
    for i, b in enumerate(data):
        out.append(b ^ key[i % len(key)])

    try:
        return out.decode("utf-8")
    except UnicodeDecodeError:
        return bytes(out)
