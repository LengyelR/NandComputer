import gate


class HalfAdd(gate.Device):
    def __init__(self, x=None, y=None):
        self.x = x
        self.y = y

        self.s = None
        self.carry = None

        self.xor = gate.Xor()
        self.and_ = gate.And()

    def _wiring(self):
        s = self.xor(self.x, self.y)
        carry = self.and_(self.x, self.y)
        return s, carry

    def step(self):
        s, carry = self._wiring()
        self.s = s
        self.carry = carry

    def __call__(self, x, y):
        self.x = x
        self.y = y
        self.step()
        return self.s, self.carry


class FullAdd(gate.Device):
    def __init__(self):
        self.x = None
        self.y = None
        self.c = None
        self.half_add1 = HalfAdd()
        self.half_add2 = HalfAdd()
        self.or_ = gate.Or()

        self.s = None
        self.carry = None

    def _wiring(self):
        sum1, carry1 = self.half_add1(self.x, self.y)
        final_sum, carry2 = self.half_add2(sum1, self.c)
        carry = self.or_(carry1, carry2)
        return final_sum, carry

    def step(self):
        s, carry = self._wiring()
        self.s = s
        self.carry = carry

    def __call__(self, x, y, c):
        self.x = x
        self.y = y
        self.c = c

        self.step()

        return self.s, self.carry


class FullAdd16Bit(gate.Device):
    def __init__(self):
        self.xs = None
        self.ys = None

        self.half_add = HalfAdd()
        self.adders = [FullAdd() for _ in range(15)]

        self.res = []

    def _wiring(self):
        # read the 16 bit inputs in reverse
        res = []
        lsb, carry = self.half_add(self.xs[15], self.ys[15])
        res.insert(0, lsb)

        for idx in range(14, -1, -1):
            digit, carry = self.adders[idx](self.xs[idx], self.ys[idx], carry)
            res.insert(0, digit)
        return res

    def step(self):
        res = self._wiring()
        self.res = res

    def __call__(self, xs, ys):
        self.xs = xs
        self.ys = ys

        self.step()

        return self.res


class Increment2bit(gate.Device):
    def __init__(self):
        self.xs = None

        self.half_add = HalfAdd()
        self.full_add = FullAdd()
        self.res = []

    def _wiring(self):
        res = []
        lsb, carry = self.half_add(self.xs[1], 1)
        res.insert(0, lsb)
        digit, _ = self.full_add(self.xs[0], 0, carry)
        res.insert(0, digit)
        return res

    def step(self):
        res = self._wiring()
        self.res = res

    def __call__(self, xs):
        self.xs = xs
        self.step()
        return self.res


class Increment16bit(gate.Device):
    def __init__(self):
        self.xs = None
        self.adder = FullAdd16Bit()
        self.res = []

    def _wiring(self):
        one = [0]*15 + [1]
        res = self.adder(self.xs, one)
        return res

    def step(self):
        res = self._wiring()
        self.res = res

    def __call__(self, xs):
        self.xs = xs
        self.step()
        return self.res


class TWosComplement(gate.SimpleGate1):
    def __init__(self):
        super().__init__()
        self.full_16bit_adder = FullAdd16Bit()
        self.not_ = [gate.Not() for _ in range(16)]

    def _wiring(self):
        one = [0]*15 + [1]
        inverted = [self.not_[idx](self.x[idx]) for idx in range(len(self.x))]
        res = self.full_16bit_adder(inverted, one)
        return res


class IsNegative(gate.SimpleGate1):
    def _wiring(self):
        msb = self.x[0]
        return msb


class IsZero(gate.SimpleGate1):
    def __init__(self):
        super().__init__()
        self.ors_ = [gate.Or() for _ in range(15)]
        self.not_ = gate.Not()

    def _wiring(self):
        level1 = [self.ors_[idx](self.x[idx*2], self.x[idx*2 + 1]) for idx in range(8)]
        level2 = [self.ors_[idx + 8](level1[idx*2], level1[idx*2 + 1]) for idx in range(4)]
        level3 = [self.ors_[idx + 8 + 4](level2[idx*2], level2[idx*2 + 1]) for idx in range(2)]

        res = self.ors_[14](level3[0], level3[1])

        return self.not_(res)


def main():
    import board
    import time

    ci = board.Circuit(4, FullAdd16Bit)
    ci.power_on()

    xs = [0]*15 + [1]
    ys = [0]*15 + [1]
    ci.device(xs, ys)
    print(ci.device.res)
    xs[3] = 1
    ys[8] = 1
    print()
    print(xs)
    print(ys)
    ci.device(xs, ys)
    time.sleep(0.5)
    print(ci.device.res)

    ci.power_off()

    print('-'*48)
    c = board.Circuit(4, Increment16bit)
    c.power_on()

    x = [1]*14 + [0, 0]
    for _ in range(10):
        print(x)
        c.device(x)
        x = c.device.res
    c.power_off()


if __name__ == '__main__':
    main()
