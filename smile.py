# TYPES
NUMBER = "NUMBER"
SYMBOL = "SYMBOL"
LPAREN = "LPAREN"
RPAREN = "RPAREN"

numbers = "1234567890"

# LEXER


class Token:
    def __init__(self, ty, val):
        self.type = ty
        self.val = val

    def __repr__(self):
        return "{type} - {val}".format(type=self.type, val=self.val)


class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0

    def create_tokens(self):
        tokens = []
        while self.pos < len(self.text):
            curr = self.text[self.pos]
            if curr == " ":
                self.pos += 1
            elif curr in numbers:
                tokens.append(Token(NUMBER, self.make_number()))
            elif curr == "(":
                tokens.append(Token(LPAREN, "("))
                self.pos += 1
            elif curr == ")":
                tokens.append(Token(RPAREN, ")"))
                self.pos += 1
            else:
                sym = self.make_symbol()
                tokens.append(Token(SYMBOL, sym))
        return tokens

    def make_symbol(self):
        sym = ""
        while self.pos < len(self.text) and not self.text[self.pos] in " ()":
            curr = self.text[self.pos]
            sym += curr
            self.pos += 1
        return sym

    def make_number(self):
        num = ""
        deci = False
        while self.pos < len(self.text) and not self.text[self.pos] in " ()":
            curr = self.text[self.pos]
            if not curr in numbers + ".":
                raise SmileError("bad number :^(")
            elif curr == ".":
                if deci:
                    raise SmileError("too many dots :^(")
                deci = True
            num += curr
            self.pos += 1
        return num


# PARSER


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def parse(self):  # TODO make better
        operands, ops = [], []
        paren_count = 0
        expected = "OPERAND"  # operand or operator
        while self.pos < len(self.tokens):
            curr = self.tokens[self.pos]
            if curr.type == RPAREN:
                if paren_count <= 0:
                    raise SmileError("misplaced parentheses :^(")
                while ops[-1].type != LPAREN:
                    validate_parse(operands)
                    right, left = operands.pop(), operands.pop()
                    pop_op = ops.pop()
                    operands.append(Node(pop_op, left, right))
                ops.pop()
                paren_count -= 1
            elif curr.type == LPAREN:
                ops.append(curr)
                paren_count += 1
            elif expected == "OPERAND":
                operands.append(Node(curr))
            elif expected == "OPERATOR":
                if curr.type == NUMBER:
                    raise SmileError("number is not an operator :^(")
                if ops and ops[-1].type != LPAREN:
                    validate_parse(operands)
                    right, left = operands.pop(), operands.pop()
                    pop_op = ops.pop()
                    operands.append(Node(pop_op, left, right))
                ops.append(curr)
            if not curr.type in [LPAREN, RPAREN]:
                expected = "OPERAND" if expected == "OPERATOR" else "OPERATOR"
            self.pos += 1
        if paren_count != 0:
            raise SmileError("misplaced parentheses :^(")
        if ops:
            validate_parse(operands)
            right, left = operands.pop(), operands.pop()
            pop_op = ops.pop()
            operands.append(Node(pop_op, left, right))
        if len(operands) > 1:
            raise SmileError("syntax error :^(")
        return operands[0] if len(operands) == 1 else None


class Node:
    def __init__(self, val, left=None, right=None):
        if type(left) != type(right):  # left, right both either None or Node
            raise SmileError("malformed nodes :^(")
        self.left = left
        self.right = right
        self.val = val

    def is_leaf(self):
        return self.left is None and self.right is None

    def __repr__(self):
        return (
            "({left} << {val} >> {right})".format(
                left=self.left, val=self.val, right=self.right
            )
            if self.left
            else "({val})".format(val=self.val)
        )


# INTERPRETER


class Interpreter:
    def explore(self, node):
        print("Found:", node.val)
        if node.left and node.right:
            self.explore(node.left)
            self.explore(node.right)

    def eval_node(self, node, env):
        if node is None:
            return
        elif node.is_leaf():
            # TODO lookup variable names
            if node.val.type == SYMBOL:
                return env.lookup(self.eval_token(node.val))
            return self.eval_token(node.val)

        operator = env.lookup(self.eval_token(node.val))
        validate_operator(operator)
        if operator.name == "bind":
            validate_bind(node)
            left = self.eval_token(node.left.val)
            right = self.eval_node(node.right, env)
        else:
            operator = env.lookup(self.eval_token(node.val))
            left = self.eval_node(node.left, env)
            right = self.eval_node(node.right, env)
        if isinstance(operator, SpecialOp):
            return operator(left, right, env)
        return operator(left, right)

    def eval_token(self, token):
        return float(token.val) if token.type == NUMBER else token.val


# FRAMES


def create_global_frame():
    frame = Frame()
    for op in builtins:
        frame.define(op[0], Operator(op[0], op[1]))
    for op in specials:
        frame.define(op[0], SpecialOp(op[0], op[1]))
    return frame


class Frame:
    def __init__(self, parent=None):  # frame with no parent is global
        self.bindings = {}
        self.parent = parent

    def define(self, id, val):
        self.bindings[id] = val

    def lookup(self, id):
        if id in self.bindings:
            return self.bindings[id]
        elif not self.parent is None:
            return self.parent.lookup(id)
        raise SmileError("unknown identifier :^(")


class Operator:
    def __init__(self, name, func):
        self.name = name
        self.func = func

    def __call__(self, *args):
        return self.func(args[0], args[1])


class SpecialOp(Operator):
    def __call__(self, *args):
        return self.func(args[0], args[1], args[2])  # pass in frame


# BUILTINS

builtins = []
specials = []


def builtin(name):
    def add(func):
        builtins.append([name, func])
        return func

    return add


def special(name):
    def add(func):
        specials.append([name, func])
        return func

    return add


@builtin("add")
def add(a, b):
    return a + b


@builtin("sub")
def sub(a, b):
    return a - b


@builtin("mul")
def mul(a, b):
    return a * b


@builtin("div")
def div(a, b):
    if b == 0:
        raise SmileError("zero division error :^(")
    return a / b


@builtin("pow")
def pow(a, b):
    return a ** b


@special("bind")
def bind(id, val, env):
    env.define(id, val)
    return val


# ERRORS


def validate_parse(operands):
    if len(operands) < 2:
        raise SmileError("few operands :^(")


def validate_operator(operator):
    if not isinstance(operator, Operator) and not isinstance(operator, SpecialOp):
        raise SmileError("not operator :^(")


def validate_bind(node):
    if not node.left.is_leaf() or node.left.val.type != SYMBOL:
        raise SmileError("wrong bind :^(")


class SmileError(Exception):
    pass