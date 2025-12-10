def first_nonempty(iterable, default=None):
    for x in iterable:
        if x and str(x).strip():
            return x.strip()
    return default

def find_all_lines_with_keywords(lines, keywords):
    """
    Return lines that contain any of the provided keywords (case-insensitive).
    """
    out = []
    for l in lines:
        lower = l.lower()
        for k in keywords:
            if k.lower() in lower:
                out.append(l)
                break
    return out
