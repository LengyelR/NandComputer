import gate
import board
import latch


class GatedLatch(gate.Device):
    def __init__(self):
        self.bit = 0
        self.set_bit = 0
        self.res = None

        self.nand0 = gate.Nand()
        self.nand1 = gate.Nand()
        self.sr_latch = latch.SrLatchNand()

    def _wiring(self):
        a = self.nand0(self.bit, self.set_bit)
        b = self.nand1(self.set_bit, a)
        res, _ = self.sr_latch(a, b)
        return res

    def step(self):
        res = self._wiring()
        self.res = res

    def __call__(self, bit, set_bit):
        self.bit = bit
        self.set_bit = set_bit
        self.step()

        return self.bit


class Register(gate.Device):
    def __init__(self, width):
        self.width = width
        self.bits = []
        self.set_bits = 0
        self.res = None

        self.latches = [GatedLatch() for _ in range(self.width)]

    def _wiring(self):
        return [self.latches[idx](self.bits[idx], self.set_bits) for idx in range(self.width)]

    def step(self):
        res = self._wiring()
        self.res = res

    def __call__(self, bits, set_bits):
        self.bits = bits
        self.set_bits = set_bits
        self.step()
        return self.res


class SixteenBit(Register):
    def __init__(self):
        super().__init__(16)


def flip_flop_test():
    import time
    circuit = board.Circuit(16, GatedLatch)
    circuit.power_on()
    time.sleep(0.5)

    def toggling_big_while_set_is_off():
        circuit.device.set_bit = 1
        circuit.device.bit = 1
        circuit.device.set_bit = 0
        time.sleep(0.25)

        for _ in range(5):
            circuit.device.bit = 0
            time.sleep(0.25)
            assert circuit.device.res == 1

            circuit.device.bit = 1
            time.sleep(0.25)
            assert circuit.device.res == 1

    def toggling_bit_while_set_is_on():
        circuit.device.set_bit = 1
        circuit.device.bit = 1
        time.sleep(0.25)

        for _ in range(5):
            circuit.device.bit = 0
            time.sleep(0.25)
            assert circuit.device.res == circuit.device.bit

            circuit.device.bit = 1
            time.sleep(0.25)
            assert circuit.device.res == circuit.device.bit

    def toggling_set_while_bit_is_on():
        circuit.device.set_bit = 1
        circuit.device.bit = 1
        time.sleep(0.5)

        for _ in range(5):
            circuit.device.set_bit = 0
            time.sleep(0.25)
            assert circuit.device.res == 1

            circuit.device.set_bit = 1
            time.sleep(0.25)
            assert circuit.device.res == 1

    def toggling_set_while_bit_is_off():
        circuit.device.set_bit = 1
        circuit.device.bit = 0
        time.sleep(0.25)

        for _ in range(5):
            circuit.device.set_bit = 0
            time.sleep(0.25)
            assert circuit.device.res == 0

            circuit.device.set_bit = 1
            time.sleep(0.25)
            assert circuit.device.res == 0

    toggling_big_while_set_is_off()
    toggling_bit_while_set_is_on()
    toggling_set_while_bit_is_off()
    toggling_set_while_bit_is_on()

    circuit.power_off()


if __name__ == '__main__':
    flip_flop_test()
