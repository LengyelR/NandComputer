import gate
import board
import latch
import utils


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

        return self.res


class Register(gate.Device):
    def __init__(self, width):
        self.width = width
        self.bits = [0]*width
        self.set_bits = 0
        self.res = [0]*width

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

    def __getitem__(self, idx):
        return self.latches[idx].res


class EightBit(Register):
    def __init__(self):
        super().__init__(8)


class SixteenBit(Register):
    def __init__(self):
        super().__init__(16)


class Memory(gate.Device):
    def __init__(self, address_space=15):
        self.memory = [SixteenBit() for _ in range(2**address_space)]
        self.address = [0]*address_space
        self.data = [0]*16
        self.write = 0
        self.res = self.memory[0].res

    def _wiring(self):
        idx = utils.to_integer(self.address)
        res = self.memory[idx](self.data, self.write)
        return res

    def step(self):
        res = self._wiring()
        self.res = res


class ROM(Memory):
    def __init__(self, burn):
        super().__init__()
        if len(burn) != len(self.memory):
            raise ValueError

        for address, data in zip(self.memory, burn):
            address(data, 1)

    def __call__(self, address):
        self.address = address
        self.step()
        return self.res


class RAM(Memory):
    def __init__(self):
        super().__init__()

    def __call__(self, address, data, write_enable):
        self.address = address
        self.data = data
        self.write = write_enable
        self.step()
        return self.res


def flip_flop_test():
    import time
    circuit = board.Circuit(16, GatedLatch)
    circuit.power_on()
    time.sleep(0.25)

    def toggling_bit_while_set_is_off():
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

    toggling_bit_while_set_is_off()
    toggling_bit_while_set_is_on()
    toggling_set_while_bit_is_off()
    toggling_set_while_bit_is_on()

    circuit.power_off()


def _burn_test():
    import time

    data = [[0]*16]*2**15
    data[0] = [0, 1]*8
    data[1] = [1, 0]*8
    data[2] = [1]*16

    c = board.Circuit(1024, ROM, data)
    c.power_on()
    time.sleep(0.25)
    for i in range(5):
        m = utils.to_machine_number(i)
        res = c.device(m)
        print(res)
    c.power_off()


if __name__ == '__main__':
    flip_flop_test()
    _burn_test()
