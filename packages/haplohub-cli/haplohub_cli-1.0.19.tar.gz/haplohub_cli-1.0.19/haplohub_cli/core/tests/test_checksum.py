import base64
import hashlib
import os
import tempfile
from unittest import TestCase
from unittest.mock import patch

from haplohub_cli.core.checksum import calculate_checksum


class ChecksumTestCase(TestCase):
    def test_calculate_checksum_matches_md5_base64(self):
        data = b"hello world"
        with tempfile.NamedTemporaryFile(delete=False) as file:
            file.write(data)
            file_path = file.name

        try:
            expected = base64.b64encode(hashlib.md5(data).digest()).decode("utf-8")
            self.assertEqual(calculate_checksum(file_path), expected)
        finally:
            os.remove(file_path)

    def test_calculate_checksum_reads_in_chunks(self):
        data = b"abcdefghijklmnopqrstuvwxyz"
        expected = base64.b64encode(hashlib.md5(data).digest()).decode("utf-8")

        class FakeFile:
            def __init__(self, payload: bytes):
                self.payload = payload
                self.offset = 0
                self.read_calls = []

            def read(self, size=-1):
                self.read_calls.append(size)
                if size is None or size < 0:
                    raise AssertionError("read called without a chunk size")
                if self.offset >= len(self.payload):
                    return b""
                chunk = self.payload[self.offset : self.offset + size]
                self.offset += len(chunk)
                return chunk

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        fake_file = FakeFile(data)
        with patch("haplohub_cli.core.checksum.open", return_value=fake_file) as mocked_open, patch(
            "haplohub_cli.core.checksum.CHUNK_SIZE", 4
        ):
            result = calculate_checksum("dummy/path")

        mocked_open.assert_called_once_with("dummy/path", "rb")
        self.assertGreaterEqual(len(fake_file.read_calls), 2)
        self.assertTrue(all(size == 4 for size in fake_file.read_calls))
        self.assertEqual(result, expected)
