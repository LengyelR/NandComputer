import gate
import alu
import cu
import memory
import peripheral


class CPU(gate.Device):
    def __init__(self):
        # inputs
        self.instruction = []    # 16 bits, the binary instruction
        self.input_M = [0]*16    # value of M[A], 16 bits (coming from RAM)
        self.reset = 0           # a "button" to reset the computer

        # outputs
        self.write = 0           # if write enable bit is set ...
        self.output_M = [0]*16   # these 16 bits will be written (into RAM)...
        self.address_M = [0]*15  # at this 15 bit address...

        self.output_PC = []      # address of next instruction to be executed (goes into PC)

        # registers
        self.A = memory.Register(16)
        self.D = memory.Register(16)
        self.PC = cu.ProgramCounter()

        # components
        self.mux0 = gate.Multiplexer2()
        self.mux1 = gate.Multiplexer2()

        self.alu = alu.ALU()
        self.decoder = cu.InstructionDecoder()
        self.seq = cu.SequenceGenerator()

    def _wiring(self):
        decoded = self.decoder(self.instruction)

        am = self.mux0(self.A.res, self.input_M, decoded.AM)
        z, is_zero, is_negative = self.alu(am, self.D.res, decoded.alu_flags)

        next_instruction_address = self.PC(self.A.res, decoded.inc_bit, decoded.write_bit, self.reset)
        self.output_PC = next_instruction_address

    def step(self):
        pass

    def __call__(self, instruction, mem, reset):
        return NotImplemented


class Computer(gate.Device):
    def __init__(self):
        self.reset = 0
        self.pc = 0
        self.mem_val = [0]*16

        self.ROM = memory.ROM([[0]*16]*2**15)
        self.RAM = memory.RAM()
        self.CPU = CPU()

        self.keyboard = peripheral.Keyboard(self.RAM)
        self.screen = peripheral.Screen(self.RAM)

    def _wiring(self):
        instruction = self.ROM(self.pc)
        write, data, address, pc = self.CPU(instruction, self.mem_val, self.reset)
        self.RAM(address, data, write)
        self.pc = pc

    def step(self):
        self._wiring()
