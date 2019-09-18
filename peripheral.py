class MemoryMappedDevice:
    def __init__(self, memory):
        self.memory = memory


class Screen(MemoryMappedDevice):
    def __init__(self, memory):
        super().__init__(memory)


class Keyboard(MemoryMappedDevice):
    def __init__(self, memory):
        super().__init__(memory)
