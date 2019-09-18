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
        self.input = []
        self.inc_bit = 0
        self.write_bit = 0
        self.reset = 0
        self.res = []

        self.increment = ops.Increment16bit()
        self.mux0 = gate.Multiplexer2()
        self.mux1 = gate.Multiplexer2()
        self.mux2 = gate.Multiplexer2()

    def _wiring(self):
        res = self.mux0(self.res, self.input, self.write_bit)
        res = self.mux1(res, self.increment(res), self.inc_bit)
        res = self.mux2(res, [0] * 15, self.reset)
        return res

    def step(self):
        res = self._wiring()
        self.res = res

    def __call__(self, new_address, inc_bit, write_bit, reset):
        self.input = new_address
        self.inc_bit = inc_bit
        self.write_bit = write_bit
        self.reset = reset
        self.step()
        return self.res


class InstructionDecoder(gate.Device):
    def __init__(self):
        self.ir = memory.EightBit()
        self.and4s = [gate.BitwiseOp(gate.And, 4) for _ in range(8)]
        self.and3s = [gate.BitwiseOp(gate.And, 3) for _ in range(4)]
        self.nots = [gate.Not() for _ in range(24)]
        self.res = []

    def _wiring(self):
        res = []
        # 0, 1, 1, 1
        add = self.and4s[0](self.nots[0](self.ir[0]), self.ir[1], self.ir[2], self.ir[3])
        res.append(add)

        sub = self.and4s[1](self.nots[1](self.ir[0]), self.nots[2](self.ir[1]), self.ir[2], self.ir[3])
        res.append(sub)
        return NotImplemented

    def step(self):
        res = self._wiring()
        self.res = res

    def __call__(self, instruction):
        self.ir = instruction
        self.step()
        return self.res


class ControlUnit(gate.Device):
    def __init__(self):
        self.ir = memory.EightBit()  # input bus: high byte of instruction register, contains opcode
        self.seq = SequenceGenerator()
        self.instruction_decoder = InstructionDecoder()
        self.alu_flags = [0] * 6  # output: input line of alu

    def step(self):
        pass


if __name__ == '__main__':
    import board
    import time

    c = board.Circuit(32, SequenceGenerator)
    c.power_on(show_step=True)
    time.sleep(5)
    c.power_off()
