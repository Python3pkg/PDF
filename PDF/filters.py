"""
Implementation of stream filters for PDF.
"""

import io

from .utils import PdfReadError

try:
    import zlib
    def decompress(data):
        return zlib.decompress(data)
    def compress(data):
        return zlib.compress(data)
except ImportError:
    # Unable to import zlib.  Attempt to use the System.IO.Compression
    # library from the .NET framework. (IronPython only)
    import System
    from System import IO, Collections, Array
    def _string_to_bytearr(buf):
        retval = Array.CreateInstance(System.Byte, len(buf))
        for i in range(len(buf)):
            retval[i] = ord(buf[i])
        return retval
    def _bytearr_to_string(bytes):
        retval = ""
        for i in range(bytes.Length):
            retval += chr(bytes[i])
        return retval
    def _read_bytes(stream):
        ms = IO.MemoryStream()
        buf = Array.CreateInstance(System.Byte, 2048)
        while True:
            bytes = stream.Read(buf, 0, buf.Length)
            if bytes == 0:
                break
            else:
                ms.Write(buf, 0, bytes)
        retval = ms.ToArray()
        ms.Close()
        return retval
    def decompress(data):
        bytes = _string_to_bytearr(data)
        ms = IO.MemoryStream()
        ms.Write(bytes, 0, bytes.Length)
        ms.Position = 0  # fseek 0
        gz = IO.Compression.DeflateStream(ms, IO.Compression.CompressionMode.Decompress)
        bytes = _read_bytes(gz)
        retval = _bytearr_to_string(bytes)
        gz.Close()
        return retval
    def compress(data):
        bytes = _string_to_bytearr(data)
        ms = IO.MemoryStream()
        gz = IO.Compression.DeflateStream(ms, IO.Compression.CompressionMode.Compress, True)
        gz.Write(bytes, 0, bytes.Length)
        gz.Close()
        ms.Position = 0 # fseek 0
        bytes = ms.ToArray()
        retval = _bytearr_to_string(bytes)
        ms.Close()
        return retval


class FlateDecode(object):
    def decode(data, decodeParms):
        data = decompress(data)
        predictor = 1
        if decodeParms:
            try:
                predictor = decodeParms.get("/Predictor", 1)
            except AttributeError:
                pass    # usually an array with a null object was read

        # predictor 1 == no predictor
        if predictor != 1:
            columns = decodeParms["/Columns"]
            # PNG prediction:
            if predictor >= 10 and predictor <= 15:
                output = io.BytesIO()
                # PNG prediction can vary from row to row
                rowlength = columns + 1
                assert len(data) % rowlength == 0
                prev_rowdata = (0,) * rowlength
                for row in range(len(data) / rowlength):
                    rowdata = [ord(x) for x in data[(row*rowlength):((row+1)*rowlength)]]
                    filterByte = rowdata[0]
                    if filterByte == 0:
                        pass
                    elif filterByte == 1:
                        for i in range(2, rowlength):
                            rowdata[i] = (rowdata[i] + rowdata[i-1]) % 256
                    elif filterByte == 2:
                        for i in range(1, rowlength):
                            rowdata[i] = (rowdata[i] + prev_rowdata[i]) % 256
                    else:
                        # unsupported PNG filter
                        raise PdfReadError("Unsupported PNG filter %r" % filterByte)
                    prev_rowdata = rowdata
                    output.write(''.join([chr(x) for x in rowdata[1:]]))
                data = output.getvalue()
            else:
                # unsupported predictor
                raise PdfReadError("Unsupported flatedecode predictor %r" % predictor)
        return data
    decode = staticmethod(decode)

    def encode(data):
        return compress(data)
    encode = staticmethod(encode)

class ASCIIHexDecode(object):
    def decode(data, decodeParms=None):
        retval = ""
        char = ""
        x = 0
        while True:
            c = data[x]
            if c == ">":
                break
            elif c.isspace():
                x += 1
                continue
            char += c
            if len(char) == 2:
                retval += chr(int(char, base=16))
                char = ""
            x += 1
        assert char == ""
        return retval
    decode = staticmethod(decode)

