import re
from functools import partial
from assembler.lexer import Lexer
from assembler.parser import Parser
from nandcomp import utils
from nandcomp import alu


class MachineCode(Parser):
    def _store(self, args):
        """
        STR A, x     --> stores "x" in the A register (x <- [0..2**15])
        STR $var, x  --> stores "x" in a symbol       (x <- [-1, 0, 1])

        note: "A" is the only register which can be set directly to number
        """

        def _parse_number(arg):
            if not re.match(r'^\d+$', arg):
                raise ValueError(f'Argument not a number:{arg}')

            val = int(arg)
            if val > 2 ** 15:
                raise ValueError(f'Not a 15 bit integer:{arg}')
            return val

        # simple case: init a symbol
        if args[0][0] == '$':
            var_address = self.symbols[args[0]]
            set_a = utils.to_machine_number(var_address)

            const = self._encode_const(args[1])
            dst = self._encode_destination('M')
            set_m = [1, 1, 1, 1] + const + dst + [0, 0, 0]
            return [set_a, set_m]

        if args[0] != 'A':
            raise ValueError('Only register A can be used')

        if args[1][0] == '$':
            var_address = self.symbols[args[1]]
            set_a = utils.to_machine_number(var_address)
            return [set_a]
        else:
            value = _parse_number(args[1])
            return [utils.to_machine_number(value)]

    def _move(self, args):
        """
        MOV X, Y  --> stores Y register in X register
        """
        m, register = self._select_register(args[1])
        dst = self._encode_destination(args[0])
        set_m = [1, 1, 1] + m + register + dst + [0, 0, 0]
        return [set_m]

    def _increment(self, args):
        """
        INC Z, X  --> Z = X + 1
        """
        return self._unary_op(args, alu.x_plus_1_op, alu.y_plus_1_op)

    def _decrement(self, args):
        """
        DEC Z, X  --> Z = X - 1
        """
        return self._unary_op(args, alu.x_minus_1_op, alu.y_minus_1_op)

    def _not(self, args):
        """
        NOT Z, X, --> Z = ~X
        """
        return self._unary_op(args, alu.not_x_op, alu.not_y_op)

    def _neg(self, args):
        """
        NEG Z, X, --> Z = -X
        """
        return self._unary_op(args, alu.minus_x_op, alu.minus_y_op)

    def _or(self, args):
        """
        OR Z, D, Y  --> Z = D | Y
        """
        return self._binary_op(args, alu.x_and_y_op)

    def _and(self, args):
        """
        AND Z, D, Y  --> Z = D & Y
        """
        return self._binary_op(args, alu.x_or_y_op)

    def _addition(self, args):
        """
        ADD Z, D, Y  --> Z = D + Y
        """
        return self._binary_op(args, alu.x_plus_y_op)

    def _subtraction(self, args):
        """
        SUB Z, X, Y  --> Z = X - Y
        """
        dst = self._encode_destination(args[0])
        if args[2] != 'D':  # D - X
            am, operation = self._select_register(args[2], None, alu.x_minus_y_op)
        else:  # X - D
            am, operation = self._select_register(args[1], None, alu.y_minus_x_op)
        sub = [1, 1, 1] + am + operation + dst + [0, 0, 0]
        return [sub]

    def _jump(self, args, jump_code):
        label = args[1][1:]
        label_address = self.symbols[label]
        set_a = utils.to_machine_number(label_address)

        # not allowing side effects
        dst = [0, 0, 0]
        # only direct registers can used (no calculations are allowed)
        am, register = self._select_register(args[0])
        jump = [1, 1, 1] + am + register + dst + jump_code
        return [set_a, jump]

    def _uncond_jump(self, args):
        if len(args) > 1:
            raise ValueError('Too many arguments')
        label = args[0][1:]
        label_address = self.symbols[label]
        set_a = utils.to_machine_number(label_address)

        # not allowing side effects
        dst = [0, 0, 0]
        dont_care = [0]
        dont_care_const = self._encode_const('0')
        jump = [1, 1, 1] + dont_care + dont_care_const + dst + [1, 1, 1]
        return [set_a, jump]

    def _to_binary(self, tokens):

        op = tokens[0]
        args = tokens[1]

        binary = {
            'STR': partial(self._store, args),
            'MOV': partial(self._move, args),
            'ADD': partial(self._addition, args),
            'AND': partial(self._and, args),
            'OR':  partial(self._or, args),
            'SUB': partial(self._subtraction, args),
            'INC': partial(self._increment, args),
            'DEC': partial(self._decrement, args),

            'JMP': partial(self._uncond_jump, args),
            'JGT': partial(self._jump, args, [0, 0, 1]),
            'JEQ': partial(self._jump, args, [0, 1, 0]),
            'JGE': partial(self._jump, args, [0, 1, 1]),
            'JLT': partial(self._jump, args, [1, 0, 0]),
            'JNE': partial(self._jump, args, [1, 0, 1]),
            'JLE': partial(self._jump, args, [1, 1, 0]),
        }
        return binary[op]()

    def assemble(self):
        res = []
        for token in self.tokens:
            res.extend(self._to_binary(token))
        return res

    def print_binary(self):
        for b in self.assemble():
            print(b)


def create(path):
    m = MachineCode(Lexer, path)
    return m.assemble()


if __name__ == '__main__':
    import os
    program = os.path.join('..', 'examples', 'add100.asm')
    machine_code = create(program)
    for line in machine_code:
        print(line)
