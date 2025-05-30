'''
Created on April 15, 2025

@author: hannahbeatty

'''

import socket
import csmessage
import cspdu
import hashlib

'''
structural implementation (plan):

class user IMPORTANT logged_in bool
class house
-> class alarm (composition)
-> class room (composition) 
   -> 4 subdevice classes (lamp, lights, lock, blinds) - each composition

'''



#question - do I need to add admin priveleges? 
#should there be a dictionary of users and associated allowed passwords?
class User:
    def __init__(self, user_id: int, username: str, password: str, role: str = "regular"):
        self.user_id = user_id
        self.username = username
        self.password_hash = self._hash_password(password)
        self.logged_in = False
        self.role = role  # 'admin', 'regular', 'guest'
        self.accessible_houses = set()  # house_ids this user can access

    def _hash_password(self, password: str) -> str:
        """
        Hashes the password using SHA-256 for secure storage.
        :param password: The raw password
        :return: The hashed password
        """
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, password: str) -> bool:
        """
        Authenticate the user with a password.
        :param password: The input password
        :return: True if the password is correct, otherwise False
        """
        if self.logged_in:
            return False
        if self.password_hash == self._hash_password(password):
            self.logged_in = True
            return True
        return False

    def logout(self):
        """
        Logs the user out.
        """
        if not self.logged_in:
            return False
        self.logged_in = False

    def get_status(self) -> dict:
        """
        Returns the current status of the user.
        :return: Dictionary with user information
        """
        return {
            "user_id": self.user_id,
            "username": self.username,
            "logged_in": self.logged_in
        }
    
    def can_control(self): #used later
        return self.role in ("admin", "regular")

    def can_modify_structure(self): #used later
        return self.role == "admin"


    def __str__(self):
        """
        Returns a string representation of the user.
        """
        return f"User {self.username} - Logged in: {self.logged_in}"


#class for managing multiple user ids, NOT for threading specifically
class UserManager:
    def __init__(self):
        self.users_by_name = {}
        self.next_user_id = 1

    def add_user(self, username, password, role="regular"):
        if username in self.users_by_name:
            raise ValueError("Username already exists")
        user = User(self.next_user_id, username, password, role)
        self.users_by_name[username] = user
        self.next_user_id += 1
        return user

    def get_user(self, username):
        return self.users_by_name.get(username)

    def authenticate_user(self, username, password):
        user = self.get_user(username)
        if user and user.authenticate(password):
            return user
        return None

class HouseManager:
    def __init__(self):
        self.houses = {}  # {house_id: SmartHouse}
        self.next_house_id = 1

    def create_house(self, name, admin_user):
        house = SmartHouse(self.next_house_id, name)
        self.houses[self.next_house_id] = house
        admin_user.accessible_houses.add(self.next_house_id)
        self.next_house_id += 1
        return house

    def get_house(self, house_id):
        return self.houses.get(house_id)

class Room:
    def __init__(self, room_id: int, name: str, ceiling_light=None, blinds=None):
        self.room_id = room_id
        self.name = name
        self.house = None  # will be set by set_house(...)
        
        self.devices = {}   # { device_id: device_object }
        self.ceiling_light = None
        self.blinds = None
        
        # If the caller passes in an initial ceiling_light or blinds,
        # we will assign IDs only after we know the house reference.

        self._pending_ceiling_light = ceiling_light
        self._pending_blinds = blinds

    def set_house(self, house):
        """Called by SmartHouse when adding this room, so we can assign device IDs."""
        self.house = house

        # If we had pending single-instance devices at init, now we can assign them
        if self._pending_ceiling_light:
            self.add_ceiling_light(self._pending_ceiling_light)
        if self._pending_blinds:
            self.add_blinds(self._pending_blinds)

        # Clear pending
        self._pending_ceiling_light = None
        self._pending_blinds = None

    def _assign_device_id(self, device):
        """Ask the House for a globally unique ID."""
        if not self.house:
            raise RuntimeError("This room doesn't belong to a house yet.")
        new_id = self.house.get_next_device_id()
        device.device_id = new_id
        self.devices[new_id] = device

    def add_devices(self, lamps=None, locks=None):
        for lamp in (lamps or []):
            self.add_lamp(lamp)
        for lock in (locks or []):
            self.add_lock(lock)

    def add_lamp(self, lamp):
        if lamp in self.devices.values():
            raise ValueError("This lamp is already in the room.")
        self._assign_device_id(lamp)

    def add_lock(self, lock):
        if lock in self.devices.values():
            raise ValueError("This lock is already in the room.")
        self._assign_device_id(lock)

    def add_ceiling_light(self, ceiling_light):
        if self.ceiling_light is not None:
            raise ValueError("Ceiling light already exists. Cannot replace it.")
        if not self.house:
            # We haven't joined a house yet, so store it for later
            self._pending_ceiling_light = ceiling_light
            return
        # Otherwise, assign it now
        self._assign_device_id(ceiling_light)
        self.ceiling_light = ceiling_light

    def add_blinds(self, blinds):
        if self.blinds is not None:
            raise ValueError("Blinds already exist. Cannot replace them.")
        if not self.house:
            self._pending_blinds = blinds
            return
        self._assign_device_id(blinds)
        self.blinds = blinds

    def get_device(self, device_id: int):
        return self.devices.get(device_id)

    def check_status(self):
        status_dict = {}
        for device_id, device_obj in self.devices.items():
            status_dict[device_id] = device_obj.check_status()
        if self.ceiling_light:
            status_dict["ceiling_light"] = self.ceiling_light.check_status()
        if self.blinds:
            status_dict["blinds"] = self.blinds.check_status()
        return status_dict

    def __str__(self):
        return f"Room {self.room_id} ({self.name}) => {self.check_status()}"


