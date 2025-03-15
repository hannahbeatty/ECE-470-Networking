'''
Created on Feb 11, 2025

@author: nigel
'''

import socket
from project1.csmessage import CSmessage

class CSpdu(object):
    '''
    classdocs
    '''

    def __init__(self, comm: socket):
        '''
        Constructor
        '''
        self._sock = comm
        
    def _loopRecv(self, size: int):
        data = bytearray(b" "*size)
        mv = memoryview(data)
        while size:
            rsize = self._sock.recv_into(mv,size)
            mv = mv[rsize:]
            size -= rsize
        return data
    
    def sendMessage(self, mess: CSmessage):
        mdata = mess.marshal()
        size = len(mdata)
        sdata = '{:04}{}'.format(size,mdata)
        self._sock.sendall(sdata.encode('utf-8'))
        
    def recvMessage(self) -> CSmessage:
        try:
            m = CSmessage()
            size = int(self._loopRecv(4).decode('utf-8'))
            params = self._loopRecv(size).decode('utf-8')
            m.unmarshal(params)
        except Exception:
            raise Exception('bad getMessage')
        else:
            return m
    
    def close(self):
        self._sock.close()
        