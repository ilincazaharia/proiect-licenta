import unittest
import sys

if __name__ == "__main__":
    print("Se ruleaza testele unitare pentru nivelurile corespunzatoare arhitecturii...\n")
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir="tests", pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
