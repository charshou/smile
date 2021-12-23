import smile


def run(text, global_frame):
    try:
        lexer = smile.Lexer(text)
        tokens = lexer.create_tokens()
        parser = smile.Parser(tokens)
        tree = parser.parse()
        interpreter = smile.Interpreter()
        return (interpreter.eval_node(tree, global_frame))
    except smile.SmileError as e:
        return (e.message)


if __name__ == "__main__":
    global_frame = smile.create_global_frame()
    
    while True:
        inp = input(":^) ")
        print(run(inp, global_frame))