from home_model import SmartHouse, Room, CeilingLight, Blinds, Lamp, Lock

def create_sample_smart_house():
    # Create the SmartHouse
    house = SmartHouse(house_id=1, name="My Smart Home")
    
    '''  
    Room 1: Living Room
     - Has a ceiling light & blinds at init
     - 2 lamps, 1 lock added
    '''
    living_room = Room(
        room_id=101, 
        name="Living Room",
        ceiling_light=CeilingLight(device_id=0, on=True, shade=75),
        blinds=Blinds(device_id=0, is_up=True)
    )
    # Add multiple lamps & a lock
    lamp1 = Lamp(device_id=0, on=True, shade=60)
    lamp2 = Lamp(device_id=0, on=False, shade=100)
    lock1 = Lock(device_id=0, code="1234", is_unlocked=False)
    living_room.add_devices(lamps=[lamp1, lamp2], locks=[lock1])
    
    house.add_room(living_room)
    
    '''
    Room 2: Bedroom
     - No ceiling light or blinds
     - 1 lamp, 1 lock
    '''
    bedroom = Room(room_id=102, name="Bedroom")
    
    lamp3 = Lamp(device_id=0, on=False, shade=50)
    lock2 = Lock(device_id=0, code="5678", is_unlocked=True)
    bedroom.add_devices(lamps=[lamp3], locks=[lock2])
    
    house.add_room(bedroom)
    
    '''
    Room 3: Kitchen
     - 1 ceiling light, no blinds
     - No lamps added
     - 2 locks
     '''

    kitchen = Room(
        room_id=103, 
        name="Kitchen",
        ceiling_light=CeilingLight(device_id=0, on=False, shade=100)
    )
    
    lock3 = Lock(device_id=0, code="4321", is_unlocked=False)
    lock4 = Lock(device_id=0, code="9999", is_unlocked=False)
    kitchen.add_devices(locks=[lock3, lock4])
    
    house.add_room(kitchen)
    
    '''
    Room 4: Bathroom
     - 1 blinds, no ceiling light
     - 1 lamp
    '''

    bathroom = Room(
        room_id=104, 
        name="Bathroom",
        blinds=Blinds(device_id=0, is_up=False)
    )
    
    lamp4 = Lamp(device_id=0, on=True, shade=30)
    bathroom.add_lamp(lamp4)
    
    house.add_room(bathroom)
    '''
    Room 5: Guest Room
     - 1 ceiling light, no blinds
     - 1 lamp, 1 lock
    '''

    guest_room = Room(
        room_id=105, 
        name="Guest Room",
        ceiling_light=CeilingLight(device_id=0, on=True, shade=80)
    )
    
    lamp5 = Lamp(device_id=0, on=False, shade=100)
    lock5 = Lock(device_id=0, code="1111", is_unlocked=False)
    guest_room.add_devices(lamps=[lamp5], locks=[lock5])
    
    house.add_room(guest_room)
    
    return house

#test case

if __name__ == "__main__":
    my_house = create_sample_smart_house()
    
    # Print the overall status of the house
    print("===== My Smart House Status =====")
    print(my_house.check_status())
    
    # Print status of a specific room
    living_room_status = my_house.get_room(101).check_status()
    print("\nLiving Room Status:")
    print(living_room_status)
    
    # Print the final house representation
    print("\nString Representation of House:")
    print(my_house)


