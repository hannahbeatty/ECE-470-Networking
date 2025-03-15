'''
Created on Feb 11, 2025

@author: nigel
'''

from enum import Enum

class REQS(Enum):
    LGIN = 100
    LOUT = 101
    LIST = 102
    SRCH = 103

class CSmessage(object):
    '''
    classdocs
    '''
    
    PJOIN = '&'
    VJOIN = '{}={}'
    VJOIN1 = '='

    def __init__(self):
        '''
        Constructor
        '''
        self._data = {}
        self._data['type'] = REQS.LGIN
        
    def __str__(self) -> str:
        return self.marshal()
        
    def reset(self):
        self._data = {}
        self._data['type'] = REQS.LGIN
        
    def setType(self, t):
        self._data['type'] = t
        
    def getType(self):
        return self._data['type']
    
    def addValue(self, key: str, value: str):
        self._data[key] = value
        
    def getValue(self, key: str) -> str:
        return self._data[key]
    
    def marshal(self) -> str:
        pairs = [CSmessage.VJOIN.format(k,v) for (k, v) in self._data.items()]
        params = CSmessage.PJOIN.join(pairs)
        return params
    
    def unmarshal(self, d: str):
        self.reset()
        if d:
            params = d.split(CSmessage.PJOIN)
            for p in params:
                k,v = p.split(CSmessage.VJOIN1)
                self._data[k] = v
