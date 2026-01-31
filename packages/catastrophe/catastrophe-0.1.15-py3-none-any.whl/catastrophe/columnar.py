def columnar(text: str, key: str) -> str:
    key_order = sorted(range(len(key)), key=lambda i: key[i])
    cols = len(key)
    rows = (len(text) + cols - 1) // cols

    grid = [[""] * cols for _ in range(rows)]
    i = 0
    for r in range(rows):
        for c in range(cols):
            if i < len(text):
                grid[r][c] = text[i]
                i += 1

    return "".join(grid[r][c] for c in key_order for r in range(rows))
