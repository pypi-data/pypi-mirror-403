"""
Unit tests for the similarity module.
"""
import unittest
from unittest import TestCase

from string2string.similarity import (
    LCSubsequenceSimilarity,
    LCSubstringSimilarity,
    JaroSimilarity,
)


class SimilarityTestCase(TestCase):
    """Test cases for classical similarity metrics."""

    def test_lc_subsequence_similarity_identical_strings(self):
        """Test LCSubsequenceSimilarity with identical strings."""
        sim = LCSubsequenceSimilarity()

        # Identical strings should have similarity 1.0
        result = sim.compute("hello", "hello")
        self.assertEqual(result, 1.0)

        result = sim.compute("abc", "abc")
        self.assertEqual(result, 1.0)

    def test_lc_subsequence_similarity_different_strings(self):
        """Test LCSubsequenceSimilarity with different strings."""
        sim = LCSubsequenceSimilarity()

        # "abc" and "axbxc" share subsequence "abc" of length 3
        # max(3, 5) = 5, so similarity = 3/5 = 0.6
        result = sim.compute("abc", "axbxc")
        self.assertAlmostEqual(result, 0.6, places=5)

        # Completely different strings
        result = sim.compute("abc", "xyz")
        self.assertEqual(result, 0.0)

    def test_lc_subsequence_similarity_denominators(self):
        """Test LCSubsequenceSimilarity with different denominators."""
        sim = LCSubsequenceSimilarity()

        # Test 'max' denominator (default)
        result_max = sim.compute("abc", "ab", denominator='max')
        self.assertAlmostEqual(result_max, 2/3, places=5)

        # Test 'sum' denominator
        result_sum = sim.compute("abc", "ab", denominator='sum')
        self.assertAlmostEqual(result_sum, 2 * 2 / (3 + 2), places=5)

    def test_lc_subsequence_similarity_invalid_denominator(self):
        """Test LCSubsequenceSimilarity with invalid denominator."""
        sim = LCSubsequenceSimilarity()

        with self.assertRaises(ValueError):
            sim.compute("abc", "abc", denominator='invalid')

    def test_lc_substring_similarity_identical_strings(self):
        """Test LCSubstringSimilarity with identical strings."""
        sim = LCSubstringSimilarity()

        # Identical strings should have similarity 1.0
        result = sim.compute("hello", "hello")
        self.assertEqual(result, 1.0)

    def test_lc_substring_similarity_different_strings(self):
        """Test LCSubstringSimilarity with different strings."""
        sim = LCSubstringSimilarity()

        # "abc" and "xabcy" share substring "abc" of length 3
        # max(3, 5) = 5, so similarity = 3/5 = 0.6
        result = sim.compute("abc", "xabcy")
        self.assertAlmostEqual(result, 0.6, places=5)

        # Completely different strings
        result = sim.compute("abc", "xyz")
        self.assertEqual(result, 0.0)

    def test_lc_substring_similarity_partial_match(self):
        """Test LCSubstringSimilarity with partial matches."""
        sim = LCSubstringSimilarity()

        # "abcdef" and "xyzabc" share substring "abc" of length 3
        # max(6, 6) = 6, so similarity = 3/6 = 0.5
        result = sim.compute("abcdef", "xyzabc")
        self.assertAlmostEqual(result, 0.5, places=5)

    def test_lc_substring_similarity_denominators(self):
        """Test LCSubstringSimilarity with different denominators."""
        sim = LCSubstringSimilarity()

        # Test 'sum' denominator
        result_sum = sim.compute("abc", "ab", denominator='sum')
        self.assertAlmostEqual(result_sum, 2 * 2 / (3 + 2), places=5)

    def test_lc_substring_similarity_invalid_denominator(self):
        """Test LCSubstringSimilarity with invalid denominator."""
        sim = LCSubstringSimilarity()

        with self.assertRaises(ValueError):
            sim.compute("abc", "abc", denominator='invalid')

    def test_jaro_similarity_identical_strings(self):
        """Test JaroSimilarity with identical strings."""
        sim = JaroSimilarity()

        # Identical strings should have similarity 1.0
        result = sim.compute("hello", "hello")
        self.assertEqual(result, 1.0)

        result = sim.compute("MARTHA", "MARTHA")
        self.assertEqual(result, 1.0)

    def test_jaro_similarity_different_strings(self):
        """Test JaroSimilarity with different strings."""
        sim = JaroSimilarity()

        # Classic Jaro example: MARTHA vs MARHTA
        # Expected: approximately 0.944
        result = sim.compute("MARTHA", "MARHTA")
        self.assertGreater(result, 0.9)
        self.assertLess(result, 1.0)

    def test_jaro_similarity_no_match(self):
        """Test JaroSimilarity with completely different strings."""
        sim = JaroSimilarity()

        # Completely different strings should have low/zero similarity
        result = sim.compute("abc", "xyz")
        self.assertEqual(result, 0.0)

    def test_jaro_similarity_partial_match(self):
        """Test JaroSimilarity with partial matches."""
        sim = JaroSimilarity()

        # DWAYNE vs DUANE
        result = sim.compute("DWAYNE", "DUANE")
        self.assertGreater(result, 0.8)
        self.assertLess(result, 1.0)

    def test_jaro_similarity_single_char(self):
        """Test JaroSimilarity with single character strings."""
        sim = JaroSimilarity()

        result = sim.compute("a", "a")
        self.assertEqual(result, 1.0)

        result = sim.compute("a", "b")
        self.assertEqual(result, 0.0)

    def test_similarity_with_lists(self):
        """Test similarity metrics with list inputs."""
        lcs_sim = LCSubsequenceSimilarity()

        # Test with list of strings
        result = lcs_sim.compute(["hello", "world"], ["hello", "world"])
        self.assertEqual(result, 1.0)

        result = lcs_sim.compute(["a", "b", "c"], ["a", "x", "b", "x", "c"])
        self.assertAlmostEqual(result, 0.6, places=5)


if __name__ == '__main__':
    unittest.main()
