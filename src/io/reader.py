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
    
    def read_str(self, encoding='euc-kr'):
        length = self.read_s('I')
        print(length)
        if length <= 0:
            return ''
        return self.read_s(f'{length}c').decode(encoding)
    
    def read_x(self, x, encoding='euc-kr'):
        buffer = self.file.read(x)
        return struct.unpack('40s', buffer)[0].decode(encoding)
    
    def read_fixed_str(self, q, encoding='euc-kr'):
        s = self.read_s(f'40s')
        print(s)
        return s.decode(encoding)

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
