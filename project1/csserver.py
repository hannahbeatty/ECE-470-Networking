'''
Created on Feb 20, 2025
@author: hannahbeatty
(forked from nigel)
'''

import socket
import logging
from csmessage import CSmessage, REQS
from cspdu import CSpdu
from home_model import SmartHouse, Room, Lamp, Blinds, Alarm, Lock, CeilingLight


logging.basicConfig(level=logging.DEBUG)

class SmartHomeServer:
    """Smart Home TCP Server using request routing."""
    logger = logging.getLogger("SmartHomeServer")

    def __init__(self, host="localhost", port=50000):
        """Initialize the Smart Home Server."""
        print("[INIT] Smart Home Server is starting...")
        self.host = host
        self.port = port

        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)  # allow up to 5 clients
            self.connected = False
            print(f"[INIT] Server initialized on {self.host}:{self.port}")
        except Exception as e:
            print(f"[ERROR] Failed to initialize server: {e}")
            exit(1)

    def run(self):
        """Main server loop."""
        print(f"[RUN] Smart Home Server is running on {self.host}:{self.port}...")
        logging.info("Waiting for client connections...")

        while True:
            try:
                print("[LISTENING] Waiting for a client to connect...")
                client_socket, addr = self.server_socket.accept()
                print(f"[CONNECTED] New connection from {addr}")
                logging.info(f"Client connected: {addr}")
                self.connected = True

                # Create PDU for communication
                pdu = CSpdu(client_socket)

                # Create an instance of SmartHomeServerOps to process requests
                handler = SmartHomeServerOps()
                handler.pdu = pdu
                handler.connected = True

                # Run the request handling loop
                handler.run()

                logging.info(f"Client {addr} disconnected.")
                print(f"[DISCONNECTED] Client {addr} disconnected.")
                client_socket.close()

            except Exception as e:
                logging.error(f"[ERROR] Server error: {e}")
                print(f"[ERROR] Server error: {e}")


