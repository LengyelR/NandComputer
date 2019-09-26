from collections import namedtuple
from nandcomp import gate
from nandcomp import ops

AluFlag = namedtuple('alu_flag', ['zx', 'nx', 'zy', 'ny', 'f', 'no'])

zero_op      = (1, 0, 1, 0, 1, 0)
one_op       = (1, 1, 1, 1, 1, 1)
minus1_op    = (1, 1, 1, 0, 1, 0)
x_op         = (0, 0, 1, 1, 0, 0)
not_x_op     = (0, 0, 1, 1, 0, 1)
minus_x_op   = (0, 0, 1, 1, 1, 1)
y_op         = (1, 1, 0, 0, 0, 0)
not_y_op     = (1, 1, 0, 0, 0, 1)
minus_y_op   = (1, 1, 0, 0, 1, 1)
x_plus_1_op  = (0, 1, 1, 1, 1, 1)
y_plus_1_op  = (1, 1, 0, 1, 1, 1)
x_minus_1_op = (0, 0, 1, 1, 1, 0)
y_minus_1_op = (1, 1, 0, 0, 1, 0)
x_plus_y_op  = (0, 0, 0, 0, 1, 0)
x_minus_y_op = (0, 1, 0, 0, 1, 1)
y_minus_x_op = (0, 0, 0, 1, 1, 1)
x_and_y_op   = (0, 0, 0, 0, 0, 0)
x_or_y_op    = (0, 1, 0, 1, 0, 1)


class ALU(gate.Device):
    def __init__(self):
        self.xs = None
        self.ys = None
        self.flags = None

        self.temp_xs = None
        self.temp_ys = None
        self.res = (None, None, None)

        self.bitwise_and = gate.BitwiseOp2(gate.And)

        self.inverters = [gate.BitwiseOp1(gate.Not) for _ in range(3)]
        self.is_zero = ops.IsZero()
        self.adder = ops.FullAdd16Bit()
        self.is_negative = ops.IsNegative()

        self.mux2_zx = gate.Multiplexer2()
        self.mux2_nx = gate.Multiplexer2()

        self.mux2_zy = gate.Multiplexer2()
        self.mux2_ny = gate.Multiplexer2()

        self.mux2_add = gate.Multiplexer2()
        self.mux2_negate = gate.Multiplexer2()

    def _wiring(self):
        xs = self.mux2_zx(self.xs, [0] * 16, self.flags.zx)
        xs = self.mux2_nx(xs, self.inverters[0](xs), self.flags.nx)

        ys = self.mux2_zy(self.ys, [0] * 16, self.flags.zy)
        ys = self.mux2_ny(ys, self.inverters[1](ys), self.flags.ny)

        add_ = self.adder(xs, ys)
        and_ = self.bitwise_and(xs, ys)

        res = self.mux2_add(and_, add_, self.flags.f)

        res = self.mux2_negate(res, self.inverters[2](res), self.flags.no)

        return res, self.is_zero(res), self.is_negative(res)

    def step(self):
        res = self._wiring()
        self.res = res

    def __call__(self, xs, ys, flags):
        self.xs = xs
        self.ys = ys
        self.flags = flags

        self.step()
        return self.res


def test_alu():
    from nandcomp import board
    from nandcomp import utils

    zero_flag = AluFlag(*zero_op)
    one_flag = AluFlag(*one_op)
    minus1_flag = AluFlag(*minus1_op)
    x_flag = AluFlag(*x_op)
    not_x_flag = AluFlag(*not_x_op)
    minus_x_flag = AluFlag(*minus_x_op)
    y_flag = AluFlag(*y_op)
    not_y_flag = AluFlag(*not_y_op)
    minus_y_flag = AluFlag(*minus_y_op)
    x_plus_1_flag = AluFlag(*x_plus_1_op)
    y_plus_1_flag = AluFlag(*y_plus_1_op)
    x_minus_1_flag = AluFlag(*x_minus_1_op)
    y_minus_1_flag = AluFlag(*y_minus_1_op)
    x_plus_y_flag = AluFlag(*x_plus_y_op)
    x_minus_y_flag = AluFlag(*x_minus_y_op)
    y_minus_x_flag = AluFlag(*y_minus_x_op)
    x_and_y_flag = AluFlag(*x_and_y_op)
    x_or_y_flag = AluFlag(*x_or_y_op)

    c = board.Circuit(4, ALU)

    def _assert(r, flag):
        x1 = utils.to_machine_number(x)
        y1 = utils.to_machine_number(y)

        res, is_zero, is_negative = c.device(x1, y1, flag)
        assert utils.to_integer(res) == r
        assert is_zero == (1 if r == 0 else 0)
        assert is_negative == (1 if r < 0 else 0)

    data = [(67, 49), (32, 75), (5123, 7546), (2 ** 14 - 17, 2 ** 13 + 6), (0, 0), (0, 1), (1, 1)]

    for x, y in data:
        _assert(0, zero_flag)
        _assert(1, one_flag)
        _assert(-1, minus1_flag)

        _assert(x, x_flag)
        _assert(y, y_flag)
        _assert(-y, minus_y_flag)
        _assert(-x, minus_x_flag)
        _assert(-x - 1, not_x_flag)
        _assert(-y - 1, not_y_flag)

        _assert(x + 1, x_plus_1_flag)
        _assert(y + 1, y_plus_1_flag)
        _assert(x - 1, x_minus_1_flag)
        _assert(y - 1, y_minus_1_flag)
        _assert(x + y, x_plus_y_flag)
        _assert(x - y, x_minus_y_flag)
        _assert(y - x, y_minus_x_flag)

        _assert(x & y, x_and_y_flag)
        _assert(x | y, x_or_y_flag)


if __name__ == '__main__':
    test_alu()
