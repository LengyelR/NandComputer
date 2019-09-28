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


class Parser:
    def __init__(self, lexer_cls, path):
        tokens, labels = lexer_cls(path).tokenize()
        self.tokens = tokens
        self.labels = labels
        self.symbols = self.create_symbols(tokens, labels)

    def _unary_op(self, args, op1, op2):
        # symbol
        if args[1][0] == '$':
            var_address = self.symbols[args[1]]
            set_a = utils.to_machine_number(var_address)

            if args[0] == args[1]:
                dst = self._encode_destination('M')
            else:
                dst = self._encode_destination(args[0])

            am, operation = self._select_register('M', op1, op2)
            res = [1, 1, 1] + am + operation + dst + [0, 0, 0]
            return [set_a, res]

        # register
        else:
            dst = self._encode_destination(args[0])
            am, operation = self._select_register(args[1], op1, op2)
            res = [1, 1, 1] + am + operation + dst + [0, 0, 0]
            return [res]

    def _binary_op(self, args, op):
        if args[1] != 'D':
            raise ValueError('first argument must be the D register')
        dst = self._encode_destination(args[0])
        am, operation = self._select_register(args[2], None, op)
        res = [1, 1, 1] + am + operation + dst + [0, 0, 0]
        return [res]

    @staticmethod
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

    @staticmethod
    def _encode_destination(arg):
        if arg == 'A':
            return [1, 0, 0]
        if arg == 'D':
            return [0, 1, 0]
        if arg == 'M':
            return [0, 0, 1]
        raise ValueError('Destination must be a register')

    @staticmethod
    def _encode_const(arg):
        if arg == '0':
            return list(alu.zero_op)
        if arg == '1':
            return list(alu.one_op)
        if arg == '-1':
            return list(alu.minus1_op)
        raise ValueError('Only 0, 1, -1 are supported')

    @staticmethod
    def _select_register(arg, x_flag=alu.x_op, y_flag=alu.y_op):
        dont_care = 0

        if arg == 'A':
            return [0], list(y_flag)
        if arg == 'D':
            return [dont_care], list(x_flag)
        if arg == 'M':
            return [1], list(y_flag)

        raise ValueError('Not recognised register')
