from base64 import b64encode
from hashlib import md5

CHUNK_SIZE = 1024 * 1024


def calculate_checksum(file_path: str) -> str:
    hasher = md5()
    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(CHUNK_SIZE), b""):
            hasher.update(chunk)
    return b64encode(hasher.digest()).decode("utf-8")
