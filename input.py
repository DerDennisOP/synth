from picozero import Pot, Button, LED
import asyncio
from machine import Pin, I2S


class Buttons:
    def __init__(self, pins):
        self.buttons = [Button(pin) for pin in pins]
        self.buttonpins = pins

    def get_buttons(self):
        return self.buttons


class Led:
    def __init__(self, pins):
        self.buttons = [LED(pin) for pin in pins]

    def set_led_on(self, index):
        self.buttons[index].on()

    def set_led_off(self, index):
        self.buttons[index].off()

    def toggle_led(self, index):
        self.buttons[index].toggle()


class Potentiometers:
    def __init__(self, pins, maxV):
        self.pots = [Pot(pin) for pin in pins]
        self.maxV = maxV

    def get_state(self, index, steps):
        r = round(steps / self.maxV * self.pots[index].voltage)
        return r

    def get_V(self):
        v = []
        for pot in self.pots:
            v.append(pot.voltage)
        return v


class Speaker:
    def __init__(self, sample_rate=8000, bits=16, buffer_size=2000):
        bck_pin = Pin(16)
        lrc_pin = Pin(17)
        din_pin = Pin(18)

        self.audio = I2S(
            0,
            sck=bck_pin,
            ws=lrc_pin,
            sd=din_pin,
            mode=I2S.TX,
            bits=bits,
            format=I2S.MONO,
            rate=sample_rate,
            ibuf=buffer_size,
        )

    def write(self, buffer):
        self.audio.write(buffer)
