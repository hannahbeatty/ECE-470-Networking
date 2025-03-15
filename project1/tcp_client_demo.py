import socket
from app_protocol import SmartHomeProtocol

def main():
    host = "localhost"
    port = 50000

    # Connect to the server
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        protocol = SmartHomeProtocol(client_socket)
        print(f"Connected to server at {host}:{port}")
    except Exception as e:
        print(f"Error connecting to server: {e}")
        return

    print("\n===== SMART HOME CONTROL DEMO =====")
    print("Type 'help' for available commands or 'exit' to quit\n")

    logged_in = False
    running = True

    while running:
        try:
            command = input("\nEnter command > ").strip().lower()
            
            if command == 'exit' or command == 'quit':
                running = False
                
            elif command == 'help':
                display_help(logged_in)
                
            elif command == 'login':
                username = input("Username: ")
                password = input("Password: ")
                
                protocol.send_login(username, password)
                logged_in = protocol.logged_in
                
            elif command == 'logout':
                if not logged_in:
                    print("You're not logged in yet.")
                else:
                    protocol.send_logout()
                    logged_in = False
                
            elif command == 'query all':
                if not logged_in:
                    print("Please login first.")
                else:
                    protocol.request_device_status("all")
                    
            elif command == 'list rooms':
                if not logged_in:
                    print("Please login first.")
                else:
                    protocol.list_rooms()
                
            elif command.startswith('query room'):
                if not logged_in:
                    print("Please login first.")
                else:
                    try:
                        # Allow querying by room name or ID
                        room_identifier = command.split('query room ')[1].strip()
                        
                        # If it's a number, treat as ID; otherwise as a name
                        if room_identifier.isdigit():
                            room_id = int(room_identifier)
                            protocol.request_device_status("room", room_id)
                        else:
                            protocol.request_device_status("room", room_identifier)
                    except IndexError:
                        print("Usage: query room <room_id or room_name>")
                
            elif command.startswith('query group'):
                if not logged_in:
                    print("Please login first.")
                else:
                    try:
                        group_name = command.split()[2]
                        protocol.request_device_status("group", group_name)
                    except IndexError:
                        print("Usage: query group <group_name>")
                
            elif command.startswith('query device'):
                if not logged_in:
                    print("Please login first.")
                else:
                    try:
                        device_id = int(command.split()[2])
                        protocol.request_device_status("device", device_id)
                    except (IndexError, ValueError):
                        print("Usage: query device <device_id>")
                        
            elif command == 'list devices':
                if not logged_in:
                    print("Please login first.")
                else:
                    if hasattr(protocol, 'device_ids_by_type'):
                        print("\nAvailable devices by type:")
                        for device_type, device_ids in protocol.device_ids_by_type.items():
                            print(f"  {device_type}: {device_ids}")
                    else:
                        print("No device information available. Try 'query all' first.")
                        
            elif command.startswith('control'):
                if not logged_in:
                    print("Please login first.")
                else:
                    handle_control_command(command, protocol)
                    
            else:
                print(f"Unknown command: '{command}'. Type 'help' for available commands.")
                
        except Exception as e:
            print(f"Error: {e}")
            
    # Clean up
    try:
        if logged_in:
            protocol.send_logout()
        client_socket.close()
        print("\nDisconnected from server. Goodbye!")
    except Exception as e:
        print(f"Error during cleanup: {e}")
    
    print("\n===== DEMO ENDED =====")

def display_help(logged_in):
    print("\nAvailable commands:")
    print("  help             - Display this help message")
    print("  exit, quit       - Exit the demo")
    
    if not logged_in:
        print("  login            - Log in to the smart home system")
    else:
        print("  logout           - Log out from the smart home system")
        print("  query all        - Query status of all devices")
        print("  list rooms       - List all available rooms")
        print("  query room <id or name> - Query all devices in a specific room")
        print("  query group <group> - Query devices by group (lamps, locks, blinds, alarms)")
        print("  query device <id> - Query a specific device by ID")
        print("  list devices     - List all discovered devices by type")
        print("\nControl commands:")
        print("  control lamp <id> on|off|dim <level>|color <color>")
        print("  control ceiling_light <id> on|off|dim <level>|color <color>")
        print("  control lock <id> lock|unlock <code>")
        print("  control blinds <id> open|close|up|down")
        print("  control alarm <id> arm|disarm|trigger|stop")

def handle_control_command(command, protocol):
    parts = command.split()
    
    if len(parts) < 4:
        print("Usage: control <device_type> <device_id> <action> [parameters]")
        return
        
    device_type = parts[1].capitalize()
    
    try:
        device_id = int(parts[2])
        action = parts[3].lower()
        
        # Check if device exists and has the correct type
        if protocol.get_device_type(device_id) != device_type:
            print(f"Device {device_id} is not a {device_type}.")
            return
            
        # Handle device-specific actions
        if device_type == "Lamp":
            if action in ["on", "off"]:
                protocol.send_device_control(device_id, action)
            elif action == "dim" and len(parts) >= 5:
                level = int(parts[4])
                protocol.send_device_control(device_id, action, level=level)
            elif action == "color" and len(parts) >= 5:
                color = parts[4]
                protocol.send_device_control(device_id, action, color=color)
            else:
                print("Usage: control lamp <id> on|off|dim <level>|color <color>")
                
        elif device_type == "Lock":
            if action == "lock":
                protocol.send_device_control(device_id, action)
            elif action == "unlock" and len(parts) >= 5:
                code = parts[4]
                protocol.send_device_control(device_id, action, code=code)
            else:
                print("Usage: control lock <id> lock|unlock <code>")
                
        elif device_type == "Blinds":
            if action in ["open", "close", "up", "down"]:
                protocol.send_device_control(device_id, action)
            else:
                print("Usage: control blinds <id> open|close|up|down")
                
        elif device_type == "Alarm":
            if action in ["arm", "disarm", "trigger_alarm", "stop_alarm"]:
                protocol.send_device_control(device_id, action)
            else:
                print("Usage: control alarm <id> arm|disarm|trigger_alarm|stop_alarm")
                
        else:
            print(f"Unsupported device type: {device_type}")
            
    except ValueError:
        print("Device ID must be a number.")
    except Exception as e:
        print(f"Error controlling device: {e}")

if __name__ == "__main__":
    main()