'''
Created on Feb 11, 2025

@author: nigel
'''
import socket
from project1.csmessage import CSmessage, REQS
from project1.cspdu import CSpdu

if __name__ == '__main__':
    
    # test messages
    mess1 = CSmessage()
    print(mess1)
    mess1.addValue('key1', 'value1')
    mess1.addValue('key2', 'value2')
    mess1.addValue('key3', 'value3')
    mess1.addValue('key5', 'value5')
    print(mess1)
    print(type(mess1.getType()))
    print(mess1.getValue('key1'))
    
    mess2 = CSmessage()
    print(mess2)
    mess2.unmarshal(mess1.marshal())
    print(mess2)
    
    if mess1.getType() == REQS.LGIN:
        print('Login')
    else:
        print('Not Login')
    
    # test PDU
    sock = socket.socket()
    sock.connect(('localhost',50000))
    pdu = CSpdu(sock)
    pdu.sendMessage(mess1)
    mess3 = pdu.recvMessage()
    print(mess3)
    pdu.close()
    
    