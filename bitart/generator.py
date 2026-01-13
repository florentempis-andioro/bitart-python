import random
from .function import Expression, Literal, Lookup, PlotFn

class FunctionMaker:
    def __init__(self, unary_rate=0.3, literal_rate=0.5, max_literal=24, depth=3):
        self.unary_rate = unary_rate
        self.literal_rate = literal_rate
        self.max_literal = max_literal
        self.depth = depth
        
        # Cache symbols for performance if needed, but not strictly necessary here
        self.bin_ops = list(Expression.BIN_OPS.keys())
        self.un_ops = list(Expression.UN_OPS.keys())

    def make(self, modulo=None):
        fn = self.make_func(self.depth)
        if modulo is not None:
             fn = Expression('%', fn, PlotFn.wrap(modulo))
        return fn

    def make_leaf(self, force_lookup):
        if force_lookup or random.random() < self.literal_rate:
            return Lookup(random.choice(['x', 'y']))
        return Literal(random.randint(1, self.max_literal))

    def make_func(self, depth, force_lookup=True):
        if depth == 0:
            return self.make_leaf(force_lookup)
        
        if random.random() < self.unary_rate:
            return self.make_unary(depth)
        
        return self.make_binary(depth)

    def make_unary(self, depth):
        op = random.choice(self.un_ops)
        arg = self.make_func(depth - 1)
        return Expression(op, arg)

    def make_binary(self, depth):
        op = random.choice(self.bin_ops)
        # One side must lookup variable to ensure function depends on x/y roughly
        # The Ruby code passes `true` for left and `false` for right to `make_func`
        # and then shuffles them.
        left = self.make_func(depth - 1, force_lookup=True)
        right = self.make_func(depth - 1, force_lookup=False)
        
        if random.random() < 0.5:
            left, right = right, left
            
        return Expression(op, left, right)
