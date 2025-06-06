from ST7735 import TFT
from machine import Pin, SPI
from sysfont import sysfont
import synth
import array

class Display(TFT):
    def __init__(self, sck=2, mosi=3, miso=0, cs=1, dc=4, rst=5):
        spi = SPI(0, baudrate=133000000, polarity=0, phase=0, sck=Pin(sck), mosi=Pin(mosi), miso=Pin(miso))
        super().__init__(spi, dc, rst, cs)
        self.initb2()
        self.rotation(3)
        self.rgb(True)
        self.clear()
        
    def clear(self):
        self.fill(TFT.BLACK)

    def draw_buffer(self, buffer):
        self.clear()
        buffer_len = len(buffer)
        last_pixel = None
        for x, y in enumerate(buffer):
            current_pixel = (int(x/buffer_len*160), int((y+256)/512*128))
            if last_pixel is not None:
                self.line(last_pixel, current_pixel, TFT.GREEN)           
            last_pixel = current_pixel
        self.line(last_pixel, current_pixel, TFT.GREEN)
    
                   

class Window():
    def __init__(self, synth_instance):
        self.tft = Display()
        self.buffer = array.array("h", [0] * 30)
        #Graph
        #Module_Menu
        #New_Module_Menu
        #Module_map
        self.display_state = "Graph"
        self.size = [160, 128]
        self.update_buffer = False
        self.aim_cross = [0, 0]
        self.synth = synth_instance
        self.selected_module = 0
        self.change_module = True
        self.init_menu = False
        self.modulelist = []
        self.all_modules = {
            "Input": synth.Input,
            "Sine": synth.Sine,
            "Square": synth.Square,
            "Triangle": synth.Triangle,
            "Sawtooth": synth.Sawtooth,
            "Mixer": synth.Mixer,
            "Envelope": synth.Envelope,
            "LowPassFilter": synth.LowPassFilter,
        }
        

    def display(self):
        while True:
            if self.display_state == "Graph":
                if self.update_buffer:
                    self.tft.draw_buffer(self.buffer)
                    self.update_buffer = False
            elif self.display_state == "Module_Menu":
                self.modules_menu()
            elif self.display_state == "New_Module_Menu":
                if not self.init_menu:
                    self.new_module_menu()
                    self.init_menu = True
                self.select_new_menu()
            elif self.display_state == "Module_map":
                if not self.init_menu and self.modulelist != []:
                    self.draw_module_map()
                    self.init_menu = True


    def set_buffer(self, buffer):
        if not self.update_buffer:
            for i in range(len(self.buffer)):
                self.buffer[i] = buffer[i]
            self.update_buffer = True

    def switch(self, display_state):
        self.display_state = display_state

    def show_graph(self, module):
        pass
    
    def add_module(self):
        #synth.add_module(self.all_modules[list(self.all_modules.keys())[self.selected_module]])
        pass

    def new_module_menu(self, pos = 10, distance = 10, margin = 10):
        for i, all_modules in enumerate(self.all_modules.keys()):
            f = (i + 1) * distance
            self.tft.text((margin, pos + 1 * f),
                          all_modules,
                          TFT.WHITE,
                          sysfont)
    
    def select_new_menu(self, pos = 10, distance = 10, margin = 10, circle_size_prozent = 0.25):
        f = self.selected_module + 1
        circle_pos = (margin - distance * circle_size_prozent,
               pos + distance * circle_size_prozent * 1 + distance * f)
        if self.change_module == True:
            self.tft.fillrect((0,0),(margin,self.size[1]),TFT.BLACK)
            self.tft.fillcircle(circle_pos, distance * circle_size_prozent, TFT.WHITE)
            self.change_module = False

    def set_selected_module(self, selected_module):
        if selected_module != self.selected_module:
            self.change_module = True
            self.selected_module = selected_module
        
    def delete_module(self, module):
        del self.modules[module.id]
        
    def set_aimcross(self, x_potstate, y_potsate):
        self.aim_cross = [x_potstate, y_potsate]
    
    def modules_menu(self):
        self.tft.clear()
        print(self.aim_cross)
        self.tft.line([self.aim_cross[0], 0], [self.aim_cross[0], self.size[1]], TFT.RED)
        self.tft.line([0,self.aim_cross[1]], [self.size[0], self.aim_cross[1]], TFT.RED)
        self.tft.circle([self.aim_cross[0], self.aim_cross[1]], 10, TFT.RED)
        
    def draw_module_map(self):
        self.tft.fillcircle((self.size[0], self.size[1]/2), 10,TFT.RED)
        print(self.modulelist)
        # for module in self.modulelist:
        #     print(self.modulelist.get_inputs())
        #     if self.modulelist.get_inputs() == {}:
        #         print("linkerrand")
        
    def get_menu_state(self):
        return self.display_state
    
    def loop_menu(self):
        pass
    
    def get_modulelist(self,modulist):
        self.modulelist = modulist