
import ast
import operator
from typing import Any, Dict, List, Union, Callable

class Selector:
    """Helper to evaluate string expressions safely."""
    
    # Safe operators
    OPS = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.And: lambda x, y: x and y,
        ast.Or: lambda x, y: x or y,
    }

    @staticmethod
    def _eval(node, data):
        if isinstance(node, ast.Expression):
            return Selector._eval(node.body, data)
        elif isinstance(node, ast.BoolOp):
            # simple left-to-right evaluation for And/Or
            val = Selector._eval(node.values[0], data)
            for v in node.values[1:]:
                op = Selector.OPS[type(node.op)]
                val = op(val, Selector._eval(v, data))
            return val
        elif isinstance(node, ast.Compare):
            left = Selector._eval(node.left, data)
            for op, comparator in zip(node.ops, node.comparators):
                right = Selector._eval(comparator, data)
                if not Selector.OPS[type(op)](left, right):
                    return False
            return True
        elif isinstance(node, ast.Name):
            return data.get(node.id)
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Attribute):
            # nested access: item.prop
            val = Selector._eval(node.value, data)
            if val and isinstance(val, dict):
                return val.get(node.attr)
            return None
        elif isinstance(node, ast.Call):
            # string methods: .startswith, .endswith etc.
            func = node.func
            if isinstance(func, ast.Attribute):
                val = Selector._eval(func.value, data)
                if isinstance(val, str):
                    method = getattr(val, func.attr, None)
                    if method:
                        args = [Selector._eval(a, data) for a in node.args]
                        return method(*args)
            return False
        else:
            raise ValueError(f"Unsupported expression node: {type(node)}")

    @staticmethod
    def compile_condition(expression: str) -> Callable[[Any], bool]:
        """Compile a string expression into a callable."""
        tree = ast.parse(expression, mode='eval')
        def condition(item):
            try:
                return bool(Selector._eval(tree, item))
            except Exception:
                return False
        return condition

    @staticmethod
    def compile_selector(fields: Union[List[str], Dict[str, str]]) -> Callable[[Any], Dict]:
        """Compile field selection into a callable."""
        if isinstance(fields, list):
            def select(item):
                return {k: item.get(k) for k in fields if k in item}
            return select
        elif isinstance(fields, dict):
            # Dict mapping new_name -> old_name (or expression?)
            # Prompt said: 'new_name': 'old_name' 
            # It also mentioned full_name: 'first + " " + last'. 
            # For v0.8 MVP, let's stick to simple renaming + dot traversal.
            def select(item):
                res = {}
                for new_k, source in fields.items():
                    # Simple traversal helper
                    val = item
                    for p in source.split('.'):
                        if isinstance(val, dict):
                            val = val.get(p)
                        else:
                            val = None
                            break
                    res[new_k] = val
                return res
            return select
        else:
            return lambda x: x
