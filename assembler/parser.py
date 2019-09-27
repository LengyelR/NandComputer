import re
from nandcomp import alu
from nandcomp import utils


class Symbol:
    def __init__(self):
        self.pointer = 16
        self.data = {f'$R{i}': 0 for i in range(16)}  # init virtual registers

    def put(self, key):
        self.data[key] = self.pointer
        self.pointer += 1

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __contains__(self, item):
        return item in self.data

    def items(self):
        return self.data.items()


def create_symbols(tokens, labels):
    symbols = Symbol()
    for op, args in tokens:
        if op != 'STR':
            continue

        for arg in args:
            if arg in symbols or not arg.startswith('$'):
                continue

            symbols.put(arg)

    for label, address in labels:
        symbols[label] = address

    return symbols


def _encode_destination(arg):
    if arg == 'A':
        return [1, 0, 0]
    if arg == 'D':
        return [0, 1, 0]
    if arg == 'M':
        return [0, 0, 1]
    raise ValueError('Destination must be a register')


def _encode_const(arg):
    if arg == '0':
        return list(alu.zero_op)
    if arg == '1':
        return list(alu.one_op)
    if arg == '-1':
        return list(alu.minus1_op)
    raise ValueError('Only 0, 1, -1 are supported')


def _select_register(arg, x_flag=alu.x_op, y_flag=alu.y_op):
    dont_care = 0

    if arg == 'A':
        return [0], list(y_flag)
    if arg == 'D':
        return [dont_care], list(x_flag)
    if arg == 'M':
        return [1], list(y_flag)

    raise ValueError('Not recognised register')


class Parser:
    def __init__(self, lexer_cls, path):
        tokens, labels = lexer_cls(path).tokenize()
        self.tokens = tokens
        self.labels = labels
        self.symbols = create_symbols(tokens, labels)

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

            const = _encode_const(args[1])
            dst = _encode_destination('M')
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
        m, register = _select_register(args[1])
        dst = _encode_destination(args[0])
        set_m = [1, 1, 1] + m + register + dst + [0, 0, 0]
        return [set_m]

    def _unary_op(self, args, op1, op2):
        # symbol
        if args[1][0] == '$':
            var_address = self.symbols[args[1]]
            set_a = utils.to_machine_number(var_address)

            if args[0] == args[1]:
                dst = _encode_destination('M')
            else:
                dst = _encode_destination(args[0])

            am, operation = _select_register('M', op1, op2)
            res = [1, 1, 1] + am + operation + dst + [0, 0, 0]
            return [set_a, res]

        # register
        else:
            dst = _encode_destination(args[0])
            am, operation = _select_register(args[1], op1, op2)
            res = [1, 1, 1] + am + operation + dst + [0, 0, 0]
            return [res]

    def _increment(self, args):
        """
        INC X  --> X = X + 1
        """
        return self._unary_op(args, alu.x_plus_1_op, alu.y_plus_1_op)

    def _decrement(self, args):
        """
        INC X  --> X = X - 1
        """
        return self._unary_op(args, alu.x_minus_1_op, alu.y_minus_1_op)

    def _addition(self, args):
        """
        ADD Z, D, Y  --> Z = D + Y
        """
        dst = _encode_destination(args[0])
        am, operation = _select_register(args[2], None, alu.x_plus_y_op)
        add = [1, 1, 1] + am + operation + dst + [0, 0, 0]
        return [add]

    def _subtraction(self, args):
        """
        SUB Z, X, Y  --> Z = X - Y
        """
        dst = _encode_destination(args[0])
        if args[2] != 'D':  # D - X
            am, operation = _select_register(args[2], None, alu.x_minus_y_op)
        else:  # X - D
            am, operation = _select_register(args[1], None, alu.y_minus_x_op)
        sub = [1, 1, 1] + am + operation + dst + [0, 0, 0]
        return [sub]

    def _jgt(self, args):
        label = args[1][1:]
        label_address = self.symbols[label]
        set_a = utils.to_machine_number(label_address)

        # not allowing side effects
        dst = [0, 0, 0]
        # only direct registers can used (no calculations are allowed)
        am, register = _select_register(args[0])
        jump = [1, 1, 1] + am + register + dst + [0, 0, 1]
        return [set_a, jump]

    def _jump(self, args):
        if len(args) > 1:
            raise ValueError('Too many arguments')
        label = args[0][1:]
        label_address = self.symbols[label]
        set_a = utils.to_machine_number(label_address)

        # not allowing side effects
        dst = [0, 0, 0]
        dont_care = [0]
        dont_care_const = _encode_const('0')
        jump = [1, 1, 1] + dont_care + dont_care_const + dst + [1, 1, 1]
        return [set_a, jump]

    def _to_binary(self, tokens):

        op = tokens[0]
        args = tokens[1]

        if op == 'STR':
            return self._store(args)

        if op == 'MOV':
            return self._move(args)

        if op == 'ADD':
            return self._addition(args)

        if op == 'SUB':
            return self._subtraction(args)

        if op == 'INC':
            return self._increment(args)

        if op == 'DEC':
            return self._decrement(args)

        if op == 'JMP':
            return self._jump(args)

        if op == 'JGT':
            return self._jgt(args)

        raise ValueError('Unknown token')

    def create_machine_code(self):
        res = []
        for token in self.tokens:
            res.extend(self._to_binary(token))
        return res

    def print_binary(self):
        for b in self.create_machine_code():
            print(b)


if __name__ == '__main__':
    import os
    import assembler.lexer as le

    program = os.path.join('..', 'examples', 'add100.asm')
    p = Parser(le.Lexer, program)
    p.print_binary()
