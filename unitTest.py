import unittest
import test_noop.py
import test_rsSync.py

loader = unittest.TestLoader

suite = loader.loadTestsFromModule(test_noop)
suite.addTests(loader.loadTestsFromModule(test_rsSync))

runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
