from __future__ import annotations
import io
from enum import Enum
from typing import Tuple, Union

class OpenMode(Enum):
    RDONLY = 'rb'
    WRONLY = 'wb'
    RDWR = 'rb+' # read and write (file must be exist)
    WRRD = 'wb+' # write and read (file will be clear in open)
    APPEND = 'ab+' # append and read

    def __str__(self):
        return self.value
    
    def is_readable(self)->bool:
        return self in (OpenMode.RDONLY, OpenMode.RDWR, OpenMode.WRRD, OpenMode.APPEND)
    
    def is_writable(self)->bool:
        return self in (OpenMode.WRONLY, OpenMode.RDWR, OpenMode.WRRD, OpenMode.APPEND)

_PathPair = Tuple[str, str] # read_path write_path
_PathMode = Tuple[str, OpenMode]
_PathPairMode = Tuple[str, str, OpenMode]

def _checkPathArgs(pth:Union[_PathPair, _PathMode])->Union[_PathPair, _PathPairMode, None]:
    __pthpair = None
    if(isinstance(pth, str)):
        __pthpair = (pth, pth)
    elif(isinstance(pth, (list, tuple)) and len(pth) == 2):
        if(isinstance(pth[0], str) and isinstance(pth[1], str)):
            __pthpair = (pth[0], pth[1])
        elif(isinstance(pth[0], str) and isinstance(pth[1], OpenMode)):
            __pthpair = (pth[0], pth[0], pth[1])
    return __pthpair

class Comm:
    __reader:io.BufferedReader
    __writer:io.BufferedWriter

    def __init__(self, rmode:OpenMode=OpenMode.RDONLY, wmode:OpenMode=OpenMode.WRONLY):
        self.__rmode:OpenMode = rmode
        self.__wmode:OpenMode = wmode
        self.__reader:io.BufferedReader = None
        self.__writer:io.BufferedWriter = None
    
    def isclosed(self)->bool:
        if(self.__rmode.is_readable() and self.__reader is None):
            return True
        if(self.__wmode.is_writable() and self.__writer is None):
            return True
        return False
    
    def isopen(self)->bool:
        return not self.isclosed()
    
    # open reader writter
    def open(self, pthargs:Union[_PathPair, str, _PathMode])->Comm:
        self.close()
        __pthpair = _checkPathArgs(pthargs)
        if(__pthpair is None):
            raise IOError('pthargs must be (pathstr, pathstr) or pathstr or (pathstr, mode)')
        if(len(__pthpair) == 3):
            self.__rmode = __pthpair[2]
            self.__wmode = __pthpair[2]
        if(self.__rmode.is_readable()):
            self.__reader = open(__pthpair[0], f'{self.__rmode}')
        if(self.__wmode.is_writable()):
            self.__writer = open(__pthpair[1], f'{self.__wmode}')
        if(self.isclosed()):
            raise IOError('Can not open file io! check file path')
        return self

    def close(self)->bool:
        if(not self.isclosed()):
            if(self.__reader is not None):
                try:
                    self.__reader.close()
                finally:
                    self.__reader = None
            if(self.__writer is not None):
                try:
                    self.__writer.close()
                finally:
                    self.__writer = None
        return True

    def read(self, size:int, timeout:float=None)->bytes:
        if(self.isclosed()):
            raise IOError('reader is close!')
        if(not self.__rmode.is_readable() or not self.__reader.readable()):
            print('reader is not readable!')
            return b''
        return self.__reader.read(size)

    def write(self, data:bytes, timeout:float=None)->int:
        if(self.isclosed()):
            raise IOError('writter is close!')
        if(not self.__wmode.is_writable() or not self.__writer.writable()):
            print('writter is not writable!')
            return 0
        len = self.__writer.write(data)
        self.__writer.flush()
        return len

def main():
    comm = Comm()
    try:
        comm.open(('/tmp/rawports/rfile', '/tmp/rawports/wfile'))
        comm.write(b'fileio message!')
        print(comm.read(32))
    except Exception as e:
        print(f'Exception:{e} ')
    finally:
        comm.close()

if __name__ == '__main__':
    main()