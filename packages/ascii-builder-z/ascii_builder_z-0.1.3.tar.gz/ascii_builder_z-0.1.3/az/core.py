import builtins
from az.ascii_map import ASCII_MAP

class ColorSettings:
    def __init__(self, settings):
        self._settings = settings
        self.red = "red"
        self.green = "green"
        self.blue = "blue"
        self.yellow = "yellow"

    def __setattr__(self, name, value):
        if name == "_settings":
            super().__setattr__(name, value)
        else:
            super().__setattr__(name, value)
            if hasattr(self, "_settings"):
                self._settings._color = value

class Settings:
    def __init__(self):
        self.name = {}
        self.space = 1
        self._color = None
        self.element_colors = {}
        self.gradient = None
        self.color = ColorSettings(self)

az_set = Settings()

def az_print(*args, **kwargs):
    if not args:
        builtins.print()
        return

    if len(args) == 1 and isinstance(args[0], str):
        text_to_check = args[0].upper()
        mapped_text = None
        for key, value in az_set.name.items():
            if text_to_check == str(value).upper():
                mapped_text = str(key).upper()
                break
        
        is_mapped = mapped_text is not None
        if is_mapped or all(c.upper() in ASCII_MAP for c in args[0]):
            text = mapped_text if is_mapped else text_to_check
        
            colors = {
                "red": "\033[91m",
                "green": "\033[92m",
                "blue": "\033[94m",
                "yellow": "\033[93m",
            }
            reset = "\033[0m"
            
            def get_color_code(color_val, default=""):
                if not color_val:
                    return default
                if color_val in colors:
                    return colors[color_val]
                if isinstance(color_val, (list, tuple)) and len(color_val) == 3:
                    r, g, b = color_val
                    return f"\033[38;2;{r};{g};{b}m"
                if isinstance(color_val, str) and "," in color_val:
                    try:
                        r, g, b = [int(c.strip()) for c in color_val.split(",")]
                        return f"\033[38;2;{r};{g};{b}m"
                    except:
                        pass
                if "\033[" in color_val:
                    return color_val
                if str(color_val).isdigit():
                    return f"\033[{color_val}m"
                return color_val

            def parse_rgb(val):
                if isinstance(val, (list, tuple)) and len(val) == 3:
                    return val
                if isinstance(val, str) and "," in val:
                    try:
                        return [int(c.strip()) for c in val.split(",")]
                    except:
                        return None
                return None

            global_color_code = get_color_code(az_set._color)
            output = ["", "", "", "", ""]
            spacing = " " * az_set.space
            
            grad_start = parse_rgb(az_set.gradient[0]) if az_set.gradient and len(az_set.gradient) > 0 else None
            grad_end = parse_rgb(az_set.gradient[1]) if az_set.gradient and len(az_set.gradient) > 1 else None
            total_chars = len(text)
            
            for idx, char in enumerate(text):
                char_upper = char.upper()
                char_color_code = global_color_code
                
                if grad_start and grad_end:
                    ratio = idx / (total_chars - 1) if total_chars > 1 else 0
                    r = int(grad_start[0] + (grad_end[0] - grad_start[0]) * ratio)
                    g = int(grad_start[1] + (grad_end[1] - grad_start[1]) * ratio)
                    b = int(grad_start[2] + (grad_end[2] - grad_start[2]) * ratio)
                    char_color_code = f"\033[38;2;{r};{g};{b}m"
                
                char_color = az_set.element_colors.get(char_upper)
                if char_color:
                    char_color_code = get_color_code(char_color, char_color_code)
                
                if char_upper in ASCII_MAP:
                    char_lines = ASCII_MAP[char_upper]
                    for i in range(5):
                        line = char_lines[i]
                        if char_color_code:
                            output[i] += f"{char_color_code}{line}{reset}" + spacing
                        else:
                            output[i] += line + spacing
                else:
                    for i in range(5):
                        output[i] += "?" + spacing
            
            for line in output:
                builtins.print(line)
            return

    builtins.print(*args, **kwargs)
