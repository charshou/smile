from smile import *

global_frame = create_global_frame()


def run(text):
    try:
        lexer = Lexer(text)
        tokens = lexer.create_tokens()
        parser = Parser(tokens)
        tree = parser.parse()
        interpreter = Interpreter()
        print(interpreter.eval_node(tree, global_frame))
    except SmileError as e:
        print(e)


if __name__ == "__main__":
    while True:
        inp = input(":^) ")
        run(inp)