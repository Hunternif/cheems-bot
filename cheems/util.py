from itertools import tee

keep_characters = ' _'


def sanitize_filename(filename: str) -> str:
    return ''.join(c for c in filename.strip() if c.isalnum() or c in keep_characters).strip()


def pairwise(iterable):
    """s -> (s0, s1), (s1, s2), (s2, s3), ..."""
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)
