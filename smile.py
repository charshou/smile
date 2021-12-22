# TYPES
NUMBER = "NUMBER"
STRING = "STRING"
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
            elif curr in '"':
                tokens.append(Token(STRING, self.make_string()))
            elif curr in numbers:
                tokens.append(Token(NUMBER, self.make_number()))
            elif curr == "(":
                tokens.append(Token(LPAREN, "("))
                self.pos += 1
            elif curr == ")":
                tokens.append(Token(RPAREN, ")"))
                self.pos += 1
            elif curr == ";":  # TODO add multiline
                pass
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

    def make_string(self):
        string = ""
        self.pos += 1
        if not '"' in self.text[self.pos :]:
            raise SmileError('cannot find " :^(')
        while self.pos < len(self.text) and self.text[self.pos] != '"':
            string += self.text[self.pos]
            self.pos += 1
        self.pos += 1
        return string


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
                is_nil = True
                while ops[-1].type != LPAREN:
                    is_nil = False
                    validate_parse(operands)
                    right, left = operands.pop(), operands.pop()
                    pop_op = ops.pop()
                    operands.append(Node(pop_op, left, right))
                ops.pop()
                if is_nil:
                    if expected == "OPERATOR":
                        raise SmileError("syntax error :^(")
                    expected = "OPERATOR"
                    operands.append(Node(Token(NUMBER, "0")))
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

    def new_parser(self): # work in progress
        # just get left mid and right nodes with nextnode
        left, middle, right = next_node(), next_node(), next_node()
        return Node(middle.val, left, right)

    def next_node(self):
        if not self.pos < len(self.tokens):
            raise SmileError("no more tokens :^(")
        curr = self.tokens[self.pos]
        if curr.type == RPAREN:
            raise SmileError("invalid token :^(")
        elif curr.type == LPAREN:
            pass #todo
        else:
            pass #todo
            
        
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
            if node.val.type == SYMBOL:
                return env.lookup(self.eval_token(node.val))
            return self.eval_token(node.val)

        operator = env.lookup(self.eval_token(node.val))
        validate_operator(operator)
        if operator.name == "bind":
            left, right = self.eval_bind_node(node, env)
        elif operator.name == "if":
            left, right = self.eval_if_node(node, env)
        elif operator.name == "function":
            left, right = self.eval_function_node(node, env)
        else:
            left = self.eval_node(node.left, env)
            right = self.eval_node(node.right, env)
        if issubclass(type(operator), SpecialOp):
            return operator(left, right, env)
        return operator(left, right)

    def eval_bind_node(self, node, env):
        validate_bind(node)
        left = self.eval_token(node.left.val)
        right = self.eval_node(node.right, env)
        return left, right

    def eval_if_node(self, node, env):
        right = self.eval_node(node.right, env)
        left = 0
        if right:
            left = self.eval_node(node.left, env)
        return left, right

    def eval_function_node(self, node, env):  # TODO make clearer
        left_op = env.lookup(self.eval_token(node.left.val))
        validate_operator(left_op)
        if not left_op.name == "link":
            raise SmileError("left side not list :^(")
        left_node, right_node = node.left.left, node.left.right
        if not (
            left_node.is_leaf()
            and right_node.is_leaf()
            and left_node.val.type == SYMBOL
            and right_node.val.type == SYMBOL
        ):
            raise SmileError("bad parameters in function :^(")
        left = Link(self.eval_token(right_node.val), self.eval_token(left_node.val))
        right = node.right
        return left, right

    def eval_token(self, token):
        if token.type == NUMBER:  # float or int
            return float(token.val) if "." in token.val else int(token.val)
        return token.val


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


# OPERATORS


class Operator:
    def __init__(self, name, func):
        self.name = name
        self.func = func

    def __call__(self, *args):
        return self.func(args[0], args[1])


class SpecialOp(Operator):
    def __call__(self, *args):
        return self.func(args[0], args[1], args[2])  # pass in frame


class UserDefinedOp(
    SpecialOp
):  # bind parameters to local frame and eval node passed as func
    def __init__(self, name, func, params):  # params is list
        self.params = [params.get(0), params.get(1)]
        SpecialOp.__init__(self, name, func)

    def __call__(self, *args):  # func is a node
        env = args[2]
        child = Frame(env)
        child.define(self.params[0], args[0])
        child.define(self.params[1], args[1])
        temp = Interpreter()
        return temp.eval_node(self.func, child)


# LISTS/LINK


class Link:
    empty = None

    def __init__(self, val, prev=empty):  # reverse linked list
        if isinstance(prev, Link):
            self.prev = prev
        elif prev is Link.empty:
            self.prev = Link.empty
        else:
            self.prev = Link(prev)
        self.val = val

    def get(self, i):
        if i >= len(self):
            return None
        index = len(self) - 1 - i
        while index > 0:
            self = self.prev
            index -= 1
        return self.val

    def __repr__(self):
        string = ")"
        while not self.prev is Link.empty:
            string = " " + str(self.val) + string
            self = self.prev
        return "(" + str(self.val) + string

    def __len__(self):
        if self.prev is Link.empty:
            return 1
        return 1 + len(self.prev)


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


@builtin("cat")
def cat(a, b):
    if not isinstance(a, str) or not isinstance(b, str):
        raise SmileError("cat only supports strs :^(")
    return a + b


@builtin("add")
def add(a, b):
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise SmileError("add only supports ints :^(")
    return a + b


@builtin("sub")
def sub(a, b):
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise SmileError("sub only supports ints :^(")
    return a - b


@builtin("mul")
def mul(a, b):
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise SmileError("mul only supports ints :^(")
    return a * b


@builtin("div")
def div(a, b):
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise SmileError("div only supports ints :^(")
    if b == 0:
        raise SmileError("zero division error :^(")
    return a / b


@builtin("pow")
def pow(a, b):
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise SmileError("pow only supports ints :^(")
    return a ** b


@builtin("greater")
def greater(a, b):
    return int(a > b)


@builtin("lesser")
def lesser(a, b):
    return int(a < b)


@builtin("equal")
def equal(a, b):
    return int(a == b)


@builtin("and")
def and_op(a, b):
    return int(a and b)


@builtin("or")
def or_op(a, b):
    return int(a or b)


@special("if")  # TODO add else condition with links
def if_op(a, b, env):  # return a if b else 0
    if b:
        return a
    return 0


@special("bind")
def bind(id, val, env):
    env.define(id, val)
    return val


@special("link")
def link(prev, val, env):
    return Link(val, prev)


@special("function")
def function_op(
    operands, body, env
):  # TODO fix parsing issue and catch recursion error
    return UserDefinedOp("u_function", body, operands)


@special("get")
def get(lst, index, env):  # TODO add get from list
    pass


# ERRORS


def validate_parse(operands):
    if len(operands) < 2:
        raise SmileError("few operands :^(")


def validate_operator(operator):
    if not isinstance(operator, Operator) and not isinstance(operator, SpecialOp):
        raise SmileError("{} not operator :^(".format(operator))


def validate_bind(node):
    if not node.left.is_leaf() or node.left.val.type != SYMBOL:
        raise SmileError("wrong bind :^(")


class SmileError(Exception):
    pass