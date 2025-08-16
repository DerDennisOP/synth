from ST7735 import TFT
from machine import Pin, SPI
from sysfont import sysfont
import synth
import array
import random
import math


class Display(TFT):
    def __init__(self, sck=2, mosi=3, miso=0, cs=1, dc=4, rst=5):
        spi = SPI(
            0,
            baudrate=133000000,
            polarity=0,
            phase=0,
            sck=Pin(sck),
            mosi=Pin(mosi),
            miso=Pin(miso),
        )
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
            current_pixel = (int(x / buffer_len * 160), int((y + 256) / 512 * 128))
            if last_pixel is not None:
                self.line(last_pixel, current_pixel, TFT.GREEN)
            last_pixel = current_pixel
        self.line(last_pixel, current_pixel, TFT.GREEN)

    def draw_arrow(self, pos1, pos2, color):
        self.line(pos1, pos2, color)

        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]

        # Avoid division by zero for identical points
        length = math.sqrt(dx * dx + dy * dy)
        if length < 1e-6:
            return

        # Calculate rotation angle using atan2 for proper quadrant handling
        rot = math.atan2(dy, dx) + 3 * math.pi / 2

        width = 2
        height = 10

        position = pos2
        points = [
            (position[0], position[1]),
            (position[0] - width, position[1] - height),
            (position[0] + width, position[1] - height),
        ]

        rotated_points = []
        for point in points:
            x = point[0] - position[0]
            y = point[1] - position[1]
            rotated_x = x * math.cos(rot) - y * math.sin(rot) + position[0]
            rotated_y = x * math.sin(rot) + y * math.cos(rot) + position[1]
            rotated_points.append((int(rotated_x), int(rotated_y)))

        self.fillpoly(rotated_points, color)

    def fillpoly(self, positions, color):
        min_x = min(pos[0] for pos in positions)
        max_x = max(pos[0] for pos in positions)
        min_y = min(pos[1] for pos in positions)
        max_y = max(pos[1] for pos in positions)

        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                inside = False
                for i in range(len(positions)):
                    j = (i + 1) % len(positions)
                    xi, yi = positions[i]
                    xj, yj = positions[j]

                    if (yi > y) != (yj > y):
                        intersect_x = (xj - xi) * (y - yi) / (yj - yi + 1e-10) + xi
                        if x < intersect_x:
                            inside = not inside

                if inside:
                    self.pixel((x, y), color)


