import socket
from app_protocol import SmartHomeProtocol

def main():
    host = "localhost"
    port = 50000

    # 1) Connect to the server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    protocol = SmartHomeProtocol(client_socket)

    print("===== DEMO START =====")

    # STEP 1: LOGIN FAILURE
    print("\n[STEP 1] Attempt login with incorrect credentials...")
    protocol.send_login("admin", "wrongpass")
    # The protocol prints "Login failed!" on failure.

    # STEP 1B: LOGIN SUCCESS
    print("\n[STEP 1B] Attempt login with correct credentials...")
    protocol.send_login("admin", "password123")
    # The protocol prints "Login successful!" on success.
    # Device discovery happens automatically upon successful login

    # STEP 2: QUERY DEVICES TO DEMONSTRATE STRUCTURE
    print("\n[STEP 2] Querying devices...")
    
    print("\n--- Query All Devices ---")
    protocol.request_device_status("all")
    
    print("\n--- Query by Room: Living Room (101) ---")
    protocol.request_device_status("room", 101)
    
    print("\n--- Query by Room: Kitchen (102) ---")
    protocol.request_device_status("room", 102)
    
    print("\n--- Query by Room: Bedroom (103) ---")
    protocol.request_device_status("room", 103)
    
    print("\n--- Query by Group: All Lamps ---")
    protocol.request_device_status("group", "lamps")
    
    print("\n--- Query by Group: All Locks ---")
    protocol.request_device_status("group", "locks")
    
    # STEP 3: DEMONSTRATE DEVICE CONTROL WITH CORRECT DEVICE TYPES
    print("\n[STEP 3] Changing some device states...")
    
    # Get device IDs by type
    lamp_id = protocol.get_device_by_type("Lamp", 0)
    lock_id = protocol.get_device_by_type("Lock", 0)
    blinds_id = protocol.get_device_by_type("Blinds", 0)
    alarm_id = protocol.get_device_by_type("Alarm", 0)
    
    if alarm_id:
        print(f"--- Arming the Alarm (Device {alarm_id}) ---")
        protocol.send_device_control(alarm_id, "arm")
        protocol.request_device_status("device", alarm_id)
    
    if lock_id:
        print(f"--- Unlocking Lock (Device {lock_id}) ---")
        protocol.send_device_control(lock_id, "unlock", code="1234")
        protocol.request_device_status("device", lock_id)
    
    if lamp_id:
        print(f"--- Turning ON Lamp (Device {lamp_id}) ---")
        protocol.send_device_control(lamp_id, "on")
        protocol.request_device_status("device", lamp_id)
        
        print(f"--- Dimming Lamp to 50% ---")
        protocol.send_device_control(lamp_id, "dim", level=50)
        protocol.request_device_status("device", lamp_id)
        
        print(f"--- Changing Lamp Color to Blue ---")
        protocol.send_device_control(lamp_id, "color", color="blue")
        protocol.request_device_status("device", lamp_id)
    
    if blinds_id:
        print(f"--- Opening Blinds (Device {blinds_id}) ---")
        protocol.send_device_control(blinds_id, "open")
        protocol.request_device_status("device", blinds_id)

    # STEP 4: RE-QUERY ALL DEVICES TO SEE UPDATED STATUS
    print("\n[STEP 4] Re-querying devices to see updated status...")
    protocol.request_device_status("all")

    # STEP 5: LOGOUT
    print("\n[STEP 5] Logging out...")
    protocol.send_logout()

    # STEP 6: ATTEMPT DEVICE CONTROL AFTER LOGOUT
    print("\n[STEP 6] Attempting control after logout (should fail)...")
    try:
        if lamp_id:
            protocol.send_device_control(lamp_id, "off")
    except PermissionError as e:
        print(f"Expected error: {e}")

    print("\n===== DEMO END =====")

    # 7) Close the socket
    client_socket.close()

if __name__ == "__main__":
    main()



