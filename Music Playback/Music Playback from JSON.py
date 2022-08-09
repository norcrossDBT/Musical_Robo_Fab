from synthesizer import Player, Synthesizer, Waveform, Writer
import sys
import os
import json

data_Path = os.path.dirname(__file__)

JSON_Name = 'test_8-9-2022.json' # JSON file from 'Musically Responsive Measuring.py'
WAV_Name = '8-9.wav' # file name for .wav audio file

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


# export wav file
export_Path = data_Path + '/' + WAV_Name

writer.write_waves(export_Path, *wave)