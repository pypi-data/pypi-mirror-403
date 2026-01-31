def scytale(text: str, rows: int) -> str:
    if rows <= 0:
        raise ValueError("rows must be > 0")
    cols = (len(text) + rows - 1) // rows
    padded = text.ljust(rows * cols)
    grid = [padded[i::rows] for i in range(rows)]
    return "".join("".join(row[c] for row in grid if c < len(row)) for c in range(cols))
