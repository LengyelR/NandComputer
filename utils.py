def to_integer(machine_number):
    integer = sum([bit * 2 ** idx for idx, bit in enumerate(reversed(machine_number))])
    if machine_number[0] == 0:
        return integer
    else:
        return integer - 2**16


def to_machine_number(integer):
    if integer < 0:
        integer = 2**16 + integer
    return [int(bit) for bit in f'{integer:016b}']


def create_image(program):
    return [to_machine_number(i) for i in program]


def decode_ir(instruction):
    if instruction[0] == 0:
        return f'A = {to_integer(instruction[1:])}'

    ys = 'M[A]' if instruction[3] else 'A'

    destination = []
    dest_bits = instruction[10:13]
    if dest_bits[0] == 1:
        destination.append('A')
    if dest_bits[1] == 1:
        destination.append('D')
    if dest_bits[2] == 1:
        destination.append('M[A]')

    dest_str = ', '.join(destination)
    dest_str = dest_str if dest_str else 'NULL'

    alu_bits = instruction[4:10]
    jump_bits = instruction[13:16]

    xs = '0' if alu_bits[0] else 'D'
    xs_sign = '!' if alu_bits[1] else ''
    ys = '0' if alu_bits[2] else ys
    ys_sign = '!' if alu_bits[3] else ''
    op = '+' if alu_bits[4] else '&'

    jump = ''.join(str(j) for j in jump_bits) if any(jump_bits) else ''

    if alu_bits[5]:
        return f'{dest_str} = !({xs_sign}{xs} {op} {ys_sign}{ys}); {jump}'
    else:
        return f'{dest_str} = {xs_sign}{xs} {op} {ys_sign}{ys}; {jump}'


def _show_num_convert():
    def show(num):
        mi = to_machine_number(num)
        integer = to_integer(mi)
        print(integer, mi)

    for i in range(10):
        show(i)
    show(2 ** 10)
    show(2 ** 13 + 64)
    show(2 ** 15 - 1)
    show(2 ** 15)

    show(2 ** 16 - 1)
    show(-1)
    show(-3)
    show(-18)


def _show_decode():
    sum100_0 = [
        0b0000000000010000,
        0b1110111111001000,
        0b0000000000010001,
        0b1110101010001000,
        0b0000000000010000,
        0b1111110000010000,
        0b0000000001100100,
        0b1110010011010000,
        0b0000000000010010,
        0b1110001100000001,
        0b0000000000010000,
        0b1111110000010000,
        0b0000000000010001,
        0b1111000010001000,
        0b0000000000010000,
        0b1111110111001000,
        0b0000000000000100,
        0b1110101010000111,
        0b0000000000010010,
        0b1110101010000111,
    ]

    sum100_1 = [
        0b0000000000010000,
        0b1110111111001000,
        0b0000000000010001,
        0b1110101010001000,
        0b0000000000010000,
        0b1111110000010000,
        0b0000000000000000,
        0b1111010011010000,
        0b0000000000010010,
        0b1110001100000001,
        0b0000000000010000,
        0b1111110000010000,
        0b0000000000010001,
        0b1111000010001000,
        0b0000000000010000,
        0b1111110111001000,
        0b0000000000000100,
        0b1110101010000111,
        0b0000000000010001,
        0b1111110000010000,
        0b0000000000000001,
        0b1110001100001000,
        0b0000000000010110,
        0b1110101010000111
    ]

    for idx, ir in enumerate(sum100_0):
        m = to_machine_number(ir)
        print(idx, '\t', decode_ir(m))


if __name__ == '__main__':
    _show_num_convert()
    _show_decode()
