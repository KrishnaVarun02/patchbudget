"""Bounded execution of trusted benchmark mutations; NOT a security sandbox."""
import ast
import copy
import hashlib
import sys

class StepLimit(Exception): pass

def evaluate(source, name, args, limit=20000):
    namespace = {}
    ticks = 0
    filename = '<candidate>'
    def trace(frame, event, arg):
        nonlocal ticks
        if event == 'line' and frame.f_code.co_filename == filename:
            ticks += 1
            if ticks > limit: raise StepLimit('line event budget exhausted')
        return trace
    previous = sys.gettrace()
    try:
        exec(compile(source, filename, 'exec'), namespace)
        sys.settrace(trace)
        result = namespace[name](*copy.deepcopy(args))
        return {'ok': True, 'value': result, 'steps': ticks}
    except Exception as exc:
        return {'ok': False, 'error': type(exc).__name__, 'steps': ticks}
    finally:
        sys.settrace(previous)

def canonical(source):
    tree = ast.parse(source)
    # Strip descriptive string expressions; retain imports and actual definitions.
    tree.body = [n for n in tree.body if not isinstance(n, ast.Expr)
                 or not isinstance(n.value, ast.Constant) or not isinstance(n.value.value, str)]
    return ast.unparse(tree) + '\n'

def mutants(source, maximum=40):
    tree = ast.parse(canonical(source))
    proposals = []
    compare = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE,
               ast.GtE: ast.Gt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}
    binary = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Add,
              ast.FloorDiv: ast.Mult, ast.Mod: ast.FloorDiv,
              ast.BitAnd: ast.BitXor, ast.BitXor: ast.BitAnd}
    for index, node in enumerate(ast.walk(tree)):
        replacements = []
        if isinstance(node, ast.Constant) and type(node.value) is int:
            replacements = [('value', node.value-1), ('value', node.value+1)]
        elif isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in compare:
            replacements = [('ops', [compare[type(node.ops[0])]()] )]
        elif isinstance(node, (ast.BinOp, ast.AugAssign)) and type(node.op) in binary:
            replacements = [('op', binary[type(node.op)]())]
        elif isinstance(node, ast.BoolOp):
            replacements = [('op', ast.Or() if isinstance(node.op, ast.And) else ast.And())]
        for field, replacement in replacements:
            altered = copy.deepcopy(tree)
            target = list(ast.walk(altered))[index]
            setattr(target, field, replacement)
            altered = ast.fix_missing_locations(altered)
            try:
                candidate = ast.unparse(altered) + '\n'
                compile(candidate, '<candidate>', 'exec')
                digest = hashlib.sha256(candidate.encode()).hexdigest()
                proposals.append((digest, candidate, f'{type(node).__name__}:{getattr(node,"lineno",0)}:{field}:{ast.dump(replacement) if isinstance(replacement,ast.AST) else repr(replacement)}'))
            except (SyntaxError, ValueError):
                raise RuntimeError('Unexpected invalid grammar mutation')
    unique = {p[0]: p for p in proposals}
    return [unique[k] for k in sorted(unique)[:maximum]]
