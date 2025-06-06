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
envelope.set("input", sine)
lpf.set("input", sine)
SYNTH.output.set("input", lpf)

envelope.attack = 0.8
envelope.decay = 0.8
envelope.release = 0.8


def messure():
    # for i in range(100):
    #     sine.read()

    t1 = time.time_ns()
    for i in range(100):
        # x.readinto(buffer, len(buffer))
        SYNTH.get_buffer()
        if not envelope.is_active():
            envelope.trigger_attack()
        elif envelope.is_sustaining():
            envelope.trigger_release()
        
        # SYNTH.get_buffer()
    t2 = time.time_ns()

    t = (t2 - t1) / 1e9

    print(f"Time taken for 100 buffer fetches: {t:.4f} seconds")


messure()
LEDS.set_led_on(3)