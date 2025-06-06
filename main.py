import time

time.sleep(1)

import input
import asyncio
import synth
import notes
import time
import display
import _thread

BUTTONS = input.Buttons(([13, 12, 11,10,9,8,7,6]))
POTENTIOMETER = input.Potentiometers([26,27,28],3.3)
LEDS = input.Led([19,20,21,22])
SPEAKER = input.Speaker(buffer_size=600)
SYNTH = synth.Synth(synth.Config())
MENUE = display.Window(SYNTH)
_thread.start_new_thread(MENUE.display, ())
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
loop_buffer = []
is_recording = False
is_playing = False


frequency_module3.set_value(1)
volume_sine.set("frequency", frequency_module3)
frequency_module2.set_value(443)
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
    next_buffer = SYNTH.get_buffer()
    stream.write(next_buffer)
    while True:
        if MENUE.display_state == "Graph":
            MENUE.set_buffer(SYNTH.read())
        next_buffer = SYNTH.get_buffer()
        await stream.drain()
        stream.write(next_buffer)

def record_loop(pause_time,freq,time):
    global loop_buffer
    loop_buffer.append([pause_time,freq,time])
    
async def play_loop():
    while True:
        for pause_time, freq, time in loop_buffer:
            await asyncio.sleep_ms(pause_time)  
            frequency_module.set_value(freq)
            envelope.trigger_attack()
            await asyncio.sleep_ms(time)
            envelope.trigger_release()
        await asyncio.sleep(0.5)

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
        pass

input_frequency = 440  # Beispiel: A4
pentatonik_frequencies = pentatonik(input_frequency)
# SYNTH.output.set_amplitude(10)

async def main():
    global is_recording, is_playing, loop_buffer, last_press_time
    p = POTENTIOMETER
    buttons = BUTTONS
    asyncio.create_task(updatespeaker())
    LEDS.set_led_off(0)
    LEDS.set_led_on(3)
    pressd = False
    last_press_time = time.ticks_ms()
    last_freq = 0
    time_pause = 0
    record = False
    looping = None
    
    MENUE.get_modulelist(SYNTH.get_modules())
    
    SYNTH.output.set_amplitude(10)

    while True:
        for i , button in enumerate(buttons.get_buttons()):
        
            if button.is_pressed and not pressd:
                time_pause = time.ticks_ms() - last_press_time
                last_press_time = time.ticks_ms()
                pressd = True

                if i <= 4 and i >= 0:
                    frequency_module.set_value(int(pentatonik_frequencies[i]))
                    last_freq = int(pentatonik_frequencies[i])
                    envelope.trigger_attack()
                    LEDS.set_led_on(2)
                    LEDS.set_led_off(1)
                    if looping is None:
                        record = True
                        last_freq = int(pentatonik_frequencies[i])
        
                elif i == 5:  # Aufnahme starten/stoppen
                    if looping is None and loop_buffer != []:  # Wenn keine Aufgabe läuft
                        print("loop")
                        looping = asyncio.create_task(play_loop())  # Starte die Aufgabe
                    elif looping is not None:  # Wenn die Aufgabe läuft
                        print("cancel")
                        looping.cancel()
                        await asyncio.sleep(0.05)
                        looping = None  # Setze looping zurück
                        loop_buffer = []
                    else:
                        print("kein loop")
                elif i == 6:  # Loop abspielen
                    pass

                elif i == 7:
                    MENUE.add_module() 

                break
                
            elif all(button.is_released for button in buttons.get_buttons()) and pressd:
                LEDS.set_led_off(2)
                LEDS.set_led_on(1)
                envelope.trigger_release()
                pressd = False
                time_press = time.ticks_ms() - last_press_time
                last_press_time = time.ticks_ms()
                if record:
                    if len(loop_buffer) == 0:
                        time_pause = 0
                    record_loop(time_pause,last_freq,time_press)
                    record = False

        
        MENUE.set_aimcross(p.get_state(0,16)*10,p.get_state(1,16)*8)
        MENUE.set_selected_module(p.get_state(0,7))
        
        #SYNTH.output.set_amplitude(p.get_state(0,20)*2)
        #pentatonik_frequencies = pentatonik(notes.tones["A"+ str(2 + p[1])])
        #frequency_module2.set_value(1+p.get_state(1,20)*40)

        await asyncio.sleep(0.1)  # Kurze Pause, um die Ausgabe zu steuern

try:
    asyncio.run(main())
finally:
    LEDS.set_led_on(0)
    LEDS.set_led_off(3)