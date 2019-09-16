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

    def _wiring(self):
        self.temp_xs = self.xs
        self.temp_ys = self.ys

        if self.flags.zx:
            self.temp_xs = [0] * 16
        if self.flags.nx:
            self.temp_xs = self.twos_complements[0](self.temp_xs)

        if self.flags.zy:
            self.temp_ys = [0] * 16
        if self.flags.ny:
            self.temp_ys = self.twos_complements[1](self.temp_ys)

        if self.flags.f:
            op = self.adder
        else:
            op = self.bitwise_and

        res = op(self.temp_xs, self.temp_ys)

        if self.flags.no:
            res = self.twos_complements[2](res)

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

    x = [0, 0, 0, 0,
         1, 0, 1, 1,
         0, 1, 1, 1,
         0, 1, 0, 0]
    y = [0, 0, 0, 1,
         0, 0, 1, 0,
         0, 1, 1, 1,
         0, 0, 1, 1]

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
