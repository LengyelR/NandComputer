import gate


class SrLatchNor(gate.Device):
    """
    S R | Q Q_
    ----+-----
    1 0 | 1 0
    0 1 | 0 1
    0 0 | latched
    1 1 | disallowed
    """
    def __init__(self):
        self.s = None
        self.r = None
        self.q = 1
        self.q_ = 0

        self.nor0 = gate.Nor()
        self.nor1 = gate.Nor()

    def _wiring(self):
        qt = self.nor0(self.s, self.q_)
        qt_ = self.nor1(self.r, self.q)
        return qt, qt_

    def _stabilise(self):
        for _ in range(2):
            self.q, self.q_ = self._wiring()

    def step(self):
        self._stabilise()

        qt, qt_ = self._wiring()
        self.q = qt
        self.q_ = qt_

    def __call__(self, s, r):
        self.s = s
        self.r = r
        self.step()
        return self.q, self.q_


class SrLatchNand(gate.Device):
    """
    S R | Q Q_
    ----+-----
    1 0 | 0 1
    0 1 | 1 0
    0 0 | disallowed
    1 1 | latched
    """
    def __init__(self):
        self.s = None
        self.r = None
        self.q = 1
        self.q_ = 0

        self.nand0 = gate.Nand()
        self.nand1 = gate.Nand()

    def _wiring(self):
        qt = self.nand0(self.s, self.q_)
        qt_ = self.nand1(self.r, self.q)
        return qt, qt_

    def _stabilise(self):
        for _ in range(2):
            self.q, self.q_ = self._wiring()

    def step(self):
        self._stabilise()

        qt, qt_ = self._wiring()
        self.q = qt
        self.q_ = qt_

    def __call__(self, s, r):
        self.s = s
        self.r = r
        self.step()
        return self.q, self.q_
