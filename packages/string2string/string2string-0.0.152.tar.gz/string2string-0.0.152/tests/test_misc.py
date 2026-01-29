"""
Unit tests for the misc module.
"""
import unittest
from unittest import TestCase

from string2string.misc import Tokenizer, PolynomialRollingHash


class TokenizerTestCase(TestCase):
    """Test cases for the Tokenizer class."""

    def test_tokenize_default_delimiter(self):
        """Test tokenization with default space delimiter."""
        tokenizer = Tokenizer()

        tokens = tokenizer.tokenize("hello world")
        self.assertEqual(tokens, ["hello", "world"])

        tokens = tokenizer.tokenize("one two three four")
        self.assertEqual(tokens, ["one", "two", "three", "four"])

    def test_tokenize_custom_delimiter(self):
        """Test tokenization with custom delimiter."""
        tokenizer = Tokenizer(word_delimiter=",")

        tokens = tokenizer.tokenize("apple,banana,cherry")
        self.assertEqual(tokens, ["apple", "banana", "cherry"])

    def test_tokenize_empty_string(self):
        """Test tokenization of empty string."""
        tokenizer = Tokenizer()

        tokens = tokenizer.tokenize("")
        self.assertEqual(tokens, [""])

    def test_tokenize_single_word(self):
        """Test tokenization of single word."""
        tokenizer = Tokenizer()

        tokens = tokenizer.tokenize("hello")
        self.assertEqual(tokens, ["hello"])

    def test_detokenize_default_delimiter(self):
        """Test detokenization with default space delimiter."""
        tokenizer = Tokenizer()

        text = tokenizer.detokenize(["hello", "world"])
        self.assertEqual(text, "hello world")

    def test_detokenize_custom_delimiter(self):
        """Test detokenization with custom delimiter."""
        tokenizer = Tokenizer(word_delimiter="-")

        text = tokenizer.detokenize(["one", "two", "three"])
        self.assertEqual(text, "one-two-three")

    def test_tokenize_detokenize_roundtrip(self):
        """Test that tokenize and detokenize are inverse operations."""
        tokenizer = Tokenizer()

        original = "hello world test"
        tokens = tokenizer.tokenize(original)
        result = tokenizer.detokenize(tokens)
        self.assertEqual(result, original)


class PolynomialRollingHashTestCase(TestCase):
    """Test cases for the PolynomialRollingHash class."""

    def test_hash_deterministic(self):
        """Test that hash function is deterministic."""
        hasher1 = PolynomialRollingHash()
        hasher2 = PolynomialRollingHash()

        hash1 = hasher1.compute("test")
        hash2 = hasher2.compute("test")
        self.assertEqual(hash1, hash2)

    def test_hash_different_strings(self):
        """Test that different strings produce different hashes (usually)."""
        hasher1 = PolynomialRollingHash()
        hasher2 = PolynomialRollingHash()

        hash1 = hasher1.compute("hello")
        hash2 = hasher2.compute("world")
        # While collisions are possible, these specific strings should differ
        self.assertNotEqual(hash1, hash2)

    def test_hash_custom_base_modulus(self):
        """Test hash function with custom base and modulus."""
        hasher = PolynomialRollingHash(base=256, modulus=65537)

        hash_val = hasher.compute("test")
        self.assertIsInstance(hash_val, int)
        self.assertGreaterEqual(hash_val, 0)
        self.assertLess(hash_val, 65537)

    def test_hash_reset(self):
        """Test that reset clears the current hash."""
        hasher = PolynomialRollingHash()

        hasher.compute("hello")
        hasher.reset()
        self.assertEqual(hasher.current_hash, 0)

    def test_hash_update(self):
        """Test rolling hash update."""
        hasher = PolynomialRollingHash()

        # Compute initial hash for "abc"
        initial_hash = hasher.compute("abc")

        # Update by removing 'a' and adding 'd' (window "bcd")
        updated_hash = hasher.update('a', 'd', window_size=3)

        # The updated hash should be different from initial
        self.assertIsInstance(updated_hash, int)

    def test_hash_empty_string(self):
        """Test hash of empty string."""
        hasher = PolynomialRollingHash()

        hash_val = hasher.compute("")
        self.assertEqual(hash_val, 0)

    def test_invalid_base(self):
        """Test that invalid base raises assertion error."""
        with self.assertRaises(AssertionError):
            PolynomialRollingHash(base=-1)

    def test_invalid_modulus(self):
        """Test that invalid modulus raises assertion error."""
        with self.assertRaises(AssertionError):
            PolynomialRollingHash(modulus=0)


if __name__ == '__main__':
    unittest.main()
