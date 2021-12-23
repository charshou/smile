import smile

global_frame = smile.create_global_frame()


def run(text):
    try:
        lexer = smile.Lexer(text)
        tokens = lexer.create_tokens()
        parser = smile.Parser(tokens)
        tree = parser.parse()
        print(tree)
        interpreter = smile.Interpreter()
        print(interpreter.eval_node(tree, global_frame))
    except smile.SmileError as e:
        print(e)


if __name__ == "__main__":
    while True:
        inp = input(":^) ")
        run(inp)