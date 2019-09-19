import abc


class Device:
    @abc.abstractmethod
    def step(self):
        pass


class SimpleGate1(Device):
    def __init__(self, x=None, res=None):
        self.x = x
        self.res = res

    @abc.abstractmethod
    def _wiring(self):
        pass

    def step(self):
        res = self._wiring()
        self.res = res

    def __call__(self, x):
        self.x = x
        self.step()
        return self.res


class SimpleGate2(Device):
    def __init__(self):
        self.x = None
        self.y = None
        self.res = None

    @abc.abstractmethod
    def _wiring(self):
        pass

    def step(self):
        res = self._wiring()
        self.res = res

    def __call__(self, x, y):
        self.x = x
        self.y = y
        self.step()
        return self.res


class SimpleGate3(Device):
    def __init__(self):
        self.x = None
        self.y = None
        self.z = None
        self.res = None

    @abc.abstractmethod
    def _wiring(self):
        pass

    def step(self):
        res = self._wiring()
        self.res = res

    def __call__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.step()
        return self.res


class Nand(SimpleGate2):
    def _wiring(self):
        temp = self.x & self.y
        res = 1 - temp
        return res


class Not(SimpleGate1):
    def __init__(self):
        super().__init__()
        self.nand = Nand()

    def _wiring(self):
        return self.nand(self.x, self.x)


class And(SimpleGate2):
    def __init__(self):
        super().__init__()
        self.nand = Nand()
        self.not_ = Not()

    def _wiring(self):
        return self.not_(self.nand(self.x, self.y))


class Or(SimpleGate2):
    def __init__(self):
        super().__init__()
        self.nand0 = Nand()
        self.nand1 = Nand()
        self.nand2 = Nand()

    def _wiring(self):
        a = self.nand0(self.x, self.x)
        b = self.nand1(self.y, self.y)
        return self.nand2(a, b)


class Xor(SimpleGate2):
    def __init__(self):
        super().__init__()
        self.and0 = And()
        self.and1 = And()
        self.not0 = Not()
        self.not1 = Not()
        self.or_ = Or()

    def _wiring(self):
        a = self.and0(self.x, self.not0(self.y))
        b = self.and1(self.not1(self.x), self.y)
        return self.or_(a, b)


class Nor(SimpleGate2):
    def __init__(self):
        super().__init__()
        self.not_ = Not()
        self.or_ = Or()

    def _wiring(self):
        return self.not_(self.or_(self.x, self.y))


class RightShift(SimpleGate1):
    def __init__(self, width=16):
        super().__init__([0] * width, [0] * width)
        self.width = width

    def _wiring(self):
        res = [None] * self.width
        for idx in range(self.width):
            res[(idx + 1) % self.width] = self.x[idx]
        return res


class LeftShift(SimpleGate1):
    def __init__(self, width=16):
        super().__init__([0] * width, [0] * width)
        self.width = width

    def _wiring(self):
        res = [None] * self.width
        for idx in range(self.width):
            res[idx] = self.x[(idx + 1) % self.width]
        return res


class BitwiseOp1(SimpleGate1):
    def __init__(self, op_gate, width=16):
        super().__init__()
        self.width = width
        self.ops = [op_gate() for _ in range(self.width)]

    def _wiring(self):
        res = []
        for idx in range(self.width):
            res.append(self.ops[idx](self.x[idx]))
        return res


class BitwiseOp2(SimpleGate2):
    def __init__(self, op_gate, width=16):
        super().__init__()
        self.width = width
        self.ops = [op_gate() for _ in range(self.width)]

    def _wiring(self):
        if len(self.x) != len(self.y) or len(self.x) != self.width:
            raise ValueError('invalid length')

        res = []
        for idx in range(self.width):
            res.append(self.ops[idx](self.x[idx], self.y[idx]))
        return res


class OneBitMultiplexer(Device):
    def __init__(self):
        self.x = 0
        self.y = 0
        self.selector = 0
        self.res = 0

        self.and0 = And()
        self.and1 = And()
        self.or_ = Or()
        self.not_ = Not()

    def _wiring(self):
        a = self.and0(self.x, self.not_(self.selector))
        b = self.and1(self.selector, self.y)
        return self.or_(a, b)

    def step(self):
        res = self._wiring()
        self.res = res

    def __call__(self, x, y, selector):
        self.x = x
        self.y = y
        self.selector = selector
        self.step()
        return self.res


class Multiplexer2(Device):
    def __init__(self, width=16):
        self.width = width
        self.xs = []
        self.ys = []
        self.selector = 0
        self.res = []

        self.multiplexers = [OneBitMultiplexer() for _ in range(self.width)]

    def _wiring(self):
        res = []
        for idx in range(self.width):
            b = self.multiplexers[idx](self.xs[idx], self.ys[idx], self.selector)
            res.append(b)
        return res

    def step(self):
        res = self._wiring()
        self.res = res

    def __call__(self, xs, ys, selector):
        self.xs = xs
        self.ys = ys
        self.selector = selector
        self.step()
        return self.res


class Multiplexer4(Device):
    def __init__(self, width=16):
        self.width = width
        self.xs = []
        self.ys = []
        self.zs = []
        self.ws = []
        self.selector0 = 0  # first bit
        self.selector1 = 0  # second bit
        self.res = []

        self.mux0 = Multiplexer2(width)
        self.mux1 = Multiplexer2(width)
        self.mux2 = Multiplexer2(width)

    def _wiring(self):
        res = []
        for idx in range(self.width):
            a = self.mux0(self.xs[idx], self.ys[idx], self.selector0)
            b = self.mux1(self.zs[idx], self.ws[idx], self.selector0)
            temp = self.mux2(a, b, self.selector1)
            res.append(temp)
        return res

    def step(self):
        res = self._wiring()
        self.res = res

    def __call__(self, xs, ys, zs, ws, selector0, selector1):
        self.xs = xs
        self.ys = ys
        self.zs = zs
        self.ws = ws
        self.selector0 = selector0
        self.selector1 = selector1

        self.step()
        return self.res


class FeedingLoop(Device):
    def __init__(self):
        self.x = 0
        self.y = 0
        self.res = 0
        self.or_ = Or()

    def _wiring(self):
        res = self.or_(self.x, self.y)
        self.y = res
        return res

    def step(self):
        res = self._wiring()
        self.res = res

    def __call__(self, x):
        self.x = x
        self.step()
        return self.res


if __name__ == '__main__':
    import board
    import time

    f = lambda: time.sleep(0.25)

    c = board.Circuit(100, RightShift, 4)
    c.power_on()
    f()
    c.device([0, 0, 0, 1])
    f()
    print(c.device.res)
    c.device([1, 0, 0, 0])
    f()
    print(c.device.res)
    c.power_off()
