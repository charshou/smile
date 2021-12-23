from constants import *
from reader_objects import Node, Token
from objects import Link

# LEXER

class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0

    def create_tokens(self):
        tokens = []
        while self.pos < len(self.text):
            curr = self.text[self.pos]
            if curr in " \t\n":
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
            else:
                sym = self.make_symbol()
                tokens.append(Token(SYMBOL, sym))
        return tokens

    def make_symbol(self):
        sym = ""
        while self.pos < len(self.text) and not self.text[self.pos] in " ()\t\n":
            curr = self.text[self.pos]
            sym += curr
            self.pos += 1
        return sym

    def make_number(self):
        num = ""
        deci = False
        while self.pos < len(self.text) and not self.text[self.pos] in " ()\t\n":
            curr = self.text[self.pos]
            if not curr in numbers + ".":
                raise SmileError("bad number")
            elif curr == ".":
                if deci:
                    raise SmileError("too many dots")
                deci = True
            num += curr
            self.pos += 1
        return num

    def make_string(self):
        string = ""
        self.pos += 1
        if not '"' in self.text[self.pos :]:
            raise SmileError('cannot find "')
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

    def parse(self) -> Node: # work in progress
        # just get left mid and right nodes with nextnode
        root = self.next_node()
        while self.pos < len(self.tokens): # more tokens
            operator, second = self.next_operator(), self.next_node()
            root = Node(operator, root, second)
        return root
        

    def next_node(self) -> Node:
        if not self.pos < len(self.tokens):
            raise SmileError("no more tokens")
        curr = self.tokens[self.pos]
        if curr.type == RPAREN:
            raise SmileError("invalid token")
        elif curr.type == LPAREN:
            self.pos += 1
            parens = 1
            sub_tokens = []
            while parens > 0 and self.pos < len(self.tokens):
                next_token = self.tokens[self.pos]
                if next_token.type == RPAREN:
                    parens -= 1
                elif next_token.type == LPAREN:
                    parens += 1
                sub_tokens.append(next_token)
                self.pos += 1
            if parens == 0:
                sub_parser = Parser(sub_tokens[:-1]) # everything but last extra rparen
                return sub_parser.parse()
            raise SmileError("missing parens")
        else:
            self.pos += 1
            return Node(curr)
    
    def next_operator(self) -> Token:
        if not self.pos < len(self.tokens):
            raise SmileError("no more tokens")
        curr = self.tokens[self.pos]
        if not curr.type == RPAREN and not curr.type == LPAREN: # yay simple token
            self.pos += 1
            return curr
        else: # not simple token (node)
            operator_node = self.next_node()
            return Token(UNRESOLVED, operator_node) # hope it resolves to a valid operator


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

        if self.eval_token_type(node.val) == SYMBOL:
            operator = env.lookup(self.eval_token(node.val))
        elif self.eval_token_type(node.val) == UNRESOLVED:
            operator = self.eval_node(self.eval_token(node.val), env)
        else:
            raise SmileError(f"{self.eval_token_type(node.val)} can not be evaluated to a function")
        
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
            raise SmileError("left side not list")
        left_node, right_node = node.left.left, node.left.right
        if not (
            left_node.is_leaf()
            and right_node.is_leaf()
            and left_node.val.type == SYMBOL
            and right_node.val.type == SYMBOL
        ):
            raise SmileError("bad parameters in function")
        left = Link(self.eval_token(right_node.val), self.eval_token(left_node.val))
        right = node.right
        return left, right

    def eval_token(self, token):
        if token.type == NUMBER:  # float or int
            return float(token.val) if "." in token.val else int(token.val)
        return token.val
    
    def eval_token_type(self, token):
        return token.type


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
        raise SmileError("unknown identifier")

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
    def __init__(self, name: str, func, params):  # params is list
        self.params = [params.get(0), params.get(1)]
        SpecialOp.__init__(self, name, func)

    def __call__(self, *args):  # func is a node
        env = args[2]
        child = Frame(env)
        child.define(self.params[0], args[0])
        child.define(self.params[1], args[1])
        temp = Interpreter()
        return temp.eval_node(self.func, child)


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
        raise SmileError("cat only supports strs")
    return a + b


@builtin("add")
def add(a, b):
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise SmileError("add only supports ints")
    return a + b


@builtin("sub")
def sub(a, b):
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise SmileError("sub only supports ints")
    return a - b


@builtin("mul")
def mul(a, b):
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise SmileError("mul only supports ints")
    return a * b


@builtin("div")
def div(a, b):
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise SmileError("div only supports ints")
    if b == 0:
        raise SmileError("zero division error")
    return a / b


@builtin("pow")
def pow(a, b):
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise SmileError("pow only supports ints")
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


@builtin("if") 
def if_op(a, b):  # return a if b else 0
    if b:
        return a
    return 0


@builtin("link")
def link(prev, val): # repurpose into expression linker
    return Link(val, prev)


@builtin("function")
def function_op(
    operands, body
):  # TODO fix parsing issue and catch recursion error
    return UserDefinedOp("u_function", body, operands)


@special("bind")
def bind(id, val, env):
    env.define(id, val)
    return val


# VALIDATORS

def validate_parse(operands):
    if len(operands) < 2:
        raise SmileError("few operands")


def validate_operator(operator):
    if not isinstance(operator, Operator) and not isinstance(operator, SpecialOp):
        raise SmileError("{} not operator".format(operator))


def validate_bind(node):
    if not node.left.is_leaf() or node.left.val.type != SYMBOL:
        raise SmileError("wrong bind")


class SmileError(Exception):
    
    def __init__(self, message):
        super(SmileError, self).__init__(f"{message} :^(")
        self.message = f"{message} :^("