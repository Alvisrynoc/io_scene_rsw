import io
import os
import struct


class BinaryFileReader(object):
    def __init__(self, file):
        self.file = file

    def tell(self):
        return self.file.tell()
    
    def read_s(self, fmt):
        size = struct.calcsize(fmt)
        buffer = self.file.read(size)
        return struct.unpack(fmt, buffer)[0]

    def read(self, fmt):
        size = struct.calcsize(fmt)
        buffer = self.file.read(size)
        return struct.unpack(fmt, buffer)

    def read_fixed_length_null_terminated_string(self, n=40, encoding='euc-kr'):
        buf = bytearray()
        for i in range(n):
            c = self.file.read(1)[0]
            if c == 0:
                self.file.seek(n - i - 1, os.SEEK_CUR)
                break
            buf.append(c)
        try:
            return buf.decode(encoding)
        except UnicodeDecodeError as e:
            print(buf)
            raise e
