import unittest
from humanbytes.humanbytes import humanbytes

class TestHumanBytes(unittest.TestCase):
    def test_decimal(self):
        self.assertEqual(humanbytes(0), "0 B")
        self.assertEqual(humanbytes(999), "999 B")
        self.assertEqual(humanbytes(1000), "1.00 KB")
        self.assertEqual(humanbytes(1536), "1.54 KB")
        self.assertEqual(humanbytes(10**6), "1.00 MB")
        self.assertEqual(humanbytes(10**9), "1.00 GB")

    def test_binary(self):
        self.assertEqual(humanbytes(0, binary=True), "0 B")
        self.assertEqual(humanbytes(1023, binary=True), "1023 B")
        self.assertEqual(humanbytes(1024, binary=True), "1.00 KiB")
        self.assertEqual(humanbytes(1536, binary=True), "1.50 KiB")
        self.assertEqual(humanbytes(2**20, binary=True), "1.00 MiB")
        self.assertEqual(humanbytes(2**30, binary=True), "1.00 GiB")

if __name__ == "__main__":
    unittest.main()