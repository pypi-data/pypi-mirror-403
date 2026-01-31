def rail_fence(text: str, rails: int) -> str:
    if rails < 2:
        return text

    fence = [[] for _ in range(rails)]
    rail, direction = 0, 1

    for ch in text:
        fence[rail].append(ch)
        rail += direction
        if rail == 0 or rail == rails - 1:
            direction *= -1

    return "".join("".join(r) for r in fence)
