# -*- coding: utf-8 -*-
"""
Created on Wed Oct 28 21:43:35 2015

@author: christopher
"""

# Libraries
import communication
import pi2go
import time
from crashing_constants import *

# Initail Values
state = 'INIT'
mode = 'STOP'
prev_mode = 'STOP'
distance = 0
squad = []
prev_messurement_time = 0
message_buffer_slave = []
message_buffer_master = []


# Programm
try:
    while True:
        
        if state == 'INIT':
            pi2go.init()
            sock = communication.init_nonblocking_receiver('',PORT)
            for x in range(SQUAD_SIZE):
                squad.append(True)
                message_buffer_slave.append(True)
            OWN_IP = communication.get_ip()
            OWN_IDENTIFIER = communication.get_id_from_ip(OWN_IP)
            print OWN_IDENTIFIER
            state = 'RUNNING'


        elif state == 'RUNNING':
            # distance         
            if time.time() - prev_messurement_time > WAIT_DIST:
                prev_messurement_time = time.time()                
                distance = pi2go.getdistance()
            
            # Obstacle = 1, No Obstacle = 0
            irCentre = pi2go.irCentre()
            
            # Obstacle Analysis
            if irCentre or (distance < DIST_MIN):
                distance_area = 0
            elif distance > DIST_MAX:
                distance_area = 2
            else:
                distance_area = 1
                
            # Receive
            data = 'new_round'
            while data != '':
                data, addr = communication.receive_message(sock) 
                if data != '':
                    ID = communication.get_id_from_ip(addr[0])
                    if identifier == OWN_IDENTIFIER:
                        print 'OWN: ' , identifier, ' : ' , data
                        continue
                    if identifier >= SQUAD_START and identifier <= SQUAD_START+SQUAD_SIZE:
                        print 'ROBOT: ', identifier, ' : ' , data
                        if data == 'PROBLEM':
                            curr_status = False
                            #squad[id-SQUAD_START] = curr_status
                            squad[identifier] = curr_status
                        elif data == 'RELEASE':
                            curr_status = True
                            #squad[id-SQUAD_START] = curr_status
                            squad[identifier] = curr_status
                    else:
                        print 'MASTER:' , identifier , ' : ' , data
                        # make List with Master commands an react on this
                        # change mode, STATUS, SPEED, distanceLIMITS
                    
            # Analyse --> Calculate mode
            prev_mode = mode
            if distance_area == 0:
                mode = 'STOP'
            elif distance_area == 1 and all(squad):
                mode = 'SLOW'
            elif distance_area == 2 and all(squad):
                mode = 'RUN'
            elif distance_area != 0 and not all(squad):
                mode = 'WARN'
            else:
                print 'check mode-Conditions'
                break
            
            # Set own SQUAD_VALUE  
            if mode != prev_mode:                          
                if mode == 'STOP':
                    #squad[OWN_IDENTIFIER-SQUAD_START] = False
                    squad[OWN_IDENTIFIER] = False
                else:
                    #squad[OWN_IDENTIFIER-SQUAD_START] = True
                    squad[OWN_IDENTIFIER] = True

            # LEDs  
            if mode != prev_mode:                          
                if mode == 'RUN':
                    pi2go.setAllLEDs(LED_OFF,LED_ON,LED_OFF)
                elif mode == 'SLOW':
                    pi2go.setAllLEDs(LED_OFF,LED_OFF,LED_ON)
                elif mode == 'WARN':
                    pi2go.setAllLEDs(LED_ON,LED_ON,LED_OFF)
                elif mode == 'STOP':
                    pi2go.setAllLEDs(LED_ON,LED_OFF,LED_OFF)
                    
            # distance controller
            if mode == 'SLOW':
                SPEED_SLOW = SPEED_RUN - (DIST_REF-distance) * KP
                # Controlllimits
                if SPEED_SLOW > SPEED_CONTROL_MAX:
                    SPEED_SLOW = SPEED_CONTROL_MAX
                elif SPEED_SLOW < SPEED_CONTROL_MIN:
                    SPEED_SLOW = SPEED_CONTROL_MIN
                print 'DIST: ', distance , 'SPEED: ', SPEED_SLOW
                        
            
            # Motor
            if mode != prev_mode:                          
                if mode == 'RUN':
                    speed = SPEED_RUN
                elif mode == 'SLOW':
                    speed = SPEED_SLOW
                elif mode == 'WARN':
                    speed = SPEED_WARN
                elif mode == 'STOP':
                    speed = SPEED_STOP 
                # Speedlimits
                if speed > 100:
                    speed = 100
                elif speed < 0:
                    speed = 0
                pi2go.go(speed,speed)
                
            # Send
            if mode != prev_mode:                          
                if prev_mode == 'STOP':
                    #print 'RELEASE'
                    message = 'RELEASE'
                    for x in range(SENDING_ATTEMPTS):
                        communication.send_broadcast_message(PORT, message)
                        time.sleep(WAIT_SEND)                    
                elif mode == 'STOP':
                    #print 'PROBLEM'
                    message = 'PROBLEM'
                    for x in range(PUSH):
                        communication.send_broadcast_message(PORT, message)
                        time.sleep(WAIT_SEND)
       
        else:
            print 'impossible state'
            state == 'RUNNING'
            
except KeyboardInterrupt:
    print 'KEYBOARD'

finally:
    pi2go.stop()
    pi2go.cleanup()
    sock.close()
    print 'END'