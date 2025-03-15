'''
Created on Feb 11, 2025

@author: nigel
'''
import socket
from project1.csmessage import CSmessage, REQS
from project1.cspdu import CSpdu
from cstime import CStime
from cscourse import CScourse

if __name__ == '__main__':
    
    print('==========Test Message')
    mess1 = CSmessage()
    print(mess1)
    mess1.addValue('username', 'user1')
    mess1.addValue('password', 'pass1')
    print(mess1)
    print(type(mess1.getType()))
    print(mess1.getValue('username'))
    
    print('==========Test Message -> str -> Message')
    mess2 = CSmessage()
    print(mess2)
    mess2.unmarshal(mess1.marshal())
    print(mess2)

    print('==========Test Message type check')
    if mess1.getType() == REQS.LGIN:
        print('Login')
        resp1 = CSmessage()
        resp1.setType(REQS.MESS)
        resp1.addValue('mess','Success')
        print(resp1)
    else:
        print('Not Login')

    print('==========Test Time')
    t1 = CStime()
    print(t1)
    
    t2 = CStime()
    t2.setTime(12, 30, 13, 45)
    print(t2)
    
    print('==========Test Course - server')
    c1 = CScourse('ECE470','Network Client-Server Programming', 'Programming',t2)
    print(c1)
    
    print('==========Test Course - server -> client')
    mess3 = CSmessage()
    mess3.setType(REQS.MESS)
    mess3.addValue('mess', str(c1))
    print(mess3)
    
    print('==========Test Course - unmarshal on client')
    mess4 = CSmessage()
    mess4.unmarshal(mess3.marshal())
    s1 = mess4.getValue('mess')
    print(s1)
    
    
    '''
    # test PDU
    sock = socket.socket()
    sock.connect(('localhost',50000))
    pdu = CSpdu(sock)
    pdu.sendMessage(mess1)
    mess3 = pdu.recvMessage()
    print(mess3)
    pdu.close()
    '''
    