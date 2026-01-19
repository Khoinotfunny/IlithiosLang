# Something beautiful is happening =)
# This is the main REPL for IthiliosPy (or short is Ithilios)

import sys
import os
from Interpreter import *

def run_file(filename):
    file_extension = os.path.splitext(filename)[1]
    if file_extension != ".ili":
        print("Error: Only .ili files are supported.")
        return

    with open(filename,"r",encoding='utf-8') as f:
        code = f.read()
    
    lexer = JoulLexer()
    parser = JoulParser()
    interpreter = JoulInterpreter()

    tokens = lexer.tokenize(code)
    ast = parser.parse(tokens)
    interpreter.walk(ast)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_file(sys.argv[1])
    else:
        lexer = JoulLexer()
        parser = JoulParser()
        interpreter = JoulInterpreter()
        print("Ithilios Language Intepreter")
        while True:
            try:
                text = input('input >> ')
                if not text.strip(): continue
                if text.lower() == "exit":
                    print("Goodbye!")
                    break
                else:
                    tokens = lexer.tokenize(text)
                    ast = parser.parse(tokens)
                    if ast:
                        for node in ast:
                            result = interpreter.walk(node)
                            # Nếu kết quả trả về không phải None (tức là một biểu thức rời như 45+45)
                            # thì chúng ta mới in nó ra màn hình.
                            if result is not None:
                                print(result)
            except EOFError: break
            except Exception as e:
                print(f"Error: {e}")