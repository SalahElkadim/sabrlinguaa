def parse_version(version_str: str):
    parts = []
    for p in str(version_str).strip().split('.'):
        digits = ''.join(ch for ch in p if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def compare_versions(v1: str, v2: str) -> int:
    t1, t2 = parse_version(v1), parse_version(v2)
    length = max(len(t1), len(t2))
    t1 = t1 + (0,) * (length - len(t1))
    t2 = t2 + (0,) * (length - len(t2))

    if t1 < t2:
        return -1
    if t1 > t2:
        return 1
    return 0
