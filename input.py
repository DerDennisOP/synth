from picozero import Pot, Button, LED
import asyncio
from machine import Pin, I2S


class Buttons():
    def __init__(self, pins):
        self.buttons = [Button(pin) for pin in pins]
        self.last_pressed = None  # Variable zum Speichern des zuletzt gedrückten Buttons
        for button in self.buttons:
            button.when_pressed = lambda b=button: self.on_button_pressed(b)
            button.when_released = lambda b=button: self.on_button_released(b)

    def on_button_pressed(self, button):
        self.last_pressed = button  # Speichere den gedrückten Button

    def on_button_released(self, button):
        if self.last_pressed == button:
            self.last_pressed = None  # Setze den zuletzt gedrückten Button zurück

class Led():
    def __init__(self,pins):
        self.buttons = [LED(pin) for pin in pins]
    
    def set_led_on(self,index):
        self.buttons[index].on()

    def set_led_off(self,index):
        self.buttons[index].off()
    
    def toggle_led(self,index):
        self.buttons[index].toggle()
        

class Potentiometers():
    def __init__(self,pins):
        self.pot = [Pot(pin) for pin in pins]
        self.state = [0,0,0]

    def update(self):
        for i in range(len(self.pot)):
            self.state[i] = self.pot[i].value

    def get_state(self,steps=[100,100,100]):
        n =[0,0,0]
        for i in range(len(self.pot)):
            n[i] = int(self.state[i] * steps[i])
        return n

class Speaker():
    def __init__(self,sample_rate=8000,bits=16,buffer_size=2000):
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
            ibuf=buffer_size
        )

    def write(self,buffer):
        self.audio.write(buffer)



