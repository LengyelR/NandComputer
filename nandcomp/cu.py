from nandcomp import gate
from nandcomp import ops
from nandcomp import memory


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


class JumpControl(gate.Device):
    def __init__(self):
        self.jump_bits = [0]*3

        self.is_negative = 0
        self.is_zero = 0
        self.ac_bit = 0

        self.inc_bit = 0
        self.jump = 0

        self.is_pos_or = gate.Or()
        self.is_pos_not = gate.Not()

        self.and_ = [gate.And() for _ in range(5)]
        self.or_ = [gate.Or() for _ in range(3)]
        self.not_ = gate.Not()

    def _wiring(self):
        is_pos = self.is_pos_not(self.is_pos_or(self.is_negative, self.is_zero))

        first_bit = self.and_[0](self.is_negative, self.jump_bits[0])
        second_bit = self.and_[1](self.is_zero, self.jump_bits[1])
        third_bit = self.and_[2](is_pos, self.jump_bits[2])

        temp1 = self.or_[0](first_bit, second_bit)
        cond_jump = self.or_[1](temp1, third_bit)

        temp2 = self.and_[3](self.jump_bits[0], self.jump_bits[1])
        uncond_jump = self.and_[3](temp2, self.jump_bits[2])
        jump_res = self.or_[2](cond_jump, uncond_jump)

        jump_ac_flow = self.and_[4](jump_res, self.ac_bit)
        inc_bit = self.not_(jump_ac_flow)

        return inc_bit, jump_ac_flow

    def step(self):
        inc_bit, jump = self._wiring()
        self.inc_bit = inc_bit
        self.jump = jump

    def __call__(self, is_zero, is_negative, jump_bits, ac_bit):
        self.is_zero = is_zero
        self.is_negative = is_negative
        self.jump_bits = jump_bits
        self.ac_bit = ac_bit
        self.step()
        return self.inc_bit, self.jump


class WriteControl(gate.Device):
    def __init__(self):
        self.destination_bits = [0]*3
        self.ac_bit = 0

        self.write_A = 0
        self.write_D = 0
        self.write_M = 0

        self.and_ = [gate.And() for _ in range(3)]

    def _wiring(self):
        a = self.and_[0](self.destination_bits[0], self.ac_bit)
        d = self.and_[1](self.destination_bits[1], self.ac_bit)
        m = self.and_[2](self.destination_bits[2], self.ac_bit)
        return a, d, m

    def step(self):
        a, d, m = self._wiring()
        self.write_A = a
        self.write_D = d
        self.write_M = m

    def __call__(self, destination_bits, ac_bit):
        self.destination_bits = destination_bits
        self.ac_bit = ac_bit
        self.step()
        return self.write_A, self.write_D, self.write_M


if __name__ == '__main__':
    import time
    from nandcomp import board

    c = board.Circuit(32, SequenceGenerator)
    c.power_on(show_step=True)
    time.sleep(5)
    c.power_off()
