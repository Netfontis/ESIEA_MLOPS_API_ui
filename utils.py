def color_for_count(n: int) -> str:
    if n >= 280: return "#e63946"   # rouge
    if n >= 240: return "#ffb703"   # jaune
    return "#20a08d"                # vert

def valid_text(t: str) -> bool:
    return isinstance(t, str) and 1 <= len(t) <= 280 and not t.isspace()
