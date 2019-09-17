import gate
import ops
import memory


class SequenceGenerator(gate.Device):
    def __init__(self):
        self.one = [0, 1]
        self.res = [0, 0]
        self.register = memory.Register(2)
        self.inc = ops.Increment2bit()

    def _wiring(self):
        res = self.inc(self.res)
        self.register(res, 1)
        return res

    def step(self):
        res = self._wiring()
        self.res = res


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
        self.ir = memory.EightBit()     # input bus: high byte of instruction register, contains opcode
        self.seq = SequenceGenerator()
        self.instruction_decoder = InstructionDecoder()
        self.alu_flags = [0]*6          # output: input line of alu

    def step(self):
        pass


if __name__ == '__main__':
    import board
    import time

    c = board.Circuit(4, SequenceGenerator)
    c.power_on()
    for _ in range(8):
        print(c.device.res)
        time.sleep(0.25)
    c.power_off()
