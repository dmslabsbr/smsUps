def twos_comp(val, bits):
    """compute the 2's complement of int value val"""
    if (val & (1 << (bits - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)        # compute negative value
    return val 


def twos_complement(n, w=32):
    if n & (1 << (w - 1)): n = n - (1 << w)
    return n

def calc_checksum(s):
    sum = 0
    for c in s:
        sum += ord(c)
    sum = sum % 256
    return '%2X' % (sum & 0xFF)


def calc1(s):
    """
    Calculates checksum for sending commands to the ELKM1.
    Sums the ASCII character values mod256 and returns
    the lower byte of the two's complement of that value.
    """
    return '%2X' % (-(sum(ord(c) for c in s) % 256) & 0xFF)





print (c2('ff ff ff ff 00'))
print (c2('54 00 64 00 00'))
print (c2('54 00 c8 00 00'))
print (c2('54 01 2C 00 00'))
print (c2('54 03 84 00 00'))
