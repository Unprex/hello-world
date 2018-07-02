"""
Simulation of a computer.

@file computer.py
@author Unprex
"""

BITS = 8


def bitsToArray(bits, size=BITS):
    """Translates a byte string to a data array"""
    array = [False] * size
    for k in range(size):
        array[k] = bits[-1 - k] == "1"
    return array


def arrayToBits(array, size=BITS):
    """Translates a data array to a byte string"""
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


def fitArray(array, size):
    """Creates an array of a specific size"""
    newArray = [False] * size
    sizeArray = len(array)
    delta = sizeArray - size
    for k in range(size):
        if k + delta >= 0:
            newArray[k] = array[k + delta]
    return newArray


class Register:
    """Temporarily stores a data array until needed"""

    def __init__(self, inBUS, outBUS, size=BITS):
        self.data = [False] * size
        self.inBUS = inBUS
        self.outBUS = outBUS
        self.size = size

    def registerIn(self):
        self.data = fitArray(self.inBUS, self.size)

    def registerOut(self):
        self.outBUS = fitArray(self.data, len(self.outBUS))


class ProgramCounter:
    """Count the number of steps the program has executed"""

    def __init__(self, BUS, size=(BITS // 2)):
        self.count = [False] * size
        self.input = Register(BUS, self.data, size)
        self.output = Register(self.data, BUS, size)
        self.size = size

    def counterOut(self):
        self.output.registerIn()  # count -> register
        self.output.registerOut()  # register -> BUS

    def counterIn(self):
        self.input.registerIn()  # BUS -> register
        self.input.registerOut()  # register -> count

    def counterStep(self):
        carry, k = True, 0
        while k < self.size and carry:
            diff = carry == self.count[k]
            self.count[k], carry = not diff, diff  # XOR, NXOR
            k += 1


class InstructionRegister:  # TODO

    def __init__(self, BUS):
        self.data = [False] * BITS
        self.BUS = BUS

    def setAddress(self, address):
        self.data = address

    def getData(self):
        return self.data


class RAM:
    """Storage and recovery of "size" data arrays"""

    def __init__(self, BUS, size=(BITS // 2)):
        self.memory = [[False] * BITS for k in range(2**size)]
        self.address = [False] * size
        self.data = [False] * BITS
        self.input = Register(BUS, self.address, size)
        self.output = Register(self.data, BUS, size)
        self.size = size

    def memoryIn(self):
        self.input.registerIn()  # BUS -> register
        self.input.registerOut()  # register -> address

    def RAMout(self):
        self.output.registerIn()  # data -> register
        self.output.registerOut()  # register -> BUS


class ALU:
    """Arithmetic and logic unit: Adds or subtracts its inputs"""

    def __init__(self, BUS, inputA, inputB):
        # "inputA" and "inputB" are registers
        self.inputA = inputA
        self.inputB = inputB
        self.BUS = BUS

    def getData(self, substract=False):
        dataA = self.inputA.getData()
        dataB = self.inputB.getData()
        output = [None] * BITS
        carry = substract
        for k in range(BITS):
            bitA = dataA[k]
            bitB = substract != dataB[k]  # XOR gate
            output[k] = (bitA != bitB) != carry
            carry = (carry and bitA) or (carry and bitB) or (bitA and bitB)
        return output


if __name__ == "__main__":  # Example code (incomplete)
    # Set-up everything
    """
    registerA = Register()
    registerB = Register()
    counter = ProgramCounter()
    alu = ALU(registerA, registerB)
    ram = RAM()
    BUS = [None] * BITS  # Initialise BUS
    counter.loadData(bitsToArray("0000"))  # Set counter to step 0
    # Initialise RAM with 13 and 6 at address 14 and 15
    ram.setData(bitsToArray("00001101"), bitsToArray("1110"))
    ram.setData(bitsToArray("00000110"), bitsToArray("1111"))

    while True:
        # CO MI RO (Counter Out -> Memory In -> RAM Out)
        BUS = ram.getData(counter.getData())
        # II (Instruction register In)
        BUS = ram.getData(counter.getData())
        counter.nextStep()

    # Step 0: Writes "13" from RAM to the BUS
    BUS = ram.getData(bitsToArray("1110"))
    counter.nextStep()
    # Step 1: Load "13" to "registerA"
    registerA.loadData(BUS)  # a = 13
    counter.nextStep()
    # Step 2: Writes "6" from RAM to the BUS
    BUS = ram.getData(bitsToArray("1111"))
    counter.nextStep()
    # Step 3: Load "6" to "registerB"
    registerB.loadData(BUS)  # b = 6
    counter.nextStep()
    # Step 4: Writes a-b = 7 ("00000111") to the BUS
    BUS = alu.getData(True)  # "True" for subtractions
    counter.nextStep()
    # Output
    print(arrayToBits(BUS))  # Prints BUS content
    print(arrayToBits(counter.getData()))  # Prints the number of steps
    """
