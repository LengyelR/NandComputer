import gate
import alu
import cu
import memory
import peripheral


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
        self.mux_ac = gate.Multiplexer2()

        self.ALU = alu.ALU()

        self.jump_and = [gate.And() for _ in range(5)]
        self.jump_or = [gate.Or() for _ in range(3)]

        self.is_pos_or = gate.Or()
        self.is_pos_not = gate.Not()
        self.inc_not = gate.Not()

    def _wiring(self):
        address_compute_bit = self.instruction[0]

        # todo: remove if-else branch
        if address_compute_bit == 0:
            self.A(self.instruction, 1)
            pc = self.PC(inc_bit=1, write_bit=0, new_address=self.A.res, reset=0)
            return 0, [0]*16, [0]*16, pc
        else:
            am_bit = self.instruction[3]
            alu_bits = self.instruction[4:10]
            dest_bits = self.instruction[10:13]
            jump_bits = self.instruction[13:16]

            xs = self.D.res
            ys = self.mux_am(self.A.res, self.input_M, am_bit)

            alu_flag = alu.AluFlag(*alu_bits)
            res, is_zero, is_negative = self.ALU(xs, ys, alu_flag)
            is_pos = self.is_pos_not(self.is_pos_or(is_negative, is_zero))

            self.A(res, dest_bits[0])
            self.D(res, dest_bits[1])
            self.output_write_bit = dest_bits[2]
            self.output_M = res

            first_bit = self.jump_and[0](is_negative, jump_bits[0])
            second_bit = self.jump_and[1](is_zero, jump_bits[1])
            third_bit = self.jump_and[2](is_pos, jump_bits[2])

            temp1 = self.jump_or[0](first_bit, second_bit)
            cond_jump = self.jump_or[1](temp1, third_bit)

            temp2 = self.jump_and[3](jump_bits[0], jump_bits[1])
            uncond_jump = self.jump_and[3](temp2, jump_bits[2])
            jump_res = self.jump_or[2](cond_jump, uncond_jump)
            inc_bit = self.inc_not(jump_res)

            pc = self.PC(inc_bit=inc_bit, write_bit=jump_res, new_address=self.A.res, reset=self.reset)
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
        self.pc_bus = [0] * 16
        self.memory_bus = [0] * 16

        self.ROM = memory.ROM(program)
        self.RAM = memory.RAM()
        self.CPU = CPU()

        self.keyboard = peripheral.Keyboard(self.RAM)
        self.screen = peripheral.Screen(self.RAM)

    def _wiring(self):
        instruction = self.ROM(self.pc_bus)
        # todo: wire memory in a better way ...
        mem = self.RAM(self.CPU.A.res, [0]*16, 0)
        write_bit, data, address, pc = self.CPU(instruction, mem, self.reset)
        self.RAM(address, data, write_bit)
        self.pc_bus = pc

    def step(self):
        self._wiring()

    def __call__(self):
        self.step()
        next_instruction = self.ROM(self.pc_bus)
        return self.pc_bus, next_instruction
