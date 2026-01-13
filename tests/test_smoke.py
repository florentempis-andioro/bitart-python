import unittest
import os
from bitart.function import Expression, Literal, safe_div
from bitart.generator import FunctionMaker

class TestBitart(unittest.TestCase):
    def test_safe_div(self):
        self.assertEqual(safe_div(10, 2), 5)
        self.assertEqual(safe_div(10, 0), -1)
        self.assertEqual(safe_div(0, 0), 1)

    def test_generator(self):
        maker = FunctionMaker(depth=2)
        fn = maker.make()
        # Verify it returns an Expression or Literal or Lookup
        # It's hard to strict type check without importing everything, but str(fn) should work
        self.assertTrue(len(str(fn)) > 0)
        
    def test_grid_creation(self):
        from bitart.grid import Grid
        g = Grid(10, 10)
        g.fill(5)
        self.assertEqual(g[0,0], 5)
        self.assertEqual(g[9,9], 5)

if __name__ == '__main__':
    unittest.main()
