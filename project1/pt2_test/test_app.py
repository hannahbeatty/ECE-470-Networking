import app_protocol
import socket

import socket
from csmessage import CSmessage, REQS
from cspdu import CSpdu

def test_message_creation_and_marshal():
    """
    1) Create various CSmessages
    2) Marshal (serialize) them
    3) Unmarshal (deserialize) into new CSmessage objects
    4) Compare results
    """
    print("=== Testing Message Creation, Marshaling, and Unmarshaling ===")

    # A) LOGIN message
    login_msg = CSmessage()
    login_msg.setType(REQS.LGIN)
    login_msg.addValue("username", "hannah")
    login_msg.addValue("password", "mypassword")
    
    # Marshal
    login_data = login_msg.marshal()
    print("Marshaled LOGIN message:", login_data)
    
    # Unmarshal into a new message
    new_login_msg = CSmessage()
    new_login_msg.unmarshal(login_data)
    print("Unmarshaled LOGIN message:", new_login_msg.marshal())
    
    # Check if they match
    assert login_msg.marshal() == new_login_msg.marshal(), "LOGIN message mismatch after unmarshal!"
    
    # B) QUERY message
    query_msg = CSmessage()
    query_msg.setType(REQS.QERY)
    query_msg.addValue("device_id", "123")
    
    query_data = query_msg.marshal()
    print("\nMarshaled QUERY message:", query_data)
    
    new_query_msg = CSmessage()
    new_query_msg.unmarshal(query_data)
    print("Unmarshaled QUERY message:", new_query_msg.marshal())
    
    assert query_msg.marshal() == new_query_msg.marshal(), "QUERY message mismatch after unmarshal!"
    
    # C) CONTROL message
    ctrl_msg = CSmessage()
    ctrl_msg.setType(REQS.CTRL)
    ctrl_msg.addValue("device_id", "1")
    ctrl_msg.addValue("action", "on")
    
    ctrl_data = ctrl_msg.marshal()
    print("\nMarshaled CONTROL message:", ctrl_data)
    
    new_ctrl_msg = CSmessage()
    new_ctrl_msg.unmarshal(ctrl_data)
    print("Unmarshaled CONTROL message:", new_ctrl_msg.marshal())
    
    assert ctrl_msg.marshal() == new_ctrl_msg.marshal(), "CONTROL message mismatch after unmarshal!"

    print("\nAll creation, marshaling, and unmarshaling tests passed!\n")

def test_sending_and_receiving():
    """
    5) Use socket.socketpair() to simulate sending/receiving a CSmessage
    via the CSpdu class, verifying the data is preserved.
    """
    print("=== Testing CSpdu Send/Receive (No Real Server Needed) ===")
    
    # Create a pair of connected sockets (client_sock, server_sock)
    client_sock, server_sock = socket.socketpair()
    
    try:
        client_pdu = CSpdu(client_sock)
        server_pdu = CSpdu(server_sock)
        
        # Build a CONTROL message
        ctrl_msg = CSmessage()
        ctrl_msg.setType(REQS.CTRL)
        ctrl_msg.addValue("device_id", "2")
        ctrl_msg.addValue("action", "off")
        
        print("Sending CONTROL message from client to server...")
        client_pdu.sendMessage(ctrl_msg)
        
        print("Server receiving message...")
        received_msg = server_pdu.recvMessage()
        
        # Print results
        print("Received message marshaled:", received_msg.marshal())
        print("Received message type:", received_msg.getType())
        print("Received device_id:", received_msg.getValue("device_id"))
        print("Received action:", received_msg.getValue("action"))
        
        # Confirm they match
        assert ctrl_msg.marshal() == received_msg.marshal(), "Mismatch in CONTROL message over socketpair!"
        
        print("Send/Receive test passed!\n")
    
    finally:
        client_sock.close()
        server_sock.close()

if __name__ == "__main__":
    # 1) Test creation, marshaling, and unmarshaling of messages
    test_message_creation_and_marshal()
    
    # 2) Test sending/receiving with mock sockets
    test_sending_and_receiving()
    
    print("All Application Protocol tests completed successfully.")