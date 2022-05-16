keep_characters = ' _'


def sanitize_filename(filename: str) -> str:
    return ''.join(c for c in filename.strip() if c.isalnum() or c in keep_characters).strip()
