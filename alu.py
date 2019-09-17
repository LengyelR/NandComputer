from collections import namedtuple
import gate
import ops

AluFlag = namedtuple('alu_flag', ['zx', 'nx', 'zy', 'ny', 'f', 'no'])


class ALU(gate.Device):
    def __init__(self):
        self.xs = None
        self.ys = None
        self.flags = None

        self.temp_xs = None
        self.temp_ys = None
        self.res = (None, None, None)

        self.bitwise_and = gate.BitwiseOp(gate.And)

        self.twos_complements = [ops.TWosComplement() for _ in range(3)]
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
        xs = self.mux2_zx(self.xs, [0]*16, self.flags.zx)
        ys = self.mux2_zy(self.ys, [0]*16, self.flags.zy)

        xs = self.mux2_nx(xs, self.twos_complements[0](xs), self.flags.zx)
        ys = self.mux2_ny(ys, self.twos_complements[1](ys), self.flags.ny)

        add_ = self.adder(xs, ys)
        and_ = self.bitwise_and(xs, ys)

        res = self.mux2_add(and_, add_, self.flags.f)

        self.mux2_negate(res, self.twos_complements[2](res), self.flags.no)

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


if __name__ == '__main__':
    import board

    x = [0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 0]
    y = [0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1]

    alu_flags = AluFlag(0, 0, 0, 0, 1, 0)
    c = board.Circuit(4, ALU)
    c.power_on()
    print(c.device.res)
    print(x)
    print(y)
    c.device(x, y, alu_flags)
    r = c.device.res
    print(r[0])
    print(r[1], r[2])
    c.power_off()
