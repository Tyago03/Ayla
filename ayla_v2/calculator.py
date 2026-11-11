"""Arithmetic via a restricted AST and Decimal. Never eval/exec, names or Python IO."""
import ast
from decimal import Decimal, DecimalException, localcontext
from .errors import AppError


def calculate(expression: str) -> dict:
    if not isinstance(expression, str) or not 1 <= len(expression) <= 180:
        raise AppError('Use uma expressão aritmética de até 180 caracteres.', 400)
    expression = expression.strip().replace('^', '**')
    try:
        tree = ast.parse(expression, mode='eval')
        if len(list(ast.walk(tree))) > 70:
            raise ValueError('Expressão complexa demais.')

        def bounded(number):
            if not number.is_finite() or abs(number) > Decimal('1e100'):
                raise ValueError('Resultado fora dos limites de cálculo.')
            return number

        def visit(node):
            if isinstance(node, ast.Constant) and type(node.value) in (int, float):
                segment = ast.get_source_segment(expression, node)
                if not segment or len(segment) > 100:
                    raise ValueError('Número muito longo.')
                return bounded(Decimal(segment.replace('_', '')))
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
                n = visit(node.operand)
                return n if isinstance(node.op, ast.UAdd) else -n
            if isinstance(node, ast.BinOp):
                a, b = visit(node.left), visit(node.right)
                if isinstance(node.op, ast.Add): value = a + b
                elif isinstance(node.op, ast.Sub): value = a - b
                elif isinstance(node.op, ast.Mult): value = a * b
                elif isinstance(node.op, ast.Div): value = a / b
                elif isinstance(node.op, ast.FloorDiv): value = a // b
                elif isinstance(node.op, ast.Mod): value = a % b
                elif isinstance(node.op, ast.Pow):
                    if b != b.to_integral_value() or abs(b) > 100:
                        raise ValueError('Expoente precisa ser inteiro entre -100 e 100.')
                    value = a ** int(b)
                else: raise ValueError('Operador não permitido.')
                return bounded(value)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
                args = [visit(a) for a in node.args]
                if node.func.id == 'sqrt' and len(args) == 1: return bounded(args[0].sqrt())
                if node.func.id == 'abs' and len(args) == 1: return abs(args[0])
            raise ValueError('Use somente números, operadores aritméticos, sqrt e abs.')
        with localcontext() as ctx:
            ctx.prec = 28
            result = visit(tree.body)
        return {'expressao': expression, 'resultado': format(result, 'f'),
                'precisao': 'decimal, até 28 algarismos significativos; cálculos não exatos podem ser arredondados'}
    except (SyntaxError, ValueError, DecimalException, OverflowError, RecursionError) as exc:
        raise AppError('Cálculo inválido ou fora dos limites. Confira divisão por zero, parênteses e operadores.', 400) from exc
