from __future__ import annotations
import os, sys
from typing import Tuple, Union

_PathPair = Tuple[str, str] # read_path write_path
_PathMode = Tuple[str, int]
_PathPairMode = Tuple[str, str, int]

def _checkPathArgs(pthargs:Union[_PathPair, str, _PathMode])->Union[_PathPair, _PathPairMode, None]:
    __pthpair = None
    if(isinstance(pthargs, str)):
        __pthpair = (pthargs, pthargs)
    elif(isinstance(pthargs, (list, tuple)) and len(pthargs) == 2):
        if(isinstance(pthargs[0], str) and isinstance(pthargs[1], str)):
            __pthpair = (pthargs[0], pthargs[1])
        elif(isinstance(pthargs[0], str) and isinstance(pthargs[1], int)):
            __pthpair = (pthargs[0], pthargs[0], pthargs[1])
    return __pthpair

def _is_readable(mode:int):
    mode = mode & (os.O_RDONLY | os.O_WRONLY | os.O_RDWR)
    return mode in (os.O_RDONLY, os.O_RDWR)

def _is_writable(mode:int):
    mode = mode & (os.O_RDONLY | os.O_WRONLY | os.O_RDWR)
    return mode in (os.O_WRONLY, os.O_RDWR)

class Comm:
    __fd_read:int
    __fd_write:int

    def __init__(self, rmode:int=os.O_RDONLY, wmode:int=os.O_WRONLY):
        self.__rmode:int = rmode
        self.__wmode:int = wmode
        self.__fd_read = -1
        self.__fd_write = -1
    
    def isclosed(self)->bool:
        if(_is_readable(self.__rmode) and self.__fd_read == -1):
            return True
        if(_is_writable(self.__wmode) and self.__fd_write == -1):
            return True
        return False

    def isopen(self)->bool:
        return not self.isclosed()
    
    # open fd_read fd_write
    def open(self, pthargs:Union[_PathPair, str, _PathMode])->Comm:
        self.close()
        __pthpair = _checkPathArgs(pthargs)
        if(__pthpair is None):
            raise IOError('pthargs must be (pathstr, pathstr) or pathstr or (pathstr, mode)')
        if(len(__pthpair) == 3):
            self.__rmode = __pthpair[2]
            self.__wmode = __pthpair[2]
        if(sys.platform == "win32"):
            self.__rmode |= os.O_BINARY
            self.__wmode |= os.O_BINARY
        if(_is_readable(self.__rmode)):
            self.__fd_read = os.open(__pthpair[0], self.__rmode)
        if(_is_writable(self.__wmode)):
            self.__fd_write = os.open(__pthpair[1], self.__wmode)
        if(self.isclosed()):
            raise IOError('Can not open file descriptor! check file path')
        return self

    def close(self)->bool:
        if(not self.isclosed()):
            if(self.__fd_read != -1):
                try:
                    os.close(self.__fd_read)
                finally:
                    self.__fd_read = -1
            if(self.__fd_write != -1):
                try:
                    os.close(self.__fd_write)
                finally:
                    self.__fd_write = -1
        return True

    def read(self, size:int, timeout:float=None)->bytes:
        if(self.isclosed()):
            raise IOError('read file descriptor is close!')
        if(not _is_readable(self.__rmode)):
            print('read file descriptor is not readable!')
            return b''
        return os.read(self.__fd_read, size)

    def write(self, data:bytes, timeout:float=None)->int:
        if(self.isclosed()):
            raise IOError('write file descriptor is close!')
        if(not _is_writable(self.__wmode)):
            print('write file descriptor is not writable!')
            return 0
        return os.write(self.__fd_write, data)

def main():
    comm = Comm()
    try:
        comm.open(('/tmp/rawports/rfile', '/tmp/rawports/wfile'))
        comm.write(b'fd message!')
        print(comm.read(32))
    except Exception as e:
        print(f'Exception:{e} ')
    finally:
        comm.close()

if __name__ == '__main__':
    main()