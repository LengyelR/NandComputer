import gate
import ops
import memory


class SequenceGenerator(gate.Device):
    def __init__(self):
        self.register = memory.Register(2)
        self.inc = ops.Increment2bit()
        self.res = self.register.res

    def _wiring(self):
        set_bit = 1
        res = self.inc(self.register.res)
        self.register(res, set_bit)
        return res

    def step(self):
        res = self._wiring()
        self.res = res

    def __call__(self):
        self.step()
        return self.res


class ProgramCounter(gate.Device):
    def __init__(self):
        self.input = [0]*16
        self.inc_bit = 0
        self.write_bit = 0
        self.reset = 0
        self.res = [0]*16

        self.increment = ops.Increment16bit()
        self.mux0 = gate.Multiplexer2()
        self.mux1 = gate.Multiplexer2()
        self.mux2 = gate.Multiplexer2()

    def _wiring(self):
        res = self.mux0(self.res, self.input, self.write_bit)
        res = self.mux1(res, self.increment(res), self.inc_bit)
        res = self.mux2(res, [0]*16, self.reset)
        return res

    def step(self):
        res = self._wiring()
        self.res = res

    def __call__(self, inc_bit, write_bit, new_address, reset):
        self.input = new_address
        self.write_bit = write_bit
        self.inc_bit = inc_bit
        self.reset = reset
        self.step()
        return self.res


if __name__ == '__main__':
    import board
    import time

    c = board.Circuit(32, SequenceGenerator)
    c.power_on(show_step=True)
    time.sleep(5)
    c.power_off()
