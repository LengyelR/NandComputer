from assembler.lexer import Lexer
from assembler.parser import Parser


def create(path):
    p = Parser(Lexer, path)
    return p.create_machine_code()


if __name__ == '__main__':
    import os
    program = os.path.join('..', 'examples', 'add100.asm')
    binary = create(program)
    for b in binary:
        print(b)
