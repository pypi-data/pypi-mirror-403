"""
Unit tests for the ExactMatch metric.
"""
import unittest
from unittest import TestCase

from string2string.metrics import ExactMatch


class ExactMatchTestCase(TestCase):
    """Test cases for the ExactMatch metric."""

    def test_exact_match_all_correct(self):
        """Test ExactMatch when all predictions are correct."""
        em = ExactMatch()

        predictions = ["hello", "world", "test"]
        references = [["hello"], ["world"], ["test"]]

        result = em.compute(predictions, references)

        self.assertEqual(result['score'], 1.0)
        self.assertEqual(result['num_correct'], 3)
        self.assertEqual(result['num_total'], 3)

    def test_exact_match_none_correct(self):
        """Test ExactMatch when no predictions are correct."""
        em = ExactMatch()

        predictions = ["hello", "world", "test"]
        references = [["goodbye"], ["universe"], ["exam"]]

        result = em.compute(predictions, references)

        self.assertEqual(result['score'], 0.0)
        self.assertEqual(result['num_correct'], 0)
        self.assertEqual(result['num_total'], 3)

    def test_exact_match_partial_correct(self):
        """Test ExactMatch with some correct predictions."""
        em = ExactMatch()

        predictions = ["hello", "world", "test"]
        references = [["hello"], ["universe"], ["test"]]

        result = em.compute(predictions, references)

        self.assertAlmostEqual(result['score'], 2/3, places=5)
        self.assertEqual(result['num_correct'], 2)
        self.assertEqual(result['num_total'], 3)

    def test_exact_match_multiple_references(self):
        """Test ExactMatch with multiple acceptable references."""
        em = ExactMatch()

        predictions = ["hello", "hi"]
        references = [["hello", "hi", "hey"], ["hi", "hello"]]

        result = em.compute(predictions, references)

        self.assertEqual(result['score'], 1.0)
        self.assertEqual(result['num_correct'], 2)

    def test_exact_match_case_insensitive(self):
        """Test ExactMatch with case insensitivity (default)."""
        em = ExactMatch()

        predictions = ["HELLO", "World", "TEST"]
        references = [["hello"], ["world"], ["test"]]

        result = em.compute(predictions, references, lowercase=True)

        self.assertEqual(result['score'], 1.0)

    def test_exact_match_case_sensitive(self):
        """Test ExactMatch with case sensitivity."""
        em = ExactMatch()

        predictions = ["HELLO", "world", "TEST"]
        references = [["hello"], ["world"], ["test"]]

        result = em.compute(predictions, references, lowercase=False)

        self.assertAlmostEqual(result['score'], 1/3, places=5)
        self.assertEqual(result['num_correct'], 1)

    def test_exact_match_empty_raises_error(self):
        """Test that empty predictions/references raises assertion error."""
        em = ExactMatch()

        with self.assertRaises(AssertionError):
            em.compute([], [])

    def test_exact_match_length_mismatch_raises_error(self):
        """Test that mismatched lengths raise assertion error."""
        em = ExactMatch()

        predictions = ["hello", "world"]
        references = [["hello"]]

        with self.assertRaises(AssertionError):
            em.compute(predictions, references)

    def test_exact_match_single_prediction(self):
        """Test ExactMatch with single prediction."""
        em = ExactMatch()

        predictions = ["hello"]
        references = [["hello", "hi"]]

        result = em.compute(predictions, references)

        self.assertEqual(result['score'], 1.0)
        self.assertEqual(result['num_correct'], 1)
        self.assertEqual(result['num_total'], 1)


if __name__ == '__main__':
    unittest.main()
