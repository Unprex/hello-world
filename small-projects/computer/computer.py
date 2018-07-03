"""
Simulation of a computer.

@file computer.py
@author Unprex
"""

BITS = 8


def bitsToArray(bits):
    """Translates a byte string to a data array"""
    size = len(bits)
    array = [False] * size
    for k in range(size):
        array[k] = bits[-1 - k] == "1"
    return array


def arrayToBits(array):
    """Translates a data array to a byte string"""
    size = len(array)
    bits = ""
    for k in range(size):
        bits += "1" if array[-1 - k] else "0"
    return bits


def arrayToInt(array):
    """Translates a data array to an integer"""
    integer = 0
    for k, bit in enumerate(array):
        integer += 2**k if bit else 0
    return integer


def fitArray(array, newArray, default=False):
    """Fits an array into another one"""
    size = len(array)
    for k in range(len(newArray)):
        if k < size:
            newArray[k] = array[k]
        else:
            newArray[k] = default


class Register:
    """Temporarily stores a data array until needed"""

    def __init__(self, inBUS, outBUS, size=BITS):
        self.data = [False] * size
        self.inBUS = inBUS
        self.outBUS = outBUS
        self.size = size

    def In(self):
        fitArray(self.inBUS, self.data)

    def Out(self):
        fitArray(self.data, self.outBUS)


class ProgramCounter(Register):
    """Count the number of steps the program has executed"""

    def __init__(self, BUS, size=(BITS // 2)):
        Register.__init__(self, BUS, BUS, size)

    def Enable(self):  # Increment counter
        carry, k = True, 0
        while k < self.size and carry:
            diff = carry == self.data[k]
            self.data[k], carry = not diff, diff  # XOR, NXOR
            k += 1


class InstructionRegister(Register):

    def __init__(self, BUS, instr, instrSize,
                 sizeData=BITS, sizeAddress=(BITS // 2)):
        self.BUS = BUS
        self.instr = instr
        Register.__init__(self, BUS, BUS, sizeData)
        self.sizeAddress = sizeAddress
        self.instrSize = instrSize

    def Out(self):
        fitArray(self.data[:self.sizeAddress], self.outBUS)

    def setFonctions(self, fonct):
        self.fonct = fonct

    def update(self):
        for k in range(self.instrSize):
            operation = arrayToInt(self.data[-self.sizeAddress:])
            for i in self.instr[8 * operation + k]:
                self.fonct[i]()


class RAM(Register):
    """Storage and recovery of "size" data arrays"""

    def __init__(self, BUS, sizeData=BITS, sizeAddress=(BITS // 2)):
        self.memory = [[False] * sizeData for _ in range(2**sizeAddress)]
        self.address = [False] * sizeAddress
        Register.__init__(self, BUS, BUS, sizeData)

    def MemaIn(self):  # Sets address
        fitArray(self.outBUS, self.address)
        self.data = self.memory[arrayToInt(self.address)]

    def setData(self, address, data):  # Sets address
        self.memory[arrayToInt(address)] = data


class ALU(Register):
    """Arithmetic and logic unit: Adds or subtracts its inputs"""

    def __init__(self, BUS, size=BITS):
        self.A = Register(BUS, BUS, size)
        self.B = Register(BUS, BUS, size)
        Register.__init__(self, BUS, BUS, size)
        self.BUS = BUS
        self.size = size

    def Out(self, substract=False):
        carry = substract
        for k in range(self.size):
            bitA = self.A.data[k]
            bitB = substract != self.B.data[k]  # XOR gate
            self.data[k] = (bitA != bitB) != carry
            carry = (carry and bitA) or (carry and bitB) or (bitA and bitB)
        fitArray(self.data, self.BUS)


class Clock:
    def __init__(self, halt=False):
        self.halt = halt

    def Halt(self):
        self.halt = True

    def running(self):
        return not self.halt


class Output(Register):
    def In(self):
        fitArray(self.inBUS, self.data)
        print(arrayToInt(self.data))


if __name__ == "__main__":  # Example code
    # Define a set of instructions (Carefull with in/out priority)
    instr = [[]] * 2**8  # 1*CF 4*Op 3*Step
    for k in range(0, 249, 8):  # 00000XXX -> 11111XXX
        instr[k] = [13, 1]  # CO MI
        instr[k + 1] = [3, 5, 12]  # RO II CE
        operation = (k // 8) % 16
        if operation == 1:  # X0001XXX (LDA)
            instr[k + 2] = [4, 1]  # IO MI
            instr[k + 3] = [3, 6]  # RO AI
        elif operation == 2:  # X0010XXX (ADD)
            instr[k + 2] = [4, 1]  # IO MI
            instr[k + 3] = [3, 10]  # RO BI
            instr[k + 4] = [8, 6]  # SO AI
        elif operation == 14:  # X1110XXX (OUT)
            instr[k + 2] = [7, 11]  # AO OI
        elif operation == 15:  # X1111XXX (HLT)
            instr[k + 2] = [0]  # HLT

    # Set-up components
    BUS = [False] * BITS  # Initialize BUS
    clk = Clock()
    out = Output(BUS, BUS)
    cnt = ProgramCounter(BUS)
    alu = ALU(BUS)
    ram = RAM(BUS)
    ins = InstructionRegister(BUS, instr, 5)  # 5 < 8 = 2**3
    ins.setFonctions([
        clk.Halt, ram.MemaIn, ram.In, ram.Out,
        ins.Out, ins.In, alu.A.In, alu.A.Out,
        alu.Out, lambda: alu.Out(True), alu.B.In, out.In,
        cnt.Enable, cnt.Out, cnt.In, lambda: None])

    # Initialize RAM with addition code
    ram.setData(bitsToArray("0000"), bitsToArray("00011110"))  # LDA 14
    ram.setData(bitsToArray("0001"), bitsToArray("00101111"))  # ADD 15
    ram.setData(bitsToArray("0010"), bitsToArray("11100000"))  # OUT
    ram.setData(bitsToArray("0011"), bitsToArray("11110000"))  # HLT

    # Initialize RAM with 13 and 6 at address 14 and 15
    ram.setData(bitsToArray("1110"), bitsToArray("00001101"))
    ram.setData(bitsToArray("1111"), bitsToArray("00000110"))

    # Run computer
    while clk.running():
        ins.update()
