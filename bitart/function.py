import operator
from abc import ABC, abstractmethod

class PlotFnError(RuntimeError):
    pass

class PFTypeError(PlotFnError):
    pass

def safe_div(a, b):
    # Ruby: return 1 if divisor == self (semi-graceful for 0/0)
    if b == 0:
        if a == 0:
            return 1
        return -1
    return a // b

def safe_mod(a, b):
    if b == 0:
        return 0
    return a % b

class PlotFn(ABC):
    @property
    def is_lookup(self): return False
    
    @property
    def is_literal(self): return False
    
    @property
    def is_binary(self): return False
    
    @property
    def is_unary(self): return False
    
    @property
    def is_expression(self): return False

    @abstractmethod
    def __str__(self): raise NotImplementedError
    
    @abstractmethod
    def __repr__(self): raise NotImplementedError
    
    @abstractmethod
    def __call__(self, context): raise NotImplementedError

    @classmethod
    def wrap(cls, obj):
        if isinstance(obj, PlotFn):
            return obj
        if isinstance(obj, int):
            return Literal(obj)
        if isinstance(obj, str):
            return Lookup(obj)
        raise PFTypeError(f"Unwrappable object '{obj}' (type {type(obj)})")

class Expression(PlotFn):
    BIN_OPS = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '&': operator.and_,
        '|': operator.or_,
        '^': operator.xor,
        '/': safe_div,
        '%': safe_mod,
    }
    
    UN_OPS = {
        '-@': operator.neg,
        '~': operator.inv,
    }

    def __init__(self, op_symbol, arg1, arg2=None):
        self.op_symbol = op_symbol
        self.binary = arg2 is not None
        self.lhs = self.wrap(arg1) if self.binary else None
        self.rhs = self.wrap(arg2) if self.binary else self.wrap(arg1)
        
        if self.binary:
            if op_symbol not in self.BIN_OPS:
                raise PlotFnError(f"Unknown binary operator '{op_symbol}'")
            self.op_func = self.BIN_OPS[op_symbol]
        else:
            if op_symbol not in self.UN_OPS:
                raise PlotFnError(f"Unknown unary operator '{op_symbol}'")
            self.op_func = self.UN_OPS[op_symbol]

    @property
    def is_binary(self): return self.binary
    
    @property
    def is_unary(self): return not self.binary
    
    @property
    def is_expression(self): return True

    def __repr__(self):
        args = [f"'{self.op_symbol}'"]
        if self.binary:
            args.append(repr(self.lhs))
        args.append(repr(self.rhs))
        return f"Expression({', '.join(args)})"

    def __str__(self):
        op_s = self.op_symbol.replace('@', '')
        if self.binary:
            return f"{self._bracket(self.lhs)} {op_s} {self._bracket(self.rhs)}"
        return f"{op_s}{self._bracket(self.rhs)}"

    def _bracket(self, pf):
        if pf.is_binary or pf.is_unary:
            return f"({pf})"
        return str(pf)

    def __call__(self, context):
        try:
            val_rhs = self.rhs(context)
            if self.binary:
                val_lhs = self.lhs(context)
                return self.op_func(val_lhs, val_rhs)
            return self.op_func(val_rhs)
        except Exception:
             # In case of any overflow or weird error, usually fallback to 0 or similar is safer for art generation
             # but Ruby version doesn't catch generic errors, only implements safe div/mod.
             # We will let it propagate or standard handling. 
             # Python integers have arbitrary precision so overflow isn't an issue like in C.
             raise

class Literal(PlotFn):
    def __init__(self, value):
        self.value = value
        
    @property
    def is_literal(self): return True
    
    def __str__(self): return str(self.value)
    
    def __repr__(self): return f"Literal({self.value})"
    
    def __call__(self, context):
        return self.value

class Lookup(PlotFn):
    def __init__(self, name):
        self.name = name
        
    @property
    def is_lookup(self): return True
    
    def __str__(self): return self.name
    
    def __repr__(self): return f"Lookup('{self.name}')"
    
    def __call__(self, context):
        return context[self.name]
