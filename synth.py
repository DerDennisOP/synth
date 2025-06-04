from micropython import const
import random
import math
import array
from uctypes import addressof


class Uuid():
    def __init__(self, uuid=None):
        if isinstance(uuid, type(None)):
            self.uuid = ''.join([random.choice(list('0123456789abcdef')) for _ in range(32)])
        else:
            val = str(uuid)
            if len(val) == 32 and all(c in '0123456789abcdef' for c in val):
                self.uuid = val
            else:
                raise ValueError(f"Invalid UUID: {val}. Must be a 32-character hexadecimal string.")
    
    def __str__(self):
        return self.uuid
    
    def __eq__(self, other):
        if isinstance(other, Uuid):
            return self.uuid == other.uuid
        elif isinstance(other, str):
            return self.uuid == other
        return False
    
    @staticmethod
    def find(objects, uuid, identifier='id'):
        for obj in objects:
            if isinstance(identifier, type(None)):
                if isinstance(obj, Uuid) and str(obj) == uuid:
                    return obj
            elif hasattr(obj, identifier):
                if str(getattr(obj, identifier)) == uuid:
                    return obj
            else:
                raise ValueError(f"Object {obj} does not have identifier {identifier}")
        return None


class Config():
    def __init__(self):
        self.sample_rate = 8000
        self.buffer_size = 200
        self.max = 255


class Synth():
    def __init__(self, base):
        self.base = base
        self.modules = []
        self.output = self.add_module(Output)

    def add_module(self, module):
        if isinstance(module, type(SynthModule)):
            new_module = module(self.base)
            self.modules.append(new_module)
        else:
            raise TypeError("Module must be an instance of SynthModule")
        
        return new_module
        
    def get_module(self, uuid):
        if isinstance(uuid, Uuid):
            uuid = str(uuid)
        elif not isinstance(uuid, str):
            raise TypeError("UUID must be a string or an instance of Uuid")
        
        module = Uuid.find(self.modules, uuid)
        if module is None:
            raise ValueError(f"Module with UUID {uuid} not found")
        
        return module

    def get_buffer(self):
        output = self.modules[0].read()
        self.modules[0].reset()
        return output


class SynthModule():
    def __init__(self, base):
        self.base = base
        self.id = Uuid()
        self.inputs = {}
        self.buffer = array.array('h', [0] * self.base.buffer_size)
        self.is_updated = False

    def read(self):
        if not self.is_updated:
            self.update()
            self.is_updated = True
        
        return self.buffer
    
    def reset(self):
        if self.is_updated:
            self.is_updated = False
            for module in self.inputs.values():
                module.reset()

    def set(self, name, module):
        if not isinstance(module, SynthModule):
            raise TypeError("Input must be an instance of SynthModule")
        self.inputs[name] = module
        
    def remove(self, name):
        self.inputs.pop(name, None)
    
    def update(self):
        raise NotImplementedError("Subclasses should implement this method")


class Input(SynthModule):
    def __init__(self, base):
        super().__init__(base)

    def set_value(self, value):
        if not isinstance(value, int):
            raise TypeError("Value must be an integer")

        for i in range(self.base.buffer_size):
            self.buffer[i] = value

    def read(self):
        return self.buffer


