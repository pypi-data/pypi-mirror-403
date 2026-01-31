from os import path
from typing import Callable

from rich.progress import Progress

ProgressCallback = Callable[[int, int, int], None]


class UploadProgress:
    def __init__(self, filename: str, progress: Progress):
        self.file = open(filename, "rb")
        self.total = path.getsize(filename)
        self.read_bytes = 0
        self.progress = progress
        self.task = progress.add_task(f"Uploading file {filename}", total=self.total)

    def __len__(self):
        return self.total

    def read(self, chunk_size=8192):
        data = self.file.read(chunk_size)

        if not data:
            return b""

        self.read_bytes += len(data)
        self.progress.update(self.task, advance=len(data))
        return data

    def close(self):
        self.file.close()
