import csmessage
from csmessage import REQS
import cspdu
import ast

class SmartHomeProtocol:
    def __init__(self, socket_conn):
        """
        Create a SmartHomeProtocol with an established socket connection.
        :param socket_conn: A socket connected to the Smart Home Server.
        """
        self.pdu = cspdu.CSpdu(socket_conn)
        self.logged_in = False  # Track login state
        self.last_response = None  # Track last server response
        self.device_ids_by_type = {}  # Store discovered device IDs by type
        self.device_types_by_id = {}  # Reverse lookup
        self.room_names = {}  # Store room names by ID
        self.room_ids_by_name = {}  # Reverse lookup for room IDs by name

    def send_login(self, username, password):
        """
        Send a LGIN request (login) to the server, then receive/handle response.
        Prints "Login successful!" or "Login failed!" accordingly.
        """
        msg = csmessage.CSmessage()
        msg.setType(REQS.LGIN)
        msg.addValue("username", username)
        msg.addValue("password", password)
        self.pdu.sendMessage(msg)

        self.last_response = self.receive_response()
        if self.last_response is not None:
            # Check server's response
            if self.last_response.getType() == REQS.LGIN and self.last_response.getValue("status") == "success":
                self.logged_in = True
                print("Login successful!")
                # No longer calling discover_device_ids() automatically after login
            else:
                print("Login failed!")

    def send_logout(self):
        """
        Send a LOUT request (logout) to the server, then receive/handle response.
        Requires that you're already logged in.
        """
        if not self.logged_in:
            raise PermissionError("Must be logged in to log out.")

        msg = csmessage.CSmessage()
        msg.setType(REQS.LOUT)
        self.pdu.sendMessage(msg)

        self.last_response = self.receive_response()
        # Typically the server will close the session,
        # but if we get a response, it might be something like REQS.LOUT with no status.
        self.logged_in = False
        print("Logged out successfully.")

    def send_device_control(self, device_id, action, level=None, color=None, code=None):
        """
        Send a CTRL request to control a device.

        :param device_id: The ID of the device to control.
        :param action: One of "on", "off", "lock", "unlock", "open", "close", "up", "down", "dim", 
                    "color", "arm", "disarm", "trigger_alarm", "stop_alarm".
        :param level: (Optional) Brightness level (0-100) for "dim".
        :param color: (Optional) Color value for "color".
        :param code: (Optional) Unlock code for "unlock".
        """
        if not self.logged_in:
            raise PermissionError("You must be logged in to control devices.")

        msg = csmessage.CSmessage()
        msg.setType(REQS.CTRL)
        msg.addValue("device_id", str(device_id))
        msg.addValue("action", action)

        # Add additional parameters based on action type
        if action == "dim" and level is not None:
            msg.addValue("level", str(level))

        if action == "color" and color is not None:
            msg.addValue("color", str(color))

        if action == "unlock" and code is not None:
            msg.addValue("code", str(code))

        self.pdu.sendMessage(msg)

        self.last_response = self.receive_response()
        if self.last_response is not None:
            status = self.last_response.getValue("status")
            if status == "success":
                print(f"📡 Device {device_id} action '{action}': success")
            else:
                print(f"📡 Device {device_id} action '{action}': {status}")

    def request_device_status(self, query_type, query_value=None):
        """
        Send a QERY request to query the status of devices.
        :param query_type: One of "all", "room", "group", or "device".
        :param query_value: Room ID, Room Name, Group Name, or Device ID (not required for "all").
        """
        if not self.logged_in:
            raise PermissionError("You must be logged in to query device status.")

        try:
            msg = csmessage.CSmessage()
            msg.setType(REQS.QERY)
            msg.addValue("query_type", query_type)

            # Convert room name to room ID if needed
            if query_type == "room" and query_value is not None:
                # Try to interpret query_value as a room name if it's not a number
                if isinstance(query_value, str) and not query_value.isdigit():
                    room_name = query_value.lower()
                    if room_name in self.room_ids_by_name:
                        query_value = self.room_ids_by_name[room_name]
                        print(f"Looking up room '{query_value}' by name")
                    else:
                        # If we haven't queried all rooms yet, do it to get room names
                        if not self.room_ids_by_name:
                            print("No room information available. Fetching room information first...")
                            self._fetch_room_info(quiet=True)
                            # Try again after fetching room info
                            if room_name in self.room_ids_by_name:
                                query_value = self.room_ids_by_name[room_name]
                                print(f"Found room '{room_name}' with ID {query_value}")
                            else:
                                print(f"Warning: Room name '{room_name}' not found.")

            if query_type != "all" and query_value is not None:  # Only add query_value for room, group, and device queries
                msg.addValue("query_value", str(query_value))

            self.pdu.sendMessage(msg)

            self.last_response = self.receive_response()
            if self.last_response is not None:
                status = self.last_response.getValue("status")
                device_status = self.last_response.getValue("device_status")
                
                if status == "success" and device_status:
                    display_value = query_value
                    if query_type == "room" and query_value in self.room_names:
                        display_value = f"{query_value} ({self.room_names[query_value]})"
                    
                    print(f"Query result ({query_type}" + (f" - {display_value}" if query_value else "") + f"): {device_status}")
                    
                    # Update device type information if this was an "all" query
                    if query_type == "all":
                        self._update_device_info(device_status)
                elif status == "error":
                    error_msg = self.last_response.getValue("error_message")
                    print(f"Query failed: {error_msg}")
                else:
                    print(f"Query returned no data or unexpected format. Raw: {self.last_response}")
        except Exception as e:
            print(f"Error in device status request: {e}")

    def _fetch_room_info(self, quiet=False):
        """
        Request information about rooms to build the room name mappings.
        This is a private helper method.
        
        :param quiet: If True, suppresses output messages for cleaner UI
        """
        if not self.logged_in:
            if not quiet:
                print("Warning: Cannot fetch room info before login.")
            return
            
        try:
            # Send a message to request room information
            msg = csmessage.CSmessage()
            msg.setType(REQS.QERY)
            msg.addValue("query_type", "all")  # Query all to get all room data
            
            self.pdu.sendMessage(msg)
            
            response = self.receive_response()
            if response is not None and response.getValue("status") == "success":
                device_status = response.getValue("device_status")
                if device_status:
                    self._update_room_info(device_status)
                    self._update_device_info(device_status, quiet=quiet)
        except Exception as e:
            if not quiet:
                print(f"Error fetching room information: {e}")

    def discover_device_ids(self):
        """
        Query all devices and build a mapping of device types to their IDs.
        Call this after login to set up the device ID mappings.
        """
        if not self.logged_in:
            print("Warning: Cannot discover devices before login.")
            return
            
        # Query all devices to build the device type mapping
        self.request_device_status("all")

    def list_rooms(self):
        """
        List all available rooms.
        """
        if not self.room_names:
            # Fetch room info silently
            self._fetch_room_info(quiet=True)
            
        if self.room_names:
            print("\nAvailable rooms:")
            for room_id, room_name in sorted(self.room_names.items()):
                print(f"  Room {room_id}: {room_name}")
        else:
            print("No room information available. Try 'query all' first.")

    def get_device_by_type(self, device_type, index=0):
        """
        Get a device ID by its type.
        :param device_type: The type of device (e.g., 'Lamp', 'Lock', 'Alarm')
        :param index: If multiple devices of the same type exist, which one to return (default: 0 for first)
        :return: The device ID or None if not found
        """
        devices = self.device_ids_by_type.get(device_type, [])
        if index < len(devices):
            return devices[index]
        return None

    def get_device_type(self, device_id):
        """
        Get the type of a device by its ID.
        :param device_id: The device ID
        :return: The device type or None if not found
        """
        return self.device_types_by_id.get(str(device_id))

    def _update_device_info(self, status_str, quiet=False):
        """
        Parse device status response and update internal device type mappings.
        :param status_str: String representation of device status
        :param quiet: If True, suppresses output messages for cleaner UI
        """
        try:
            # Convert the string representation to a Python dictionary
            status_dict = ast.literal_eval(status_str)
            
            # Reset device mappings
            self.device_ids_by_type = {}
            self.device_types_by_id = {}
            
            # Process all rooms and devices
            for room_id, room_devices in status_dict.items():
                for device_id, device_info in room_devices.items():
                    # Skip non-numeric keys like 'blinds' or 'ceiling_light' that are references
                    if isinstance(device_id, str) and not device_id.isdigit():
                        # If it's a ceiling_light, extract its info
                        if device_id == "ceiling_light" and device_info:
                            ceiling_light_id = device_info.get('device_id')
                            if ceiling_light_id and 'type' in device_info:
                                device_type = device_info['type']
                                # Add to type->id mapping
                                if device_type not in self.device_ids_by_type:
                                    self.device_ids_by_type[device_type] = []
                                self.device_ids_by_type[device_type].append(ceiling_light_id)
                                # Add to id->type mapping
                                self.device_types_by_id[str(ceiling_light_id)] = device_type
                        continue
                        
                    if 'type' in device_info:
                        device_type = device_info['type']
                        # Add to type->id mapping
                        if device_type not in self.device_ids_by_type:
                            self.device_ids_by_type[device_type] = []
                        self.device_ids_by_type[device_type].append(int(device_id))
                        
                        # Add to id->type mapping
                        self.device_types_by_id[str(device_id)] = device_type
            
            if self.device_ids_by_type and not quiet:
                print(f"Discovered devices by type: {self.device_ids_by_type}")
                
        except Exception as e:
            if not quiet:
                print(f"Error updating device information: {e}")

    def _update_room_info(self, status_str):
        """
        Parse device status response to extract room information.
        :param status_str: String representation of device status
        """
        try:
            # Convert the string representation to a Python dictionary
            status_dict = ast.literal_eval(status_str)
            
            # Update room mappings based on room IDs
            for room_id in status_dict.keys():
                # We don't have room names in the standard response, so we'll use placeholder names
                # The server's SmartHomeServer has room names, but they're not included in the response
                # We can use default names based on the IDs, which will be:
                # 101: Living Room, 102: Kitchen, 103: Bedroom
                room_name = "Unknown Room"
                if room_id == 101:
                    room_name = "Living Room"
                elif room_id == 102:
                    room_name = "Kitchen"
                elif room_id == 103:
                    room_name = "Bedroom"
                
                self.room_names[room_id] = room_name
                self.room_ids_by_name[room_name.lower()] = room_id
                
        except Exception as e:
            print(f"Error updating room information: {e}")

    def receive_response(self):
        """
        Block until the next response arrives from the server.
        Returns a CSmessage or None on error.
        Also does some basic printing for known error cases.
        """
        try:
            response = self.pdu.recvMessage()

            # Optional: Additional checks for specific error messages:
            if response.getType() == REQS.LGIN and response.getValue("status") == "failure":
                print("Login failed: Incorrect credentials")
            elif response.getType() == REQS.CTRL and response.getValue("status") == "error":
                print(f"Device control failed: {response.getValue('error_message')}")

            return response

        except Exception as e:
            print(f"Error receiving response: {e}")
            return None