from picozero import Pot, Button, LED
from machine import Pin
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


class RotaryEncoder:
    def __init__(self, pin_a, pin_b, pin_switch):
        self.pin_a = Pin(pin_a, Pin.IN, Pin.PULL_UP)
        self.pin_b = Pin(pin_b, Pin.IN, Pin.PULL_UP)
        self.switch = Button(pin_switch)
        self.position = 0
        self.last_a = self.pin_a.value()
        self.last_b = self.pin_b.value()
        
        # Set up interrupts for rotation detection
        self.pin_a.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=lambda pin: self._rotation_handler())
        
    def _rotation_handler(self):
        a_state = self.pin_a.value()
        b_state = self.pin_b.value()
        
        if a_state != self.last_a:
            if a_state != b_state:
                self.position += 1
            else:
                self.position -= 1
                
        self.last_a = a_state
        self.last_b = b_state
    
    def get_position(self):
        return self.position
    
    def reset_position(self):
        self.position = 0
    
    def is_pressed(self):
        return self.switch.is_pressed


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