class Alarm:
    def __init__(self, code: int):
        self.code = code
        self.is_armed = False
        self.is_alarm = False
        self.house = None  # set when assigned
        self.failed_attempts_by_lock = {}

    def link_house(self, house):
        self.house = house

    def notify_wrong_code(self, lock_id):
        self.failed_attempts_by_lock[lock_id] = self.failed_attempts_by_lock.get(lock_id, 0) + 1
        if self.failed_attempts_by_lock[lock_id] >= 3:
            self.trigger_alarm()

    def trigger_alarm(self):
        if self.is_armed:
            self.is_alarm = True
            print("[ALARM TRIGGERED] Excessive failed attempts on lock!")

    def disarm(self):
        self.is_armed = False
        self.is_alarm = False
        self.failed_attempts_by_lock.clear()


class Lamp:
    def __init__(self, device_id: int, on: bool = False, shade: int = 100, color: str = "white"):
        """
        Initialize a Lamp.
        :param device_id: Unique identifier for the lamp
        :param on: Whether the lamp is on or off (default: False)
        :param shade: Brightness level (0-100, default: 100)
        :param color: Lamp color (default: white)
        """
        self.device_id = device_id
        self.on = on
        self.shade = max(0, min(100, shade))  # Ensure brightness is within range
        self.color = color.lower()  # Store color in lowercase for consistency

    def flip_switch(self):
        """Toggle the lamp on/off."""
        self.on = not self.on

    def set_shade(self, level: int):
        """Set the brightness of the lamp."""
        if 0 <= level <= 100:
            self.shade = level
        else:
            raise ValueError("Shade level must be between 0 and 100.")

    def change_color(self, new_color: str):
        """Change the color of the lamp."""
        valid_colors = ["red", "green", "blue", "white", "yellow", "purple", "orange"]
        if new_color.lower() in valid_colors:
            self.color = new_color.lower()
        else:
            raise ValueError(f"Invalid color '{new_color}'. Supported colors: {', '.join(valid_colors)}.")

    def check_status(self):
        """Returns the current status of the lamp."""
        return {
            "device_id": self.device_id,
            "on": self.on,
            "shade": self.shade,
            "color": self.color
        }

    def __str__(self):
        """Returns a string representation of the lamp."""
        return f"Lamp {self.device_id}: {'On' if self.on else 'Off'}, Shade: {self.shade}, Color: {self.color}"


class CeilingLight:
    def __init__(self, device_id: int, on: bool = False, shade: int = 100, color: str = "white"):
        """
        Initialize a Ceiling Light.
        :param device_id: Unique identifier for the ceiling light
        :param on: Whether the light is on or off (default: False)
        :param shade: Brightness level (0-100, default: 100)
        :param color: Light color (default: white)
        """
        self.device_id = device_id
        self.on = on
        self.shade = max(0, min(100, shade))  # Ensure brightness is within range
        self.color = color.lower()

    def flip_switch(self):
        """Toggle the ceiling light on/off."""
        self.on = not self.on

    def set_shade(self, level: int):
        """Set the brightness of the ceiling light."""
        if 0 <= level <= 100:
            self.shade = level
        else:
            raise ValueError("Shade level must be between 0 and 100.")

    def change_color(self, new_color: str):
        """Change the color of the ceiling light."""
        valid_colors = ["red", "green", "blue", "white", "yellow", "purple", "orange"]
        if new_color.lower() in valid_colors:
            self.color = new_color.lower()
        else:
            raise ValueError(f"Invalid color '{new_color}'. Supported colors: {', '.join(valid_colors)}.")

    def check_status(self):
        """Returns the current status of the ceiling light."""
        return {
            "device_id": self.device_id,
            "on": self.on,
            "shade": self.shade,
            "color": self.color
        }

    def __str__(self):
        """Returns a string representation of the ceiling light."""
        return f"CeilingLight {self.device_id}: {'On' if self.on else 'Off'}, Shade: {self.shade}, Color: {self.color}"



