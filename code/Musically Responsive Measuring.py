from synthesizer import Player, Synthesizer, Waveform
import serial
import serial.tools.list_ports
import sys
import crcmod.predefined
import os
import json
import time

DATA_PATH = os.path.dirname(__file__)
GH_JSON = 'JSON_from_GH.json' # name of JSON file from Grasshopper

player = Player()
player.open_stream()
synthesizer = Synthesizer(osc1_waveform=Waveform.sine, osc1_volume=1.0, use_osc2=False)
synthesizer2 = Synthesizer(osc1_waveform=Waveform.sine, osc1_volume=1.0, use_osc2=True, osc2_waveform=Waveform.triangle)

fab_dists = [] # empty list to append measured distances to
fab_tones = [] # empty list to append measurement tones to
tolerance_counter = [] # empty list for counting number of consecutive times a measured distance is in a range

audio_range = [100, 600] # comfortable range for audio scale in herz
audio_time = 0.1 # how long each audio tone is played for, also determines how often a measurement is taken

# all distance units are in meters
measure_range = [0.2, 2.8] # range within which measurements will be taken

filename = os.path.join(DATA_PATH, GH_JSON)
with open(filename, 'r') as f:
    GH_JSON_dict = json.load(f) # open and load JSON file from Grasshopper

target_dist = float(GH_JSON_dict['target_dist']) # the target distance
tolerable_dist = float(GH_JSON_dict['tolerable_dist']) # value +/- the target_dist for an acceptable tolerance range
toleration_times = int(GH_JSON_dict['toleration_times']) # number of times the distance measurement needs to be within the tolerance range
tol_range = [(target_dist - tolerable_dist), (target_dist + tolerable_dist)]
JSON_name = GH_JSON_dict['export_JSON']

def findEvo():
    # Find Live Ports, return port name if found, NULL if not
    print('Scanning all live ports on this PC')
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        # print(p) # This causes each port's information to be printed out.
        if "5740" in p[2]:
            print('Evo found on port ' + p[0])
            return p[0]
    return 'NULL'

def openEvo(portname):
    print('Attempting to open port...')
    # Open the Evo and catch any exceptions thrown by the OS
    print(portname)
    evo = serial.Serial(portname, baudrate=115200, timeout=2)
    # Send the command "Binary mode"
    set_bin = (0x00, 0x11, 0x02, 0x4C)
    # Flush in the buffer
    evo.flushInput()
    # Write the binary command to the Evo
    evo.write(set_bin)
    # Flush out the buffer
    evo.flushOutput()
    print('Serial port opened')
    return evo

def get_evo_range(evo_serial):
    crc8_fn = crcmod.predefined.mkPredefinedCrcFun('crc-8')
    # Read one byte
    data = evo_serial.read(1)
    if data == b'T':
        # After T read 3 bytes
        frame = data + evo_serial.read(3)
        if frame[3] == crc8_fn(frame[0:3]):
            # Convert binary frame to decimal in shifting by 8 the frame
            rng = frame[1] << 8
            rng = rng | (frame[2] & 0xFF)
        else:
            return "CRC mismatch. Check connection or make sure only one progam access the sensor port."
    # Check special cases (limit values)
    else:
        return "Wating for frame header"

    # Checking error codes
    if rng == 65535: # Sensor measuring above its maximum limit
        dec_out = float('inf')
    elif rng == 1: # Sensor not able to measure
        dec_out = float('nan')
    elif rng == 0: # Sensor detecting object below minimum range
        dec_out = -float('inf')
    else:
        # Convert frame in meters
        dec_out = rng / 1000.0
    return dec_out

def remap(old_val, old_min, old_max, new_min, new_max):
    return ((new_max - new_min) * (old_val - old_min) / (old_max - old_min) + new_min)

