BITS = 8

def bitsToArray(bits):
    """Translates a byte string to a data array"""
    array = [False]*BITS
    for k in range(min(BITS, len(bits))):
        array[k] = bits[-1-k] == "1"
    return array

def arrayToBits(array):
    """Translates a data array to a byte string"""
    bits = ""
    for k in range(BITS):
        bits += "1" if array[-1-k] else "0"
    return bits

def arrayToInt(array):
    """Translates a data array to an integer"""
    integer = 0
    for k, bit in enumerate(array):
        integer += 2**k if bit else 0
    return integer

class Register:
    """Temporarily stores a data array until needed"""
    def __init__(self):
        self.data = [None]*BITS
    def loadData(self, data):
        self.data = data
    def getData(self):
        return self.data

class ProgramCounter(Register):
    """Count the number of steps the program has executed"""
    def nextStep(self):
        carry, k = True, 0
        while k < BITS and carry:
            diff = carry == self.data[k]
            self.data[k], carry = not diff, diff # XOR, NXOR
            k += 1

class RAM:
    """Storage and recovery of "size" data arrays"""
    def __init__(self, size=2**(BITS//2)):
        self.data = [[None]*BITS for k in range(size)]
    def setData(self, data, address): # Address as a data array
        self.data[arrayToInt(address)] = data
    def getData(self, address):
        return self.data[arrayToInt(address)]

class Decoder: # TODO
    def __init__(self):
        pass

class ALU:
    """Arithmetic and logic unit: Adds or subtracts its inputs"""
    def __init__(self, inputA, inputB):
        # "inputA" and "inputB" are registers
        self.inputA = inputA
        self.inputB = inputB
    def getData(self, substract=False):
        dataA = self.inputA.getData()
        dataB = self.inputB.getData()
        output = [None]*BITS
        carry = substract
        for k in range(BITS):
            bitA = dataA[k]
            bitB = substract != dataB[k] # XOR gate
            output[k] = (bitA != bitB) != carry
            carry = (carry and bitA) or (carry and bitB) or (bitA and bitB)
        return output

if __name__ == "__main__": # Example code (incomplete)
    # Set-up everything
    registerA = Register()
    registerB = Register()
    counter = ProgramCounter()
    alu = ALU(registerA, registerB)
    ram = RAM()
    BUS = [None]*BITS # Initialise BUS
    counter.loadData(bitsToArray("0000")) # Set counter to step 0
    # Initialise RAM with 13 and 6 at address 0 and 1
    ram.setData(bitsToArray("00001101"), bitsToArray("0000"))
    ram.setData(bitsToArray("00000110"), bitsToArray("0001"))
    # Step 0: Writes "13" from RAM the BUS
    BUS = ram.getData(bitsToArray("0000"))
    counter.nextStep()
    # Step 1: Load "13" to "registerA"
    registerA.loadData(BUS) # a = 13
    counter.nextStep()
    # Step 2: Writes "6" from RAM to the BUS
    BUS = ram.getData(bitsToArray("0001"))
    counter.nextStep()
    # Step 3: Load "6" to "registerB"
    registerB.loadData(BUS) # b = 6
    counter.nextStep()
    # Step 4: Writes a-b = 7 ("00000111") to the BUS
    BUS = alu.getData(True) # "True" for subtractions
    counter.nextStep()
    # Output
    print(arrayToBits(BUS)) # Prints BUS content
    print(arrayToBits(counter.getData())) # Prints the number of steps

