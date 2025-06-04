import input
import asyncio
import synth
import notes

BUTTONS = input.Buttons([13, 12, 11,10,9,8,7,6])
POTENTIOMETER = input.Potentiometers([26,27,28])
LEDS = input.Led([19,20,21,22])
SPEAKER = input.Speaker(buffer_size=2000)
SYNTH = synth.Synth(synth.Config())
frequency_module = SYNTH.add_module(synth.Input)
frequency_module2 = SYNTH.add_module(synth.Input)
frequency_module3 = SYNTH.add_module(synth.Input)
volume_sine = SYNTH.add_module(synth.Sine)
base_sine = SYNTH.add_module(synth.Sine)
sine = SYNTH.add_module(synth.Sine)
saw = SYNTH.add_module(synth.Sawtooth)
square = SYNTH.add_module(synth.Square)
triangle = SYNTH.add_module(synth.Triangle)
mixer = SYNTH.add_module(synth.Mixer)
envelope = SYNTH.add_module(synth.Envelope)
lpf = SYNTH.add_module(synth.LowPassFilter)
ak_wave = 0
ak_effect = 0


frequency_module3.set_value(1)
volume_sine.set("frequency", frequency_module3)

frequency_module2.set_value(int(440/4))
base_sine.set("frequency", frequency_module2)

frequency_module.set_value(440)

sine.set("frequency", frequency_module)
saw.set("frequency", frequency_module)
square.set("frequency", frequency_module)
triangle.set("frequency", frequency_module)

mixer.set("0", sine)
mixer.set("1", base_sine)
mixer.set("1_volume", volume_sine)
# SYNTH.get_module(mixer).add_channel(saw)
envelope.set("input", mixer)
# lpf.set("input", envelope)
SYNTH.output.set("input", envelope)


async def updatespeaker():
    stream = asyncio.StreamWriter(SPEAKER.audio)
    NEXT_BUFFER = SYNTH.get_buffer()
    stream.write(NEXT_BUFFER)
    while True:
        NEXT_BUFFER = SYNTH.get_buffer()
        await stream.drain()
        stream.write(NEXT_BUFFER)


def pentatonik(frequency):
    # Intervalle für die Dur-Pentatonik
    intervals = [0, 2, 4, 7, 9]  # Halbtöne für die Pentatonik
    pentatonik_frequencies = []

    for interval in intervals:
        # Berechnung der Frequenz für jeden Ton in der Pentatonik
        note_frequency = frequency * (2 ** (interval / 12))
        pentatonik_frequencies.append(note_frequency)

    return pentatonik_frequencies


def tooggle_wave():
    global ak_wave
    ak_wave += 1
    if ak_wave > 3:
        ak_wave = 0

    if ak_wave == 0:
        print("sine")
        mixer.set(0, sine)
    elif ak_wave == 1:
        print("saw")
        mixer.set(0, saw)
    elif ak_wave == 2:
        print("square")
        mixer.set(0, square)
    elif ak_wave == 3:
        print("triangle")
        mixer.set(0, triangle)
        
def toggle_effects():
    global ak_effect
    ak_effect += 1
    if ak_effect > 3:
        ak_effect = 0
    if ak_effect == 0:
        pass
    elif ak_effect == 1:
        pass
    elif ak_effect == 2:
        pass
    elif ak_effect == 3:
        print("heheheheheh")
        pass

# Beispielaufruf
input_frequency = 440  # Beispiel: A4
pentatonik_frequencies = pentatonik(input_frequency)

async def main():
    potentiometers = POTENTIOMETER
    buttons = BUTTONS
    asyncio.create_task(updatespeaker())
#     asyncio.create_task(loadbuffer())
    LEDS.set_led_off(0)
    LEDS.set_led_on(3)
    pressd = False
    while True:
        potentiometers.update()
        p = potentiometers.get_state([40,3,1])
        if buttons.last_pressed is not None:
            n = buttons.last_pressed.pin
            # if n-6 <= 2 and n-6 >= 0:
            #     LEDS.toggle_led(2-(n-6))
            #     #settings
            #     pass
            if n == 8:
                tooggle_wave()
            if n == 7:
                toggle_effects()
            elif n-9 <= 5 and n-9 >= 0:
                frequency_module.set_value(int(pentatonik_frequencies[n-9]))
                envelope.trigger_attack()
                pressd = True
                LEDS.set_led_on(2)
                LEDS.set_led_off(1)
        elif pressd:
            LEDS.set_led_off(2)
            LEDS.set_led_on(1)
            pressd = False
            envelope.trigger_release()

        SYNTH.output.set_amplitude(p[0])
        #pentatonik_frequencies = pentatonik(notes.tones["A"+ str(2 + p[1])])

        await asyncio.sleep(0.1)  # Kurze Pause, um die Ausgabe zu steuern

try:
    asyncio.run(main())
finally:
    LEDS.set_led_on(0)
    LEDS.set_led_off(3)