class Lock:
    def __init__(self, device_id: int, code: list[int], is_unlocked: bool = False):
        """
        Initialize a Lock.
        :param device_id: Unique identifier for the lock
        :param code: Security code required to unlock
        :param is_unlocked: Whether the lock is initially unlocked (default: False)
        """
        self.device_id = device_id
        self._code = code  
        self.is_unlocked = is_unlocked
        self.failed_attempts = 0  # Track incorrect unlock attempts

    def lock(self):
        """Lock the door."""
        self.is_unlocked = False

    def unlock(self, user_code: str) -> bool:
        """
        Attempt to unlock the door.
        :param user_code: Code entered by the user
        :return: True if unlocked successfully, False otherwise
        """
        if user_code in self._code:
            self.is_unlocked = True
            self.failed_attempts = 0  # Reset failed attempts
            return True
        else:
            self.failed_attempts += 1
            return False

    def check_status(self):
        """Returns the current status of the lock."""
        return {
            "device_id": self.device_id,
            "is_unlocked": self.is_unlocked,
            "failed_attempts": self.failed_attempts
        }

    def __str__(self):
        """Returns a string representation of the lock."""
        return f"Lock {self.device_id}: {'Unlocked' if self.is_unlocked else 'Locked'}"

class Blinds:
    def __init__(self, device_id: int, is_up: bool = True, is_open: bool = False):
        """
        Initialize Blinds.
        :param device_id: Unique identifier for the blinds
        :param is_up: Whether the blinds are initially up (default: True)
        """
        self.device_id = device_id
        self.is_up = is_up  # True = Up, False = Down
        self.is_open = is_open # True = open, False = closed

    def toggle(self):
        """Toggle the blinds up/down."""
        self.is_up = not self.is_up

    def shutter(self):
        """Open or close the blinds"""
        self.is_open = not self.is_open


    def check_status(self):
        """Returns the current status of the blinds."""
        return {
            "device_id": self.device_id,
            "is_up": self.is_up,
            "is_open" : self.is_open
        }

    def __str__(self):
        """Returns a string representation of the blinds."""
        return f"Blinds {self.device_id}: {'Up' if self.is_up else 'Down'}"


class SmartHouse:
    
    def __init__(self, house_id: int, name: str):
        self.house_id = house_id
        self.name = name
        self.rooms = {}  # { room_id: Room }
        self.alarm = None #only one cane exist
        self.next_device_id = 1  # <--- Global device ID for the whole house

    def get_next_device_id(self) -> int:
        """Return a globally unique device ID."""
        new_id = self.next_device_id
        self.next_device_id += 1
        return new_id

    def add_room(self, room):
        """
        Add a room to the house.
        :param room: A Room object
        """
        if room.room_id in self.rooms:
            raise ValueError(f"Room ID {room.room_id} already exists in the house.")
        
        # Let the Room know which house it belongs to (for ID assignment)
        room.set_house(self)
        self.rooms[room.room_id] = room
    
    
    def remove_room(self, room_id: int):
        """
        Remove a room from the house by its ID.
        :param room_id: The ID of the room to remove
        """
        if room_id in self.rooms:
            del self.rooms[room_id]
        else:
            raise ValueError(f"Room ID {room_id} not found in this house.")

    def get_room(self, room_id: int):
        """
        Retrieve a room by its ID.
        :param room_id: The ID of the room to retrieve
        :return: The Room object or None if not found
        """
        return self.rooms.get(room_id, None)

    def check_status(self):
        """
        Returns the status of all rooms and their devices in the house.
        :return: Dictionary containing all rooms and their device statuses
        """
        return {room_id: room.check_status() for room_id, room in self.rooms.items()}

    def set_alarm(self, alarm):
        if self.alarm is not None:
            raise ValueError("Alarm already exists in this house")
        self.alarm = alarm
        alarm.link_house(self)

    def __str__(self):
        """
        Returns a string representation of the house and its rooms.
        """
        return f"SmartHouse {self.house_id} - {self.name}, Rooms: {list(self.rooms.keys())}"


    