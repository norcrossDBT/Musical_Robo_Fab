from synthesizer import Player, Synthesizer, Waveform, Writer
import sys
import os
import json

data_Path = os.path.dirname(__file__)
JSON_Name = input("\nPlease type name of JSON file, don't include '.json'.\nPress Enter to continue\n") # JSON file from 'Musically Responsive Measuring.py'
JSON_Name += '.json'
save_wav = int(input("\nType 1 to save a .wav file of the fabrication audio, otherwise type 0.\nPress Enter to continue\n")) # toggle to save playback as .wav file or not

player = Player()
player.open_stream()
synthesizer = Synthesizer(osc1_waveform=Waveform.sine, osc1_volume=1.0, use_osc2=False)
synthesizer2 = Synthesizer(osc1_waveform=Waveform.sine, osc1_volume=1.0, use_osc2=True, osc2_waveform=Waveform.triangle)
writer = Writer()

filename = os.path.join(data_Path, JSON_Name)

with open(filename, 'r') as f:
    JSON_dict = json.load(f) # open and load JSON file

wave = [] # empty list to append waves to

# playback tones heard during fabrication
for freq in JSON_dict['fab_tones']:
    if freq == 700 or 100:
        player.play_wave(synthesizer2.generate_constant_wave(freq, JSON_dict['audio_time'] / 2))
        wave.append(synthesizer2.generate_constant_wave(freq, JSON_dict['audio_time'] / 2))
    else:
        player.play_wave(synthesizer.generate_constant_wave(freq, JSON_dict['audio_time']))
        wave.append(synthesizer.generate_constant_wave(freq, JSON_dict['audio_time']))

def file_check(exp_path): # check for existing file with the same name
    if os.path.exists(exp_path) == True: # if same named file exists, adds "- Copy" to the end
        ext_len = 4 # this value is the length of the file extension (ex: '.json' = 5, '.wav' = 4)
        exp_path = exp_path[0:-ext_len] + " - Copy" + exp_path[-ext_len:]
        exp_path_new = file_check(exp_path)
        return(exp_path_new)
    elif os.path.exists(exp_path) == False:
        return(exp_path)

# export wav file
if save_wav == 1:
    WAV_Name = input("\nPlease type name of wav file, don't include '.wav'.\nPress Enter to continue\n") # file name for .wav audio file
    export_Path = file_check(data_Path + '/' + WAV_Name + '.wav')
    writer.write_waves(export_Path, *wave)