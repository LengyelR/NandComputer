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


if __name__ == '__main__':
    def show(num):
        mi = to_machine_number(num)
        integer = to_integer(mi)
        print(integer, mi)

    for i in range(10):
        show(i)
    show(2**10)
    show(2**13+64)
    show(2**15-1)
    show(2**15)

    show(2**16-1)
    show(-1)
    show(-3)
    show(-18)
