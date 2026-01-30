import unittest
from ai_context_core.analyzer.metrics import calculate_maintenance_index


class TestMetricsAdvanced(unittest.TestCase):
    def test_calculate_maintenance_index_perfect(self):
        # Perfect score for very simple code
        # V=1, G=1, LOC=1 -> should be near 100
        score = calculate_maintenance_index(1.0, 1, 1)
        self.assertGreater(score, 90.0)
        self.assertLessEqual(score, 100.0)

    def test_calculate_maintenance_index_complex(self):
        # Lower score for complex code
        # V=1000, G=20, LOC=500
        score = calculate_maintenance_index(1000.0, 20, 500)
        self.assertLess(score, 50.0)
        self.assertGreaterEqual(score, 0.0)

    def test_calculate_maintenance_index_invalid(self):
        # Zero or negative values should return 100 as fallback (or at least not fail)
        self.assertEqual(calculate_maintenance_index(0, 0, 0), 100.0)
        self.assertEqual(calculate_maintenance_index(-1, 5, 10), 100.0)


if __name__ == "__main__":
    unittest.main()