class SmartHomeServerOps:
    """Handles Smart Home client requests."""
    logger = logging.getLogger("SmartHomeServerOps")

    def __init__(self):
        

        # 1) Create the House
        self.smart_home = SmartHouse(1, "My Demo House")

        # 2) Create the Rooms
        living_room = Room(room_id=101, name="Living Room")
        kitchen = Room(room_id=102, name="Kitchen")
        bedroom = Room(room_id=103, name="Bedroom")

        # Add rooms to the house
        self.smart_home.add_room(living_room)
        self.smart_home.add_room(kitchen)
        self.smart_home.add_room(bedroom)

        # 3) Add devices to the Living Room
        lr_light1 = Lamp(device_id=0, on=False, shade=100)
        lr_light2 = Lamp(device_id=0, on=False, shade=100)
        lr_light3 = Lamp(device_id=0, on=False, shade=100)
        lr_blinds = Blinds(device_id=0, is_up=True, is_open=False)

        living_room.add_lamp(lr_light1)
        living_room.add_lamp(lr_light2)
        living_room.add_lamp(lr_light3)
        living_room.add_blinds(lr_blinds)

        # 4) Add devices to the Kitchen
        kitchen_light = CeilingLight(device_id=0, on=False, shade=100)
        kitchen.add_ceiling_light(kitchen_light)

        # 5) Add devices to the Bedroom
        bed_light1 = Lamp(device_id=0, on=False, shade=100)
        bed_light2 = Lamp(device_id=0, on=False, shade=100)
        bed_blinds = Blinds(device_id=0, is_up=True, is_open=False)

        bedroom.add_lamp(bed_light1)
        bedroom.add_lamp(bed_light2)
        bedroom.add_blinds(bed_blinds)

        alarm = Alarm(code=9999, is_armed=False, is_alarm=False)
       
        living_room._assign_device_id(alarm)
        living_room.devices[alarm.device_id] = alarm

        # Two Locks
        lock1 = Lock(device_id=0, code=["1234", "1235", "1236", "1237", "1238"], is_unlocked=False)
        lock2 = Lock(device_id=0, code=["9999", "9998", "9997", "9996", "9995"], is_unlocked=False)
        living_room.add_lock(lock1)
        living_room.add_lock(lock2)


        #print(f"Device IDs assigned: {[d.device_id for room in self.smart_home.rooms.values() for d in room.devices.values()]}")



        # Routing table
        self._route = {
            REQS.LGIN: self._doLogin,
            REQS.LOUT: self._doLogout,
            REQS.CTRL: self._doDeviceControl,
            REQS.QERY: self._doQuery
        }

    def _doLogin(self, req: CSmessage) -> CSmessage:
        """Handles login request."""
        username = req.getValue("username")
        password = req.getValue("password")
        SmartHomeServerOps.logger.info(f"[LOGIN] Attempt from: {username}")

        #how to handle admin priveleges here lol
        if username == "hannahbanana" and password == "JuniperTheCat":
            self.logged_in_user = username
            resp = CSmessage(REQS.LGIN)
            resp.addValue("status", "success")
            print(f"[LOGIN SUCCESS] User: {username}")
        else:
            resp = CSmessage(REQS.LGIN)
            resp.addValue("status", "failure")
            print(f"[LOGIN FAILED] User: {username}")

        return resp

    def _doLogout(self, req: CSmessage) -> CSmessage:
        """Handles logout request."""
        print(f"[LOGOUT] User: {self.logged_in_user} logging out.")
        SmartHomeServerOps.logger.info(f"Logging out user: {self.logged_in_user}")
        self.logged_in_user = None
        self.connected = False  # terminate session
        return CSmessage(REQS.LOUT)

    def _doDeviceControl(self, req: CSmessage) -> CSmessage:
        """
        Handles device control requests. Supports:
        - Lamps / CeilingLight: "on", "off", "dim", ADD COLOR HERE
        - Locks: "lock", "unlock"
        - Blinds: "open", "close" (via shutter), "up", "down", (via toggle)
        - Alarm: "arm", "disarm", "trigger_alarm", "stop_alarm", "enter_code"

        device status handled in query call (other function)

        Note: I allow color and dim to be changed while the lamp is off.
        """
        #print(f"[DEBUG] Looking up device {device_id} - Found: {type(found_device).__name__}")

        if not self.logged_in_user:
            print("[ERROR] Device control attempted without login!")
            resp = CSmessage(REQS.CTRL)
            resp.addValue("status", "error")
            resp.addValue("error_message", "User not logged in")
            return resp

        # 1) Get the device_id and action from the request
        device_id_str = req.getValue("device_id")
        action = req.getValue("action")

        # Convert device_id to an integer
        try:
            device_id = int(device_id_str)
        except ValueError:
            resp = CSmessage(REQS.CTRL)
            resp.addValue("status", "error")
            resp.addValue("error_message", f"Invalid device_id: {device_id_str}")
            return resp

        # 2) Find the actual device object in the house
        found_device = None
        for room in self.smart_home.rooms.values():
            found_device = room.get_device(device_id)
            if found_device:
                break

        if not found_device:
            # No device with that ID
            resp = CSmessage(REQS.CTRL)
            resp.addValue("status", "error")
            resp.addValue("error_message", f"Device {device_id} not found in any room.")
            return resp

        # 3) Device-Specific Logic

        if isinstance(found_device, Lamp) or isinstance(found_device, CeilingLight):
            if action == "on":
                if found_device.on:
                    resp = CSmessage(REQS.CTRL)
                    resp.addValue("status", "error")
                    resp.addValue("error_message", f"Device {device_id} is already ON.")
                    return resp
                else:
                    found_device.flip_switch()
                    print(f"[DEVICE CONTROL] Turned ON device {device_id} (Lamp/Light)")

            elif action == "off":
                if not found_device.on:
                    resp = CSmessage(REQS.CTRL)
                    resp.addValue("status", "error")
                    resp.addValue("error_message", f"Device {device_id} is already OFF.")
                    return resp
                else:
                    found_device.flip_switch()
                    print(f"[DEVICE CONTROL] Turned OFF device {device_id} (Lamp/Light)")

            elif action == "dim":
                level_str = req.getValue("level")
                if level_str is None:
                    resp = CSmessage(REQS.CTRL)
                    resp.addValue("status", "error")
                    resp.addValue("error_message", "Missing brightness level for dim action.")
                    return resp

                try:
                    level = int(level_str)
                    found_device.set_shade(level)
                    print(f"[DEVICE CONTROL] Dimmed device {device_id} to {level}% brightness.")
                except ValueError:
                    resp = CSmessage(REQS.CTRL)
                    resp.addValue("status", "error")
                    resp.addValue("error_message", "Invalid brightness level. Must be an integer between 0 and 100.")
                    return resp
                

            elif action == "color":
                color_str = req.getValue("color")
                if color_str is None:
                    resp = CSmessage(REQS.CTRL)
                    resp.addValue("status", "error")
                    resp.addValue("error_message", "Missing color value for color action.")
                    return resp

                valid_colors = ["red", "green", "blue", "white", "yellow", "purple", "orange"]
                if color_str.lower() not in valid_colors:
                    resp = CSmessage(REQS.CTRL)
                    resp.addValue("status", "error")
                    resp.addValue("error_message", f"Invalid color '{color_str}'. Supported colors: {', '.join(valid_colors)}.")
                    return resp

                found_device.change_color(color_str.lower())  # Apply color change
                print(f"[DEVICE CONTROL] Set device {device_id} color to {color_str.lower()}.")

            else:
                resp = CSmessage(REQS.CTRL)
                resp.addValue("status", "error")
                resp.addValue("error_message", f"Action '{action}' not supported for Lamp/Light. Use 'on', 'off', or 'dim'.")
                return resp


        elif isinstance(found_device, Lock):
            if action == "lock":
                found_device.lock()
                print(f"[DEVICE CONTROL] Locked device {device_id} (Lock)")

            elif action == "unlock":
                user_code = req.getValue("code")  # Get the user-entered code
                if user_code is None:
                    resp = CSmessage(REQS.CTRL)
                    resp.addValue("status", "error")
                    resp.addValue("error_message", "Unlocking requires a code.")
                    return resp

                if found_device.unlock(user_code):
                    print(f"[DEVICE CONTROL] Unlocked device {device_id} (Lock)")
                else:
                    print(f"[DEVICE CONTROL] Incorrect code for unlocking device {device_id}. Failed attempts: {found_device.failed_attempts}")
                    resp = CSmessage(REQS.CTRL)
                    resp.addValue("status", "error")
                    resp.addValue("error_message", "Incorrect unlock code.")
                    return resp

            else:
                resp = CSmessage(REQS.CTRL)
                resp.addValue("status", "error")
                resp.addValue("error_message", f"Action '{action}' not supported for Lock. Use 'lock'/'unlock'.")
                return resp


        elif isinstance(found_device, Blinds):
            if action == "open":
                if found_device.is_open:
                    resp = CSmessage(REQS.CTRL)
                    resp.addValue("status", "error")
                    resp.addValue("error_message", f"Blinds {device_id} are already OPEN.")
                    return resp
                else:
                    found_device.shutter()
                    print(f"[DEVICE CONTROL] Blinds {device_id} opened.")

            elif action == "close":
                if not found_device.is_open:
                    resp = CSmessage(REQS.CTRL)
                    resp.addValue("status", "error")
                    resp.addValue("error_message", f"Blinds {device_id} are already CLOSED.")
                    return resp
                else:
                    found_device.shutter()
                    print(f"[DEVICE CONTROL] Blinds {device_id} closed.")

            elif action == "up":
                if found_device.is_up:
                    resp = CSmessage(REQS.CTRL)
                    resp.addValue("status", "error")
                    resp.addValue("error_message", f"Blinds {device_id} are already UP.")
                    return resp
                else:
                    found_device.toggle()
                    print(f"[DEVICE CONTROL] Blinds {device_id} raised.")

            elif action == "down":
                if not found_device.is_up:
                    resp = CSmessage(REQS.CTRL)
                    resp.addValue("status", "error")
                    resp.addValue("error_message", f"Blinds {device_id} are already DOWN.")
                    return resp
                else:
                    found_device.toggle()
                    print(f"[DEVICE CONTROL] Blinds {device_id} lowered.")

            else:
                resp = CSmessage(REQS.CTRL)
                resp.addValue("status", "error")
                resp.addValue("error_message", f"Action '{action}' not supported for Blinds. Use 'open', 'close', 'up', or 'down'.")
                return resp


        elif isinstance(found_device, Alarm):
            if action == "arm":
                if found_device.is_armed:
                    resp = CSmessage(REQS.CTRL)
                    resp.addValue("status", "error")
                    resp.addValue("error_message", f"Alarm {device_id} is already ARMED.")
                    return resp
                else:
                    found_device.arm()
                    print(f"[DEVICE CONTROL] Alarm {device_id} armed.")

            elif action == "disarm":
                if not found_device.is_armed:
                    resp = CSmessage(REQS.CTRL)
                    resp.addValue("status", "error")
                    resp.addValue("error_message", f"Alarm {device_id} is already DISARMED.")
                    return resp
                else:
                    found_device.disarm()
                    print(f"[DEVICE CONTROL] Alarm {device_id} disarmed.")

            elif action == "trigger_alarm":
                if found_device.is_alarm:
                    resp = CSmessage(REQS.CTRL)
                    resp.addValue("status", "error")
                    resp.addValue("error_message", f"Alarm {device_id} is ALREADY TRIGGERED.")
                    return resp
                else:
                    found_device.trigger_alarm()
                    print(f"[DEVICE CONTROL] Alarm {device_id} has been TRIGGERED!")

            elif action == "stop_alarm":
                if not found_device.is_alarm:
                    resp = CSmessage(REQS.CTRL)
                    resp.addValue("status", "error")
                    resp.addValue("error_message", f"Alarm {device_id} is NOT currently triggered.")
                    return resp
                else:
                    found_device.stop_alarm()
                    print(f"[DEVICE CONTROL] Alarm {device_id} has been STOPPED.")

            elif action == "enter_code":
                user_code = req.getValue("code")  # Get the user-entered code
                if user_code is None:
                    resp = CSmessage(REQS.CTRL)
                    resp.addValue("status", "error")
                    resp.addValue("error_message", "Disarming requires a code.")
                    return resp

                if found_device.enter_code(user_code):
                    print(f"[DEVICE CONTROL] Correct code entered. Alarm {device_id} DISARMED.")
                else:
                    print(f"[DEVICE CONTROL] Incorrect code entered for Alarm {device_id}.")
                    resp = CSmessage(REQS.CTRL)
                    resp.addValue("status", "error")
                    resp.addValue("error_message", "Incorrect disarm code.")
                    return resp

            else:
                resp = CSmessage(REQS.CTRL)
                resp.addValue("status", "error")
                resp.addValue("error_message", f"Action '{action}' not supported for Alarm. Use 'arm', 'disarm', 'trigger_alarm', 'stop_alarm', or 'enter_code'.")
                return resp


        else:
            resp = CSmessage(REQS.CTRL)
            resp.addValue("status", "error")
            resp.addValue("error_message",
                          f"Device {device_id} type is not recognized or supported by this server.")
            return resp

        resp = CSmessage(REQS.CTRL)
        resp.addValue("status", "success")
        return resp

    
    def _doQuery(self, req: CSmessage) -> CSmessage:
        """Handles device status queries for All Devices, By Room, By Group, or By Device."""

        if not self.logged_in_user:
            print("[ERROR] Query attempted without login!")
            resp = CSmessage(REQS.QERY)
            resp.addValue("status", "error")
            resp.addValue("error_message", "User not logged in")
            return resp

        # Create a default response message in case of errors
        resp = CSmessage(REQS.QERY)

        try:
            # Determine query type: all, room, group, or device
            query_type = req.getValue("query_type")  # "all", "room", "group", "device"
            query_value = req.getValue("query_value")  # Room ID, Group Name, or Device ID

            if query_type == "all":
                # Return status of all rooms and devices with type information
                all_status = {}
                for room_id, room in self.smart_home.rooms.items():
                    room_status = {}
                    for device_id, device in room.devices.items():
                        # Add device type to each device status
                        device_status = device.check_status()
                        device_status["type"] = type(device).__name__
                        room_status[device_id] = device_status
                    all_status[room_id] = room_status
                    
                status = all_status
                print("[QUERY] Returning status for all devices.")
                self.logger.info("[QUERY] Returning status for all devices.")

            elif query_type == "room":
                # Fetch room by ID with type information
                try:
                    room_id = int(query_value)
                    room = self.smart_home.get_room(room_id)
                    if not room:
                        raise ValueError("Room not found")
                    
                    # Add type information to each device in the room
                    room_status = {}
                    for device_id, device in room.devices.items():
                        device_status = device.check_status()
                        device_status["type"] = type(device).__name__
                        room_status[device_id] = device_status
                        
                    status = {room_id: room_status}
                    print(f"[QUERY] Returning status for Room {room_id}")
                    self.logger.info(f"[QUERY] Returning status for Room {room_id}")
                except ValueError:
                    resp.addValue("status", "error")
                    resp.addValue("error_message", f"Invalid room ID: {query_value}")
                    return resp

            elif query_type == "group":
                # Filter devices by type with type information included
                group_name = query_value.lower()
                group_status = {}
                
                for room in self.smart_home.rooms.values():
                    for device_id, device in room.devices.items():
                        if (group_name == "lamps" and isinstance(device, Lamp)) or \
                        (group_name == "locks" and isinstance(device, Lock)) or \
                        (group_name == "blinds" and isinstance(device, Blinds)) or \
                        (group_name == "alarms" and isinstance(device, Alarm)) or \
                        (group_name == "ceiling_lights" and isinstance(device, CeilingLight)):
                            device_status = device.check_status()
                            device_status["type"] = type(device).__name__
                            group_status[device_id] = device_status

                if not group_status:
                    print(f"[QUERY] No devices found in group '{group_name}'")
                    self.logger.info(f"[QUERY] No devices found in group '{group_name}'")
                
                status = {group_name: group_status}

            elif query_type == "device":
                # Fetch single device by ID (already includes type)
                try:
                    device_id = int(query_value)
                    found_device = None
                    for room in self.smart_home.rooms.values():
                        found_device = room.get_device(device_id)
                        if found_device:
                            break

                    if not found_device:
                        raise ValueError("Device not found")

                    # Already includes type in the device query
                    device_status = found_device.check_status()
                    device_status["type"] = type(found_device).__name__
                    status = {device_id: device_status}
                    
                    print(f"[QUERY] Returning status for Device {device_id}")
                    self.logger.info(f"[QUERY] Returning status for Device {device_id}")
                except ValueError:
                    resp.addValue("status", "error")
                    resp.addValue("error_message", f"Invalid device ID: {query_value}")
                    return resp

            else:
                resp.addValue("status", "error")
                resp.addValue("error_message", "Invalid query type. Use 'all', 'room', 'group', or 'device'.")
                return resp

            # Create response message with successful status
            resp.addValue("status", "success")
            resp.addValue("device_status", str(status))
            
        except Exception as e:
            # Catch all exceptions to prevent server crash
            error_msg = f"Error processing query: {str(e)}"
            print(f"[ERROR] {error_msg}")
            self.logger.error(error_msg)
            
            resp.addValue("status", "error")
            resp.addValue("error_message", error_msg)
        
        return resp

    def _process(self, req: CSmessage) -> CSmessage:
        """Routes requests."""
        handler = self._route.get(req.getType(), None)
        if handler:
            return handler(req)
        else:
            print(f"[WARNING] Unknown request type: {req.getType()}")
        return CSmessage(REQS.LOUT)

    def run(self):
        """Server loop."""
        print("[START] Handling client requests...")
        try:
            while self.connected:
                try:
                    req = self.pdu.recvMessage()
                    print(f"[REQUEST] Received: {req}")
                    SmartHomeServerOps.logger.info(f"Received request: {req}")

                    resp = self._process(req)
                    print(f"[RESPONSE] Sending: {resp}")
                    SmartHomeServerOps.logger.info(f"Sending response: {resp}")

                    self.pdu.sendMessage(resp)

                    if req.getType() == REQS.LOUT:
                        break
                        
                except ConnectionError as e:
                    logging.error(f"[ERROR] Connection error: {e}")
                    print(f"[ERROR] Connection error: {e}")
                    break
                except Exception as e:
                    logging.error(f"[ERROR] Processing request error: {e}")
                    print(f"[ERROR] Processing request error: {e}")
                    # Continue the loop rather than breaking, to see if the connection can recover
            
        except Exception as e:
            logging.error(f"[ERROR] Server loop error: {e}")
            print(f"[ERROR] Server loop error: {e}")

        self.shutdown()


# Code for running the server
server = SmartHomeServer()  # Default host="localhost", port=50000
server.run()
