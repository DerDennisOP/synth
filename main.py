import time

time.sleep(1)

import input
import asyncio
import synth
import notes
import time
import display
import _thread

BUTTONS = input.Buttons(([13, 12, 11, 10, 9, 8, 7, 6]))
ROTARY_ENCODER = input.RotaryEncoder(26, 27, 28)
LEDS = input.Led([19, 20, 21, 22])
SPEAKER = input.Speaker(buffer_size=600)
SYNTH = synth.Synth(synth.Config())
MENUE = display.Window(SYNTH)

frequency_module = SYNTH.add_module(synth.Input)
frequency_module2 = SYNTH.add_module(synth.Input)
frequency_module3 = SYNTH.add_module(synth.Input)
volume_sine = SYNTH.add_module(synth.Sine)
base_sine = SYNTH.add_module(synth.Sine)
sine = SYNTH.add_module(synth.Sine)
# saw = SYNTH.add_module(synth.Sawtooth)
# square = SYNTH.add_module(synth.Square)
# triangle = SYNTH.add_module(synth.Triangle)
# mixer1 = SYNTH.add_module(synth.Mixer)
# mixer2 = SYNTH.add_module(synth.Mixer)
# mixer3 = SYNTH.add_module(synth.Mixer)
# mixer4 = SYNTH.add_module(synth.Mixer)
# mixer5 = SYNTH.add_module(synth.Mixer)
# mixer6 = SYNTH.add_module(synth.Mixer)
mixer = SYNTH.add_module(synth.Mixer)
envelope = SYNTH.add_module(synth.Envelope)
lpf = SYNTH.add_module(synth.LowPassFilter)
hpf = SYNTH.add_module(synth.HighPassFilter)
noise = SYNTH.add_module(synth.Noise)
shifter = SYNTH.add_module(synth.PitchShifter)
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
# saw.set("frequency", frequency_module)
# square.set("frequency", frequency_module)
# triangle.set("frequency", frequency_module)

mixer.set("input0", sine)
mixer.set("input1", base_sine)
mixer.set("input1_volume", volume_sine)
# mixer.set("2", mixer2)
# mixer2.set("0", mixer3)
# mixer3.set("0", mixer4)
# mixer4.set("0", mixer5)
# mixer5.set("0", mixer6)
# mixer6.set("0", saw)
# SYNTH.get_module(mixer).add_channel(saw)
shifter.set("input", mixer)
envelope.set("input", mixer)
lpf.set("input", envelope)
hpf.set("input", envelope)
SYNTH.output.set("input", lpf)


_thread.start_new_thread(MENUE.display, ())


async def updatespeaker():
    stream = asyncio.StreamWriter(SPEAKER.audio)
    next_buffer = SYNTH.get_buffer()
    stream.write(next_buffer)
    while True:
        if MENUE.display_state == "Graph":
            MENUE.set_buffer(SYNTH.read())
        next_buffer = SYNTH.get_buffer()
        # print(sine.read())
        # print(next_buffer)
        await stream.drain()
        stream.write(next_buffer)


def record_loop(pause_time, freq, time):
    global loop_buffer
    loop_buffer.append([pause_time, freq, time])


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


input_frequency = 440  # Beispiel: A4
pentatonik_frequencies = pentatonik(input_frequency)
# SYNTH.output.set_amplitude(10)


async def main():
    global is_recording, is_playing, loop_buffer, last_press_time
    encoder = ROTARY_ENCODER
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

    SYNTH.output.set_amplitude(20)

    while True:
        for i, button in enumerate(buttons.get_buttons()):

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
                    if (
                        looping is None and loop_buffer != []
                    ):  # Wenn keine Aufgabe läuft
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
                    if MENUE.get_menu_state() == "New_Module_Menu":
                        MENUE.add_module()
                    else:
                        # Switch to new module menu or other functionality
                        pass

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
                    record_loop(time_pause, last_freq, time_press)
                    record = False

        encoder_pos = encoder.get_position()
        encoder_pressed = encoder.is_pressed()
        MENUE.get_encoder_state(encoder_pos, encoder_pressed)

        # Debug output (remove this later)
        if encoder_pos != 0 or encoder_pressed:
            print(f"Encoder - Position: {encoder_pos}, Pressed: {encoder_pressed}")

        # Update button states for menu system
        button_states = []
        for button in buttons.get_buttons()[:3]:  # Only first 3 buttons for menu
            button_states.append(button.is_pressed)
        MENUE.set_button_states(button_states)

        # SYNTH.output.set_amplitude(p.get_state(0,20)*2)
        # pentatonik_frequencies = pentatonik(notes.tones["A"+ str(2 + p[1])])
        # frequency_module2.set_value(1+p.get_state(1,20)*40)

        await asyncio.sleep(0.1)  # Kurze Pause, um die Ausgabe zu steuern


try:
    asyncio.run(main())
finally:
    LEDS.set_led_on(0)
    LEDS.set_led_off(3)
