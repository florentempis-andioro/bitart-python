import ast
from .function import Expression, Literal, Lookup

class EquationParser:
    def parse(self, equation_str):
        # Remove "f(x,y) =" prefix if present
        if "=" in equation_str:
            _, equation_str = equation_str.split("=", 1)
        
        equation_str = equation_str.strip()
        tree = ast.parse(equation_str, mode='eval')
        return self._transform(tree.body)

    def _transform(self, node):
        if isinstance(node, ast.BinOp):
            return self._transform_binop(node)
        elif isinstance(node, ast.UnaryOp):
            return self._transform_unaryop(node)
        elif isinstance(node, ast.Name):
            return self._transform_name(node)
        elif isinstance(node, ast.Constant): # Python 3.8+
            return self._transform_constant(node)
        elif isinstance(node, ast.Num): # Python < 3.8 fallback
            return Literal(node.n)
        else:
            raise ValueError(f"Unsupported syntax: {node}")

    def _transform_binop(self, node):
        op_map = {
            ast.Add: '+',
            ast.Sub: '-',
            ast.Mult: '*',
            ast.Div: '/',
            ast.FloorDiv: '/', # Treat // as / for bitart context if user types it, or normal /
            ast.Mod: '%',
            ast.BitOr: '|',
            ast.BitXor: '^',
            ast.BitAnd: '&',
        }
        
        op_type = type(node.op)
        if op_type not in op_map:
            raise ValueError(f"Unsupported binary operator: {op_type}")
            
        op_sym = op_map[op_type]
        left = self._transform(node.left)
        right = self._transform(node.right)
        
        return Expression(op_sym, left, right)

    def _transform_unaryop(self, node):
        op_map = {
            ast.USub: '-@',
            ast.Invert: '~',
        }
        
        op_type = type(node.op)
        if op_type not in op_map:
            raise ValueError(f"Unsupported unary operator: {op_type}")
            
        op_sym = op_map[op_type]
        operand = self._transform(node.operand)
        return Expression(op_sym, operand)

    def _transform_name(self, node):
        if node.id not in ('x', 'y'):
            raise ValueError(f"Unknown variable: {node.id}. Only 'x' and 'y' allowed.")
        return Lookup(node.id)

    def _transform_constant(self, node):
        if isinstance(node.value, int):
            return Literal(node.value)
        raise ValueError(f"Unsupported constant type: {type(node.value)}")
