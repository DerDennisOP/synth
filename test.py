import time
import synth
import array
import input

LEDS = input.Led([19,20,21,22])
CONFIG = synth.Config()
CONFIG.sample_rate = 1024
SYNTH = synth.Synth(CONFIG)
frequency = SYNTH.add_module(synth.Input)
sine = SYNTH.add_module(synth.Sine)
saw = SYNTH.add_module(synth.Sawtooth)
square = SYNTH.add_module(synth.Sawtooth)
mixer = SYNTH.add_module(synth.Mixer)
envelope = SYNTH.add_module(synth.Envelope)
lpf = SYNTH.add_module(synth.LowPassFilter)

frequency.set_value(1)
sine.set("frequency", frequency)
saw.set("frequency", frequency)
square.set("frequency", frequency)
SYNTH.output.set("input", square)

# SYNTH.get_module(mixer).add_channel(sine)
# SYNTH.get_module(mixer).add_channel(saw)
# SYNTH.get_module(envelope).set(mixer)
# SYNTH.get_module(lpf).set(envelope)

def messure():
    # for i in range(100):
    #     sine.read()

    t1 = time.time_ns()
    for i in range(1):
        # x.readinto(buffer, len(buffer))
        # x.read()
        
        print(SYNTH.get_buffer())
        print(sine.lut)
    t2 = time.time_ns()

    t = (t2 - t1) / 1e9

    print(f"Time taken for 100 buffer fetches: {t:.4f} seconds")


messure()
LEDS.set_led_on(3)