def measureLoop(): # connects to evo sensor, then processes measurements until tolerance_counter == toleration_times
    # connect to evo sensor
    print('Starting Evo data streaming')
    # get the port the evo has been connected to
    port = findEvo()
    if port == 'NULL':
        print("Sorry couldn't find the Evo. Exiting.")
        sys.exit()
    else:
        evo = openEvo(port)
        
        tolerance_counter = []
        while len(tolerance_counter) < toleration_times: # measure and play audio loop
            if len(tolerance_counter) > toleration_times: # extra failsafe clause just to make me feel safe
                evo.close()
                break
            
            evo.flushInput()
            evo.flushOutput() # clears the serial buffer for low latency measuring
            dist = get_evo_range(evo) # gets measurement
            
            if type(dist) is not str: # test for errors (measurement outside sensor limits or unable to measure)
                if dist > tol_range[0] and dist < tol_range[1]: # test if 'dist' is in 'tol_range'
                    # if True, play beeping sound and lengthen 'tolerance_counter' list
                    player.play_wave(synthesizer2.generate_constant_wave(700, audio_time / 2))
                    player.play_wave(synthesizer2.generate_constant_wave(100, audio_time / 2))
                    fab_tones.append(700)
                    fab_tones.append(100)
                    fab_dists.append(dist)
                    tolerance_counter.append(1)
                    print(tolerance_counter)
                
                else:
                    # if 'dist' is outside tolerance range, then reset 'tolerance_counter' to an empty list
                    # generate and play tone corresponding to proximity of 'dist' to 'tol_range'
                    # a 'dist' close to 'tol_range' will have a high pitch tone, a 'dist' far from 'tol_range' will have a low pitch tone
                    fab_dists.append(dist)
                    tolerance_counter = []
                    if dist < tol_range[0]: # True if 'dist' is less than low end of 'tol_range'
                        tone = remap(dist, measure_range[0], tol_range[0], audio_range[0], audio_range[1])
                        player.play_wave(synthesizer.generate_constant_wave(tone, audio_time))
                        fab_tones.append(tone)
                    if dist > tol_range[1]: # True if 'dist' is more than high end of 'tol_range'
                        tone = remap(dist, tol_range[1], measure_range[1], audio_range[1], audio_range[0])
                        player.play_wave(synthesizer.generate_constant_wave(tone, audio_time))
                        fab_tones.append(tone)
            print(dist)
        evo.close()

def file_check(exp_path): # check for existing file with the same name
    if os.path.exists(exp_path) == True: # if same named file exists, adds "- Copy" to the end
        ext_len = 5 # this value is the length of the file extension (ex: '.json' = 5, '.wav' = 4)
        exp_path = exp_path[0:-ext_len] + " - Copy" + exp_path[-ext_len:]
        exp_path_new = file_check(exp_path)
        return(exp_path_new)
    elif os.path.exists(exp_path) == False:
        return(exp_path)

if target_dist < measure_range[0] or target_dist > measure_range[1]: # measurable distance failsafe
    print("ERROR!!!\nERROR!!!\nERROR!!!\ntarget_dist is outside measure_range")
    sys.exit()

start_time = time.monotonic()
measureLoop()
end_time = time.monotonic()

# compile fabrication related data as dictionary and save as a JSON file
if __name__ == "__main__":
    JSON_dict = {}
    JSON_dict["target_dist"] = target_dist
    JSON_dict["fab_time"] = end_time - start_time
    JSON_dict["date_time"] = GH_JSON_dict['date_time']
    JSON_dict["tolerable_dist"] = tolerable_dist
    JSON_dict["toleration_times"] = toleration_times
    JSON_dict["measure_range"] = measure_range
    JSON_dict["audio_range"] = audio_range
    JSON_dict["audio_time"] = audio_time
    JSON_dict["fab_dists"] = fab_dists
    JSON_dict["fab_tones"] = fab_tones

export_DATA_PATH = DATA_PATH + "\data\JSON_files"
filename = file_check(os.path.join(export_DATA_PATH, JSON_name))
with open(filename, 'w') as f:
    f.write(json.dumps(JSON_dict, sort_keys=False)) # save data as JSON file

print("Fabrication completed in " + str("%.3f" % (end_time - start_time)) + " seconds.")