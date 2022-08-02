from synthesizer import Player, Synthesizer, Waveform, Writer
import sys
import os
import json

data_Path = os.path.dirname(__file__)

JSON_Name = 'test.json'
WAV_Name = 'test.wav'

player = Player()
player.open_stream()
synthesizer = Synthesizer(osc1_waveform=Waveform.sine, osc1_volume=1.0, use_osc2=False)
writer = Writer()

filename = os.path.join(data_Path, JSON_Name)
with open(filename, 'r') as f:
    JSON_data = json.load(f)

wave = []
for i in JSON_data:
    player.play_wave(synthesizer.generate_constant_wave(i, 0.1))
    wave.append(synthesizer.generate_constant_wave(i, 0.1))

export_Path = data_Path + '/' + WAV_Name

writer.write_waves(export_Path, *wave)