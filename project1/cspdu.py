'''
Created on Feb 15, 2025
@author: hannahbeatty
(forked from nigel)
'''

import socket
from csmessage import CSmessage

class CSpdu:
    def __init__(self, comm: socket.socket):
        """
        Initialize a PDU handler with a socket connection.
        """
        self._sock = comm

    def _loopRecv(self, size: int):
        """
        Ensure full reception of a message of given size.
        """
        data = bytearray(size)
        mv = memoryview(data)
        while size:
            rsize = self._sock.recv_into(mv, size)
            if rsize == 0:
                raise ConnectionError("Socket closed unexpectedly")
            mv = mv[rsize:]
            size -= rsize
        return data

    def sendMessage(self, mess: CSmessage):
        """
        Send a CSmessage over the socket.
        """
        mess.validate()  # Ensure message is well-formed
        mdata = mess.marshal()
        size = len(mdata)
        sdata = '{:04}{}'.format(size, mdata)
        
        try:
            self._sock.sendall(sdata.encode('utf-8'))
        except Exception as e:
            raise ConnectionError(f"Failed to send message: {e}")

    def recvMessage(self) -> CSmessage:
        """
        Receive a CSmessage from the socket.
        """
        try:
            size = int(self._loopRecv(4).decode('utf-8'))
            params = self._loopRecv(size).decode('utf-8')
            m = CSmessage()
            m.unmarshal(params)
            return m
        except Exception as e:
            raise ConnectionError(f"Failed to receive message: {e}")

    def close(self):
        """
        Close the socket connection.
        """
        self._sock.close()
