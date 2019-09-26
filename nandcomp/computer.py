from nandcomp import alu
from nandcomp import gate
from nandcomp import cu
from nandcomp import memory
from nandcomp import peripheral


class CPU(gate.Device):
    def __init__(self):
        # inputs
        self.instruction = []
        self.input_M = []
        self.reset = 0

        # outputs
        self.output_M = []
        self.address_M = []
        self.output_write_bit = 0
        self.output_PC = []

        # registers
        self.A = memory.SixteenBit()
        self.D = memory.SixteenBit()
        self.PC = cu.ProgramCounter()

        # components
        self.mux_am = gate.Multiplexer2()

        self.ac_not = gate.Not()

        self.ALU = alu.ALU()
        self.jump_control = cu.JumpControl()
        self.write_control = cu.WriteControl()

    def _decode(self):
        ac_bit = self.instruction[0]
        am_bit = self.instruction[3]
        alu_bits = self.instruction[4:10]
        dest_bits = self.instruction[10:13]
        jump_bits = self.instruction[13:16]
        return ac_bit, am_bit, alu_bits, dest_bits, jump_bits

    def _wiring(self):
        ac_bit, am_bit, alu_bits, dest_bits, jump_bits = self._decode()

        self.A(self.instruction, self.ac_not(ac_bit))

        xs = self.D.res
        ys = self.mux_am(self.A.res, self.input_M, am_bit)

        alu_flag = alu.AluFlag(*alu_bits)
        res, is_zero, is_negative = self.ALU(xs, ys, alu_flag)

        write_a, write_d, write_m = self.write_control(dest_bits, ac_bit)
        self.A(res, write_a)
        self.D(res, write_d)
        self.output_write_bit = write_m
        self.output_M = res

        inc_bit, jump_ac_flow = self.jump_control(is_zero, is_negative, jump_bits, ac_bit)

        pc = self.PC(inc_bit=inc_bit, write_bit=jump_ac_flow, new_address=self.A.res, reset=self.reset)
        return dest_bits[2], res, self.A.res, pc

    def step(self):
        write_bit, res, address, pc = self._wiring()
        self.output_write_bit = write_bit
        self.output_M = res
        self.address_M = address
        self.output_PC = pc

    def __call__(self, instruction, mem, reset):
        self.instruction = instruction
        self.input_M = mem
        self.reset = reset
        self.step()
        return self.output_write_bit, self.output_M, self.address_M, self.output_PC


class Computer(gate.Device):
    def __init__(self, program):
        self.reset = 0
        self.PC_bus = [0] * 16
        self.memory_bus = [0] * 16

        self.ROM = memory.ROM(program)
        self.RAM = memory.RAM()
        self.CPU = CPU()

        self.keyboard = peripheral.Keyboard(self.RAM)
        self.screen = peripheral.Screen(self.RAM)

    def _wiring(self):
        instruction = self.ROM(self.PC_bus)
        write_bit, data, address, pc = self.CPU(instruction, self.memory_bus, self.reset)
        self.RAM(address, data, write_bit)
        self.PC_bus = pc
        self.memory_bus = self.RAM(address, data, 0)

    def step(self):
        self._wiring()

    def __call__(self):
        self.step()
        next_instruction = self.ROM(self.PC_bus)
        return self.PC_bus, next_instruction


def program_test():
    from nandcomp import utils

    def show_memory():
        for address in range(16, 20):
            memory_val = computer.RAM.memory[address]
            decimal = utils.to_integer(memory_val.res)
            print(address, memory_val, decimal)

    two_plus_two_minus_one = [
        0b0000000000000010,  # @2        --> A = 2
        0b1110110000010000,  # D = A     --> D = 2
        0b1110000010010000,  # D = D + A --> D += 2
        0b1111001110010000,  # D = D - 1 --> D--
        0b0000000000000000,  # @0        --> A = 0
        0b1110001100001000,  # M = D     --> M[0] = 3
    ]
    sum100 = [
        0b0000000000010000,  # 0   @i        --> A = 16
        0b1111111111001000,  # 1   M = 1     --> M[16] = 1    --> var i = 1
        0b0000000000010001,  # 2   @sum      --> A = 17
        0b1110101010001000,  # 3   M = 0     --> M[17] = 0    --> var sum = 0
        0b0000000000010000,  # 4   @i        --> A = 16
        0b1111110000010000,  # 5   D = M     --> D = M[16]    --> D = i
        0b0000000001100100,  # 6   @100      --> A = 100
        0b1110010011010000,  # 7   D = D - A --> D = D - 100  --> D = i - 100
        0b0000000000010010,  # 8   @END      --> A = 18
        0b1110001100000001,  # 9   D;JGT     --> IF D > 0 THEN GOTO 18
        0b0000000000010000,  # 10  @i        --> A = 16
        0b1111110000010000,  # 11  D = M     --> D = M[16]          --> D = i
        0b0000000000010001,  # 14  @sum      --> A = 17
        0b1111000010001000,  # 13  M = D + M --> M[17] = M[17] + D  --> sum += i
        0b0000000000010000,  # 14  @i        --> A = 16
        0b1111110111001000,  # 15  M = M + 1 --> M[16] = M[16] + 1  --> i++
        0b0000000000000100,  # 16  @LOOP     --> A = 4
        0b1110101010000111,  # 17  0;JMP     --> GOTO 4
        0b0000000000010010,  # 18  @END      --> A = 18
        0b1110101010000111,  # 19  0;JMP     --> GOTO 18
    ]

    image = utils.create_image(sum100)
    computer = Computer(image)
    next_address, next_ir = computer()

    for _ in range(2000):
        # instruction to be executed
        i = utils.to_integer(next_address)
        decoded = utils.decode_ir(next_ir)
        print('line no', i)
        print(decoded)

        # execute
        next_address, next_ir = computer()

        # show registers, ram
        print('A', utils.to_integer(computer.CPU.A.res), computer.CPU.A.res)
        print('D', utils.to_integer(computer.CPU.D.res), computer.CPU.D.res)
        show_memory()
        print('-'*48)


if __name__ == '__main__':
    program_test()