class Window:
    def __init__(self, synth_instance):
        self.tft = Display()
        self.buffer = array.array("h", [0] * 30)
        # Graph
        # Module_Menu
        # New_Module_Menu
        # Module_map
        # Module_settings
        self.display_state = "Graph"
        self.size = [160, 128]
        self.update_buffer = False
        self.synth = synth_instance
        self.selected_module = 0
        self.selected_module_id = ""
        self.init_menu = False
        self.steps = [0, 0, 0]
        self.encoder_position = 0
        self.encoder_pressed = False
        self.last_encoder_pressed = False
        self.button_states = [False, False, False]
        self.current_setting_index = 0
        self.current_setting_value = 0
        self.settings_module = None
        self.last_setting_index = -1
        self.last_encoder_position = -1
        self.last_encoder_pressed = False
        self.module_map_pos = {}
        self.module_map_grid = []
        self.all_modules = {
            "Input": synth.Input,
            "Noise": synth.Noise,
            "Sine": synth.Sine,
            "Square": synth.Square,
            "Triangle": synth.Triangle,
            "Sawtooth": synth.Sawtooth,
            "Mixer": synth.Mixer,
            "PitchShifter": synth.PitchShifter,
            "Envelope": synth.Envelope,
            "LowPassFilter": synth.LowPassFilter,
            "HighPassFilter": synth.HighPassFilter,
            "Reverb": synth.Reverb,
        }

        self.color_legend = {
            "Input": self.tft.GREEN,
            "Noise": self.tft.color(0, 50, 100),
            "Sine": self.tft.color(0, 204, 204),
            "Square": self.tft.color(0, 204, 204),
            "Triangle": self.tft.color(0, 204, 204),
            "Sawtooth": self.tft.color(0, 204, 204),
            "Mixer": self.tft.YELLOW,
            "PitchShifter": self.tft.color(255, 165, 0),
            "Envelope": self.tft.color(138, 43, 226),
            "LowPassFilter": self.tft.BLUE,
            "HighPassFilter": self.tft.color(0, 20, 255),
            "Output": self.tft.RED,
            "Reverb": self.tft.WHITE,
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
                    self.draw_str_list(self.all_modules.keys())
                    self.init_menu = True
                    self.steps[0] = len(self.all_modules)
                self.select_new_menu()
            elif self.display_state == "Module_map":
                if not self.init_menu and self.modules() != []:
                    self.draw_module_map()
                    self.init_menu = True
                self.select_module_in_map()
            elif self.display_state == "Module_settings":
                if not self.init_menu:
                    self.init_menu = True
                    self.draw_module_settings()
                    self.last_setting_index = self.current_setting_index
                    self.last_pot_states = self.pot_states[:]

                self.handle_module_settings_input()

                # Only redraw if something changed
                if (
                    self.current_setting_index != self.last_setting_index
                    or self.encoder_position != self.last_encoder_position
                    or self.encoder_pressed != self.last_encoder_pressed
                ):
                    self.draw_module_settings()
                    self.last_setting_index = self.current_setting_index
                    self.last_encoder_position = self.encoder_position
                    self.last_encoder_pressed = self.encoder_pressed

    def set_buffer(self, buffer):
        if not self.update_buffer:
            for i in range(len(self.buffer)):
                self.buffer[i] = buffer[i]
            self.update_buffer = True

    def switch(self, display_state):
        self.tft.clear()
        self.display_state = display_state

    def show_graph(self, module):
        pass

    def modules(self):
        return self.synth.modules

    def add_module(self):
        # Ensure selected_module is within valid range
        module_keys = list(self.all_modules.keys())
        if 0 <= self.selected_module < len(module_keys):
            module_class = self.all_modules[module_keys[self.selected_module]]
            new_module = self.synth.add_module(module_class)
            # Redraw module map to include new module
            self.draw_module_map()
            return new_module
        return None

    def delete_module(self, module):
        del self.synth.modules[module.id]

    def select_new_menu(self, pos=10, distance=10, margin=10, circle_size_prozent=0.25):
        # Use encoder position to select modules, with bounds checking
        max_modules = len(self.all_modules) - 1
        if max_modules >= 0:
            # Map encoder position to module selection (handle negative positions)
            bounded_selection = self.encoder_position % (max_modules + 1)
            if bounded_selection < 0:
                bounded_selection = max_modules + bounded_selection + 1

            if self.selected_module != bounded_selection:
                self.selected_module = bounded_selection
                f = self.selected_module + 1
                circle_pos = (
                    margin - distance * circle_size_prozent,
                    pos + distance * circle_size_prozent * 1 + distance * f,
                )

                self.tft.fillrect((0, 0), (margin, self.size[1]), TFT.BLACK)
                self.tft.fillcircle(circle_pos, distance * circle_size_prozent, TFT.WHITE)
        
        # Handle encoder button press to add module (detect rising edge)
        if self.encoder_pressed and not self.last_encoder_pressed:
            self.add_module()

    def get_encoder_state(self, position, is_pressed):
        self.last_encoder_pressed = self.encoder_pressed
        self.encoder_position = position
        self.encoder_pressed = is_pressed

    def draw_module_map(self, rad=4):
        sorted_modules = self.synth.sort_modules()

        # Calculate grid dimensions based on module dependencies
        layers = {}
        layer_counts = {}

        # Assign modules to layers based on their dependency depth
        for module in sorted_modules:
            max_input_layer = -1
            for input_module in module.get_inputs().values():
                if str(input_module.get_id()) in layers:
                    max_input_layer = max(
                        max_input_layer, layers[str(input_module.get_id())]
                    )

            current_layer = max_input_layer + 1
            layers[str(module.get_id())] = current_layer

            if current_layer not in layer_counts:
                layer_counts[current_layer] = 0
            layer_counts[current_layer] += 1

        # Calculate positions
        max_layer = max(layers.values()) if layers else 0
        max_modules_per_layer = max(layer_counts.values()) if layer_counts else 1

        layer_positions = {layer: 0 for layer in layer_counts.keys()}
        pos = {}

        for module in sorted_modules:
            module_id = str(module.get_id())
            layer = layers[module_id]
            position_in_layer = layer_positions[layer]

            # Calculate x position based on layer
            x = int((self.size[0] * 0.9) * (layer + 1) / (max_layer + 2)) + int(
                self.size[0] * 0.05
            )

            # Calculate y position based on position in layer
            if layer_counts[layer] > 1:
                y = int(
                    (self.size[1] * 0.8)
                    * (position_in_layer + 1)
                    / (layer_counts[layer] + 1)
                ) + int(self.size[1] * 0.1)
            else:
                y = int(self.size[1] / 2)

            pos[module_id] = (x, y)
            layer_positions[layer] += 1

        self.module_map_pos = pos

        for module in sorted_modules:
            for m in module.get_inputs().values():
                if str(m.get_id()) in pos:
                    self.tft.draw_arrow(
                        self.module_map_pos[str(m.get_id())],
                        self.module_map_pos[str(module.get_id())],
                        self.tft.WHITE,
                    )

        for module in sorted_modules:
            self.tft.fillcircle(
                self.module_map_pos[str(module.get_id())],
                rad,
                self.color_legend[type(module).__name__],
            )

        self.steps[0], self.steps[1] = self.create_position_grid()

    def select_module_in_map(self, rad=4):
        # Use encoder position to navigate module map
        if not self.module_map_grid:
            return
            
        # Get all non-empty module IDs from the grid
        module_ids = []
        for row in self.module_map_grid:
            for module_id in row:
                if module_id != "":
                    module_ids.append(module_id)
        
        if not module_ids:
            return
            
        # Map encoder position to module index (handle negative positions)
        module_index = self.encoder_position % len(module_ids)
        if module_index < 0:
            module_index = len(module_ids) + module_index
            
        m_id = module_ids[module_index]
        if self.selected_module_id != m_id:
            # Deselect previous module
            if (
                self.selected_module_id != ""
                and self.selected_module_id in self.module_map_pos
            ):
                # Get the module to restore its original color
                try:
                    module = self.synth.get_module(self.selected_module_id)
                    original_color = self.color_legend.get(
                        type(module).__name__, self.tft.WHITE
                    )
                    self.tft.fillcircle(
                        self.module_map_pos[self.selected_module_id],
                        rad,
                        original_color,
                    )
                except:
                    # If module not found, use default color
                    self.tft.fillcircle(
                        self.module_map_pos[self.selected_module_id],
                        rad,
                        self.tft.RED,
                    )

            # Select new module
            if m_id != "" and m_id in self.module_map_pos:
                self.tft.fillcircle(self.module_map_pos[m_id], rad, self.tft.WHITE)

            self.selected_module_id = m_id

        # Check if encoder switch is pressed to open module settings (detect rising edge)
        if self.encoder_pressed and not self.last_encoder_pressed and self.selected_module_id != "":
            self.open_module_settings(self.selected_module_id)

    def open_module_settings(self, module_id):
        """Open the module settings menu for the specified module"""
        try:
            module = self.synth.get_module(module_id)
            self.settings_module = module
            self.display_state = "Module_settings"
            self.current_setting_index = 0
            self.current_setting_value = 0
            options = module.get_options()
            self.steps[0] = len(options) - 1 if options else 0  # For option selection
            self.steps[1] = 100  # For value adjustment (will be adjusted per option)
            self.steps[2] = 0  # Reserved for future use
            return True
        except Exception as e:
            print(f"Error opening module settings: {e}")
            return False

    def draw_module_settings(self):
        """Draw the module settings interface"""
        if not self.settings_module:
            # Clear screen and show error
            self.tft.fillrect((0, 0), self.size, self.tft.BLACK)
            self.tft.text((10, 10), "No module selected", self.tft.WHITE, sysfont)
            return

        # Clear screen
        self.tft.fillrect((0, 0), self.size, self.tft.BLACK)

        # Module title
        module_name = type(self.settings_module).__name__
        self.tft.text((10, 10), f"Settings: {module_name}", self.tft.WHITE, sysfont)

        # Get module options
        options = self.settings_module.get_options()
        if not options:
            self.tft.text((10, 30), "No settings available", self.tft.YELLOW, sysfont)
            return

        # Display options with selection indicator
        y_pos = 30
        for i, option in enumerate(options):
            color = (
                self.tft.WHITE
                if i == self.current_setting_index
                else self.tft.color(100, 100, 100)
            )

            # Selection indicator
            if i == self.current_setting_index:
                self.tft.text((5, y_pos), ">", self.tft.YELLOW, sysfont)

            # Option name
            self.tft.text((15, y_pos), option, color, sysfont)

            # Try to get current value
            try:
                current_value = getattr(self.settings_module, option, "N/A")
                self.tft.text((80, y_pos), f": {current_value}", color, sysfont)
            except:
                pass

            y_pos += 12

        # Instructions
        self.tft.text(
            (10, self.size[1] - 18),
            "Encoder: Navigate/Adjust",
            self.tft.color(150, 150, 150),
            sysfont,
        )
        self.tft.text(
            (10, self.size[1] - 6), "Press: Back", self.tft.color(150, 150, 150), sysfont
        )

    def handle_module_settings_input(self):
        """Handle input for module settings menu"""
        if not self.settings_module:
            return

        options = self.settings_module.get_options()
        if not options:
            return

        # Update setting selection based on encoder position
        # Use modulo to cycle through options (handle negative positions)
        new_index = self.encoder_position % len(options)
        if new_index < 0:
            new_index = len(options) + new_index
        self.current_setting_index = new_index

        # Get current option
        current_option = options[self.current_setting_index]

        # For value adjustment, we could use a separate mode or different logic
        # For now, let's use a simple approach: encoder position maps to value
        if hasattr(self.settings_module, f"set_{current_option}"):
            # Map encoder position to a value range - use absolute value and scale
            # This gives us 0-100 range regardless of encoder direction
            adjustment_value = (abs(self.encoder_position) * 5) % 101  # 0-100, scaled by 5 for finer control
            
            # Determine value range based on the option type
            if current_option == "duty_cycle":
                # Duty cycle: 0.0 to 1.0
                new_value = adjustment_value / 100.0
            elif current_option in ["attack", "decay", "sustain", "release"]:
                # Envelope parameters: 0.0 to 2.0
                new_value = (adjustment_value / 100.0) * 2.0
            elif current_option in ["cutoff"]:
                # Filter cutoff: 20 to 4000 Hz
                new_value = 20 + (adjustment_value / 100.0) * 3980
            elif current_option in ["roomsize", "damp", "mix"]:
                # Reverb parameters: 0.0 to 1.0
                new_value = adjustment_value / 100.0
            elif current_option == "pitch":
                # Pitch shifter: 0.1 to 2.0
                new_value = 0.1 + (adjustment_value / 100.0) * 1.9
            elif current_option == "amplitude":
                # Amplitude: 0.0 to 2.0
                new_value = (adjustment_value / 100.0) * 2.0
            elif current_option == "type":
                # Noise type: select from available types
                noise_types = [
                    "white",
                    "pink",
                    "red",
                    "violet",
                    "blue",
                    "gray",
                    "black",
                ]
                type_index = max(0, min(adjustment_value % len(noise_types), len(noise_types) - 1))
                new_value = noise_types[type_index]
            elif current_option == "value":
                # Input value: -255 to 255
                new_value = int(-255 + (adjustment_value / 100.0) * 510)
            else:
                # Default: 0.0 to 1.0
                new_value = adjustment_value / 100.0

            # Apply the new value
            try:
                setter_method = getattr(self.settings_module, f"set_{current_option}")
                setter_method(new_value)
            except Exception as e:
                print(f"Error setting {current_option}: {e}")

        # Check if encoder switch is pressed to go back (detect rising edge)
        if self.encoder_pressed and not self.last_encoder_pressed:
            self.display_state = "Module_map"
            self.settings_module = None
            self.init_menu = False  # Reset init_menu for next time
            self.tft.clear()

    def draw_str_list(self, list, pos=10, distance=10, margin=10):
        for i, text in enumerate(list):
            f = (i + 1) * distance
            self.tft.text((margin, pos + 1 * f), str(text), TFT.WHITE, sysfont)

    def get_menu_state(self):
        return self.display_state

    def get_button_states(self):
        return self.button_states

    def set_button_states(self, states):
        self.button_states = states[-3:]

    def loop_menu(self):
        pass

    def create_position_grid(self):
        unique_x = set()
        unique_y = set()

        for pos in self.module_map_pos.values():
            unique_x.add(pos[0])
            unique_y.add(pos[1])

        max_x = len(unique_x)
        max_y = len(unique_y)

        grid = [["" for _ in range(max_y)] for _ in range(max_x)]

        sorted_x = sorted(unique_x)
        sorted_y = sorted(unique_y)

        x_index = {value: index for index, value in enumerate(sorted_x)}
        y_index = {value: index for index, value in enumerate(sorted_y)}

        for key, pos in self.module_map_pos.items():
            grid_x = x_index[pos[0]]
            grid_y = y_index[pos[1]]
            grid[grid_x][grid_y] = key

        self.module_map_grid = grid

        print(grid)

        return max_x - 1, max_y - 1
