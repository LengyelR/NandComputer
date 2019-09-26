import os

from assembler import codegen
from nandcomp.computer import Computer

sum100 = os.path.join('..', 'examples', 'add100.asm')
image = codegen.create(sum100)

computer = Computer(image)
for _ in range(1500):
    next_address, next_ir = computer()
    print(computer.RAM.memory[17])
