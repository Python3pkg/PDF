"""
Utility functions for PDF library.
"""

import io

#custom implementation of warnings.formatwarning
def _formatwarning(message, category, filename, lineno, line=None):
    file = filename.replace("/","\\").rsplit("\\",1)[1] # find the file name
    return "%s: %s [%s:%s]\n" % (category.__name__, message, file, lineno)

def readUntilWhitespace(stream, maxchars=None):
    """
    Reads non-whitespace characters and returns them.
    Stops upon encountering whitespace or when maxchars is reached.
    """
    txt = b_("")
    while True:
        tok = stream.read(1)
        if tok.isspace() or not tok:
            break
        txt += tok
        if len(txt) == maxchars:
            break
    return txt

def readNonWhitespace(stream):
    """
    Finds and reads the next non-whitespace character (ignores whitespace).
    """
    tok = b_(' ')
    while tok == b_('\n') or tok == b_('\r') or tok == b_(' ') or tok == b_('\t'):
        tok = stream.read(1)
    return tok

def skipOverWhitespace(stream):
    """
    Similar to readNonWhitespace, but returns a Boolean if more than
    one whitespace character was read.
    """
    tok = b_(' ')
    cnt = 0
    while tok == b_('\n') or tok == b_('\r') or tok == b_(' ') or tok == b_('\t'):
        tok = stream.read(1)
        cnt+=1
    return (cnt > 1)

def skipOverComment(stream):
    tok = stream.read(1)
    stream.seek(-1, 1)
    if tok == b_('%'):
        while tok not in (b_('\n'), b_('\r')):
            tok = stream.read(1)

class ConvertFunctionsToVirtualList(object):
    def __init__(self, lengthFunction, getFunction):
        self.lengthFunction = lengthFunction
        self.getFunction = getFunction

    def __len__(self):
        return self.lengthFunction()

    def __getitem__(self, index):
        if not isinstance(index, int):
            raise TypeError("sequence indices must be integers")
        len_self = len(self)
        if index < 0:
            # support negative indexes
            index = len_self + index
        if index < 0 or index >= len_self:
            raise IndexError("sequence index out of range")
        return self.getFunction(index)

def RC4_encrypt(key, plaintext):
    S = [i for i in range(256)]
    j = 0
    for i in range(256):
        j = (j + S[i] + ord_(key[i % len(key)])) % 256
        S[i], S[j] = S[j], S[i]
    i, j = 0, 0
    retval = b_("")
    for x in range(len(plaintext)):
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        t = S[(S[i] + S[j]) % 256]
        retval += b_(chr(ord_(plaintext[x]) ^ t))
    return retval

def matrixMultiply(a, b):
    return [[sum([float(i)*float(j)
                  for i, j in zip(row, col)]
                 ) for col in zip(*b)]
            for row in a]

def markLocation(stream):
    """Creates text file showing current location in context."""
    # Mainly for debugging
    RADIUS = 5000
    stream.seek(-RADIUS, 1)
    outputDoc = open('PyPDF2_pdfLocation.txt', 'w')
    outputDoc.write(stream.read(RADIUS))
    outputDoc.write('HERE')
    outputDoc.write(stream.read(RADIUS))
    outputDoc.close()
    stream.seek(-RADIUS, 1)

class PyPdfError(Exception):
    pass

class PdfReadError(PyPdfError):
    pass

class PageSizeNotDefinedError(PyPdfError):
    pass

class PdfReadWarning(UserWarning):
    pass

class PdfStreamError(PdfReadError):
    pass

def hexStr(num):
    return hex(num).replace('L','')

import sys
if sys.version_info[0] < 3:
    def b_(s):
        return s

    def u_(s):
        return str(s, 'unicode_escape')

    def str_(b):
        return str(b)

    def ord_(b):
        return ord(b)

    def chr_(c):
        return c

    def barray(b):
        return b

    def hexencode(b):
        return b.encode('hex')

    string_type = str
    bytes_type = str

    def is_file(ob):
        return isinstance(ob, file)

else:
    def b_(s):
        return s.encode('latin-1')

    def u_(s):
        return s

    def str_(b):
        return b.decode('latin-1')

    def ord_(b):
        return b

    def chr_(c):
        return chr(c)

    def barray(b):
        return bytearray(b)

    def hexencode(b):
        import codecs
        coder = codecs.getencoder('hex_codec')
        return coder(b)[0]

    string_type = str
    bytes_type = bytes

    def is_file(ob):
        return isinstance(ob, io.IOBase)