class LZWDecode(object):
    """Taken from:
    http://www.java2s.com/Open-Source/Java-Document/PDF/PDF-Renderer/com/sun/pdfview/decode/LZWDecode.java.htm
    """
    class decoder(object):
        def __init__(self,data):
            self.STOP=257
            self.CLEARDICT=256
            self.data=data
            self.bytepos=0
            self.bitpos=0
            self.dict=[""]*4096
            for i in range(256):
                self.dict[i]=chr(i)
            self.resetDict()

        def resetDict(self):
            self.dictlen=258
            self.bitspercode=9


        def nextCode(self):
            fillbits=self.bitspercode
            value=0
            while fillbits>0 :
                if self.bytepos >= len(self.data):
                    return -1
                nextbits=ord(self.data[self.bytepos])
                bitsfromhere=8-self.bitpos
                if bitsfromhere>fillbits:
                    bitsfromhere=fillbits
                value |= (((nextbits >> (8-self.bitpos-bitsfromhere)) &
                           (0xff >> (8-bitsfromhere))) <<
                          (fillbits-bitsfromhere))
                fillbits -= bitsfromhere
                self.bitpos += bitsfromhere
                if self.bitpos >=8:
                    self.bitpos=0
                    self.bytepos = self.bytepos+1
            return value

        def decode(self):
            """ algorithm derived from:
            http://www.rasip.fer.hr/research/compress/algorithms/fund/lz/lzw.html
            and the PDFReference
            """
            cW = self.CLEARDICT;
            baos=""
            while True:
                pW = cW;
                cW = self.nextCode();
                if cW == -1:
                    raise PdfReadError("Missed the stop code in LZWDecode!")
                if cW == self.STOP:
                    break;
                elif cW == self.CLEARDICT:
                    self.resetDict();
                elif pW == self.CLEARDICT:
                    baos+=self.dict[cW]
                else:
                    if cW < self.dictlen:
                        baos += self.dict[cW]
                        p=self.dict[pW]+self.dict[cW][0]
                        self.dict[self.dictlen]=p
                        self.dictlen+=1
                    else:
                        p=self.dict[pW]+self.dict[pW][0]
                        baos+=p
                        self.dict[self.dictlen] = p;
                        self.dictlen+=1
                    if (self.dictlen >= (1 << self.bitspercode) - 1 and
                        self.bitspercode < 12):
                        self.bitspercode+=1
            return baos



    @staticmethod
    def decode(data,decodeParams=None):
        return LZWDecode.decoder(data).decode()

class ASCII85Decode(object):
    def decode(data, decodeParms=None):
        retval = ""
        group = []
        x = 0
        hitEod = False
        # remove all whitespace from data
        data = [y for y in data if not (y in ' \n\r\t')]
        while not hitEod:
            c = data[x]
            if len(retval) == 0 and c == "<" and data[x+1] == "~":
                x += 2
                continue
            #elif c.isspace():
            #    x += 1
            #    continue
            elif c == 'z':
                assert len(group) == 0
                retval += '\x00\x00\x00\x00'
                continue
            elif c == "~" and data[x+1] == ">":
                if len(group) != 0:
                    # cannot have a final group of just 1 char
                    assert len(group) > 1
                    cnt = len(group) - 1
                    group += [ 85, 85, 85 ]
                    hitEod = cnt
                else:
                    break
            else:
                c = ord(c) - 33
                assert c >= 0 and c < 85
                group += [ c ]
            if len(group) >= 5:
                b = group[0] * (85**4) + \
                    group[1] * (85**3) + \
                    group[2] * (85**2) + \
                    group[3] * 85 + \
                    group[4]
                assert b < (2**32 - 1)
                c4 = chr((b >> 0) % 256)
                c3 = chr((b >> 8) % 256)
                c2 = chr((b >> 16) % 256)
                c1 = chr(b >> 24)
                retval += (c1 + c2 + c3 + c4)
                if hitEod:
                    retval = retval[:-4+hitEod]
                group = []
            x += 1
        return retval
    decode = staticmethod(decode)

def decodeStreamData(stream):
    from generic import NameObject
    filters = stream.get("/Filter", ())
    if len(filters) and not isinstance(filters[0], NameObject):
        # we have a single filter instance
        filters = (filters,)
    data = stream._data
    for filterType in filters:
        if filterType == "/FlateDecode":
            data = FlateDecode.decode(data, stream.get("/DecodeParms"))
        elif filterType == "/ASCIIHexDecode":
            data = ASCIIHexDecode.decode(data)
        elif filterType == "/LZWDecode":
            data = LZWDecode.decode(data, stream.get("/DecodeParms"))
        elif filterType == "/ASCII85Decode":
            data = ASCII85Decode.decode(data)
        elif filterType == "/Crypt":
            decodeParams = stream.get("/DecodeParams", {})
            if "/Name" not in decodeParams and "/Type" not in decodeParams:
                pass
            else:
                raise NotImplementedError("/Crypt filter with /Name or /Type not supported yet")
        else:
            # unsupported filter
            raise NotImplementedError("unsupported filter %s" % filterType)
    return data
