BITS = 8

def bitsToArray(bits):
    array = [False]*BITS
    for k in range(min(BITS, len(bits))):
        array[k] = bits[-1-k] == "1"
    return array

def arrayToBits(array):
    bits = ""
    for k in range(BITS):
        bits += "1" if array[-1-k] else "0"
    return bits

def arrayToInt(array):
    integer = 0
    for k, bit in enumerate(array):
        integer += 2**k if bit else 0
    return integer

class Register:
    def __init__(self):
        self.data = [None]*BITS
    def loadData(self, data):
        self.data = data
    def getData(self):
        return self.data

class RAM:
    def __init__(self, size=2**(BITS/2)):
        self.data = [[None]*BITS for k in range(size)]
    def setData(self, data, address):
        self.data[arrayToInt(address)] = data
    def getData(self, address):
        return self.data[arrayToInt(address)]

class Decoder:
    def __init__(self):
        pass

class ALU:
    def __init__(self, inputA, inputB):
        self.inputA = inputA
        self.inputB = inputB
    def getData(self, substract=False):
        dataA = self.inputA.getData()
        dataB = self.inputB.getData()
        output = [None]*BITS
        carry = substract
        for k in range(BITS):
            bitA = dataA[k]
            bitB = (substract != dataB[k])
            output[k] = (bitA != bitB) != carry
            carry = (carry and bitA) or (carry and bitB) or (bitA and bitB)
        return output

registerA = Register()
registerB = Register()
alu = ALU(registerA, registerB)
ram = RAM()
