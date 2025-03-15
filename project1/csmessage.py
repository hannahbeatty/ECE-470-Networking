# csmessage.py

'''
Created on Feb 15, 2025
@author: hannahbeatty
(forked from nigel)
'''

from enum import Enum

class REQS(Enum):
    LGIN = 100  # User Login
    LOUT = 101  # User Logout
    QERY = 104  # Get status of a device or room
    CTRL = 105  # Control a device (e.g., turn light on, unlock door)

class CSmessage:
    PJOIN = '&'
    VJOIN = '{}={}'
    VJOIN1 = '='

    def __init__(self, req_type=REQS.LGIN):
        """
        Initialize a new CSmessage with a specific request type.
        """
        self._data = {'type': req_type}

    def __str__(self) -> str:
        return self.marshal()

    def reset(self):
        """
        Reset message data.
        """
        self._data = {'type': REQS.LGIN}

    def setType(self, t):
        """
        Set the message type (e.g., LOGIN, QERY, CTRL).
        """
        if not isinstance(t, REQS):
            raise ValueError("Invalid request type")
        self._data['type'] = t

    def getType(self):
        """
        Get the message type.
        """
        return self._data['type']

    def addValue(self, key: str, value: str):
        """
        Add key-value pairs to the message.
        """
        self._data[key] = value

    def getValue(self, key: str, default=None) -> str:
        """
        Retrieve a value from the message.
        :param key: The key to retrieve
        :param default: Default value if key doesn't exist
        :return: The value for the key or default if not found
        """
        return self._data.get(key, default)

    def marshal(self) -> str:
        """
        Convert message data into a serialized string for transmission.
        """
        pairs = []
        for k, v in self._data.items():
            # --- NEW: If it's 'type' and an enum, store the integer code, e.g. "100" ---
            if k == "type" and isinstance(v, REQS):
                v = str(v.value)
            else:
                v = str(v)

            pairs.append(CSmessage.VJOIN.format(k, v))
        return CSmessage.PJOIN.join(pairs)

    def unmarshal(self, d: str):
        """
        Convert a received string into message data, ensuring 'type' is an Enum.
        """
        self.reset()
        if d:
            params = d.split(CSmessage.PJOIN)
            for p in params:
                if CSmessage.VJOIN1 in p:
                    k, v = p.split(CSmessage.VJOIN1)
                    if k == "type":  # Convert type back to REQS Enum
                        try:
                            v = REQS(int(v))  # e.g. "100" -> REQS.LGIN
                        except ValueError:
                            v = None  # Invalid type, return None
                    self._data[k] = v

    def validate(self):
        """
        Validate that required fields are present based on request type.
        For response messages (those containing 'status'), we skip these checks.
        """
        req_type = self.getType()

        # If this is a response (has 'status'), skip
        if 'status' in self._data:
            return

        # Otherwise, validate based on the request type:
        if req_type == REQS.LGIN:
            # LOGIN must have username and password
            if 'username' not in self._data or 'password' not in self._data:
                raise ValueError("LOGIN requires username and password")

        elif req_type == REQS.QERY:
            # "all" queries don't need query_value
            if 'query_type' not in self._data:
                raise ValueError("QERY requires 'query_type' (all, room, group, device)")

            if self._data['query_type'] != "all" and 'query_value' not in self._data:
                raise ValueError("QERY requires 'query_value' for room, group, and device queries")



        elif req_type == REQS.CTRL:
            # CTRL must have device_id and action
            if 'device_id' not in self._data or 'action' not in self._data:
                raise ValueError("CTRL requires device_id and action")



            valid_actions = ["on", "off", "lock", "unlock", "open", "close", "up", "down", "dim", "color", 
                             "arm", "disarm", "trigger_alarm", "stop_alarm"]
            if self._data['action'] not in valid_actions:
                raise ValueError(f"Invalid action '{self._data['action']}'")