class Oscillator(SynthModule):
    def __init__(self, base):
        super().__init__(base)
        self.index = 0
        self.lut_amount = const(1024)
        self.lut = array.array("h", [0] * self.lut_amount)
        self._generate_lut()

    def _generate_lut(self):
        raise NotImplementedError("Subclasses should implement this method")
    
    @micropython.viper
    def update(self):
        idx = uint(self.index)
        frequency = ptr16(self.inputs["frequency"].read())
        buffer_size = uint(self.base.buffer_size)
        buffer = ptr16(self.buffer)
        increment = uint((int(self.lut_amount)<<16) // int(self.base.sample_rate))
        lut = ptr16(self.lut)
        mod = uint(self.lut_amount) - 1
        i = uint(0)
        while i < buffer_size:
            buffer[i] = lut[(idx>>16) & mod]
            idx += increment * frequency[i]
            i += 1

        self.index = idx


class Sine(Oscillator):
    def __init__(self, base):
        super().__init__(base)

    def _generate_lut(self):
        for i in range(self.lut_amount):
            self.lut[i] = int(self.base.max * math.sin(2 * math.pi * i / self.lut_amount))


class Square(Oscillator):
    def __init__(self, base):
        self.duty_cycle = 0.5
        super().__init__(base)

    def _generate_lut(self):
        for i in range(self.lut_amount):
            if i < self.lut_amount * self.duty_cycle:
                self.lut[i] = int(self.base.max)
            else:
                self.lut[i] = -int(self.base.max)

    def set_duty_cycle(self, duty_cycle):
        if not (0 <= duty_cycle <= 1):
            raise ValueError("Duty cycle must be between 0 and 1")
        self.duty_cycle = duty_cycle
        self._generate_lut()


class Triangle(Oscillator):
    def __init__(self, base):
        super().__init__(base)

    def _generate_lut(self):
        for i in range(self.lut_amount):
            if i < self.lut_amount // 2:
                self.lut[i] = int(self.base.max * (2 * i / self.lut_amount - 1))
            else:
                self.lut[i] = int(self.base.max * (1 - 2 * (i / self.lut_amount)))


class Sawtooth(Oscillator):
    def __init__(self, base):
        super().__init__(base)
    
    def _generate_lut(self):
        for i in range(self.lut_amount):
            self.lut[i] = int(self.base.max * (2 * i / self.lut_amount - 1))
            if i >= self.lut_amount // 2:
                self.lut[i] = -self.lut[i]


class Mixer(SynthModule):
    def __init__(self, base):
        super().__init__(base)

    def update(self):
        for i in range(self.base.buffer_size):
            self.buffer[i] = 0

        for (name, module) in self.inputs.items():
            if name.endswith("_volume"):
                continue 
            module_buffer = module.read()
            module_volume = self.inputs.get(name + "_volume", None)
            if module_volume is not None:
                module_volume = module_volume.read()
            for i in range(self.base.buffer_size):
                if module_volume is not None:
                    self.buffer[i] += int(module_buffer[i] * module_volume[i] / self.base.max)
                else:
                    self.buffer[i] += module_buffer[i]


class Output(SynthModule):
    def __init__(self, base):
        super().__init__(base)
        self.amplitude = 1
    
    def set_amplitude(self, amplitude):
        self.amplitude = amplitude
    
    def update(self):
        input_buffer = self.inputs["input"].read()
        for i in range(self.base.buffer_size):
            self.buffer[i] = input_buffer[i] * self.amplitude


class Envelope(SynthModule):
    def __init__(self, base, attack=0.1, decay=0.1, sustain=0.5, release=0.1):
        super().__init__(base)
        self.attack = attack
        self.decay = decay
        self.sustain = sustain
        self.release = release
        self.state = 'idle'
        self.value = 0.0
    
    def trigger_attack(self):
        if self.state != 'attack':
            self.state = 'attack'
    
    def trigger_release(self):
        if self.state != 'idle':
            self.state = 'release'

    def is_active(self):
        return self.state != 'idle'
    
    def is_sustaining(self):
        return self.state == 'sustain'

    def update(self):
        buffer = self.inputs["input"].read()
        for i in range(self.base.buffer_size):
            if self.state == 'attack':
                self.value += 1.0 / (self.attack * self.base.sample_rate)
                if self.value >= 1.0:
                    self.value = 1.0
                    self.state = 'decay'
            elif self.state == 'decay':
                self.value -= (1.0 - self.sustain) / (self.decay * self.base.sample_rate)
                if self.value <= self.sustain:
                    self.value = self.sustain
                    self.state = 'sustain'
            elif self.state == 'sustain':
                pass
            elif self.state == 'release':
                self.value -= self.sustain / (self.release * self.base.sample_rate)
                if self.value <= 0.0:
                    self.value = 0.0
                    self.state = 'idle'
            self.buffer[i] = int(buffer[i] * self.value)


class LowPassFilter(SynthModule):
    def __init__(self, base, cutoff=1000.0, resonance=0.5):
        super().__init__(base)
        self.cutoff = cutoff
        self.resonance = resonance
        self.prev_input = 0.0
        self.prev_output = 0.0
    
    def update(self):
        buffer = self.inputs["input"].read()
        output = []
        rc = 1.0 / (2 * math.pi * self.cutoff)
        alpha = rc / (rc + (1.0 / self.base.sample_rate))

        for i in range(self.base.buffer_size):
            output_sample = alpha * (self.prev_output + buffer[i] - self.prev_input)
            self.prev_input = buffer[i]
            self.prev_output = output_sample
            self.buffer[i] = int(output_sample)