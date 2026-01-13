import random
from PIL import Image, ImageDraw
from .grid import Grid
from .generator import FunctionMaker

EXTENT = 512
MAX_ZOOM = 3

class ComputeContext:
    def __init__(self, depth, attempts=20, reject_bad=True, scale_power=0, color_override=None):
        self.depth = depth
        self.attempts = attempts
        self.reject_bad = reject_bad
        self.scale = 1 << scale_power
        self.extent = EXTENT // self.scale
        self.color_override = color_override
        
        if scale_power > MAX_ZOOM:
            raise ValueError(f"Scale too high! Max {MAX_ZOOM}")

    def compute_and_render(self):
        pixels = None
        stats = None
        fn = None
        modulo = None
        problem = None

        for attempt in range(1, self.attempts + 1):
            if random.random() < 0.1: # Small chance of no modulo
                 modulo = None
            else:
                 modulo = random.randint(2, 13)

            fn = FunctionMaker(depth=self.depth).make(modulo)
            
            # Compute grid
            pixels = self.compute(fn)
            stats = pixels.analysis()
            
            problem = self.review_image(pixels, stats)
            if not (self.reject_bad and problem):
                break
                
            # If we reached here and reject_bad is true, we loop again
            if attempt == self.attempts:
                # Unable to produce interesting pattern
                return None, None, None, None, None, "Failed to generate interesting pattern"

        color_fn_type = self.choose_color_function(stats, modulo)
        color_func = self.create_color_function(color_fn_type, stats)
        image = self.render(pixels, color_func)
        

        
        return image, fn, stats, color_fn_type, modulo, problem

    def render_custom(self, fn):
        # Render a specific function without the random loop
        pixels = self.compute(fn)
        stats = pixels.analysis()
        
        # We don't really have a modulo from generation, but we can try to guess it or just default
        # For coloring, we need to pick a strategy.
        # Let's say if stats keys are small (< 16), assume discrete/modulo-like -> onebit
        # else gradient
        
        modulo = None # We don't strictly know it, maybe parsing could extract it but partial AST match is hard
        # But for coloring decision:
        
        # If the function ends with % N, maybe we can infer?
        # But simpler: check stats.
        
        if self.color_override:
             color_fn_type = self.color_override
        elif stats['num_keys'] < 30: # arbitrary heuristic
             color_fn_type = 'onebit'
        else:
             color_fn_type = 'gradient'
             
        color_func = self.create_color_function(color_fn_type, stats)
        image = self.render(pixels, color_func)
        
        problem = self.review_image(pixels, stats)
        
        return image, fn, stats, color_fn_type, modulo, problem

    def compute(self, function):
        # function is a plotfn object, clear callable
        results = Grid(self.extent, self.extent)
        # We need to pass a context dict to function
        # optimization: use map_inplace
        def mapper(x, y, val):
            return function({'x': x, 'y': y})
        
        results.map_inplace(mapper)
        return results

    def render(self, pixels, color_func):
        # Create image
        image = Image.new("RGB", (self.extent * self.scale, self.extent * self.scale))
        draw = ImageDraw.Draw(image)
        
        for x, y, val in pixels.each_pos():
            color = color_func(val)
            # PIL rectangle is [x0, y0, x1, y1] inclusive or similar?
            # PIL rectangle: [x0, y0, x1, y1] where second point is just outside logic usually but 
            # documentation says: The second point is just outside the drawn rectangle.
            
            scale = self.scale
            x0 = x * scale
            y0 = y * scale
            x1 = (x + 1) * scale - 1 
            y1 = (y + 1) * scale - 1
            
            # Draw can take [x0, y0, x1, y1]
            draw.rectangle([x0, y0, x1, y1], fill=color, outline=None) # No outline to match solid blocks
            
        return image

    def stripes_count(self, pixels):
        max_pattern = 16
        fraction = 0.95
        
        hcount = 0
        vcount = 0
        
        # Check rows for horizontal stripes logic (this seems to be checking if whole ROW is a repeating pattern?)
        # Wait, repeated_pattern takes an index and vertical boolean.
        # If vertical=True, it takes column at `index`.
        
        for i in range(self.extent):
             if pixels.repeated_pattern(i, vertical=True, maxlen=max_pattern):
                 vcount += 1
             if pixels.repeated_pattern(i, vertical=False, maxlen=max_pattern):
                 hcount += 1
                 
        striped = (vcount / self.extent > fraction) or (hcount / self.extent > fraction)
        return striped, hcount, vcount

    def review_image(self, pixels, stats):
        if stats['num_keys'] <= 1:
            return "Solid colour"
        if stats['dominance'] > 0.98:
            return f"Dominance too high: {stats['dominance']}"
            
        striped, hcount, vcount = self.stripes_count(pixels)
        if striped:
            return f"Image is mostly stripes ({hcount}, {vcount})"
            
        return None

    def choose_color_function(self, stats, modulo):
        if self.color_override:
            return self.color_override
        if modulo:
            return "onebit"
        return "gradient"

    def create_color_function(self, mode, stats):
        bw_palette = [(0, 0, 0), (255, 255, 255)] # RGB tuples
        
        min_key = stats['min_key']
        max_key = stats['max_key']
        most_common = stats['most_common_key']
        
        if mode == 'onebit':
            def onebit(n):
                return bw_palette[0] if n == most_common else bw_palette[1]
            return onebit
            
        if mode == 'gradient':
            denom = float(max_key - min_key)
            if denom == 0: denom = 1.0
            
            def gradient(n):
                mag = (n - min_key) / denom
                # Clamp or handle weirdness
                mag = max(0.0, min(1.0, mag))
                val = int(mag * 255)
                return (val, val, val)
            return gradient
            
        if mode == 'rgb':
            denom = float(max_key - min_key)
            if denom == 0: denom = 1.0
            
            # Simple heatmap-like RGB: Blue -> Cyan -> Green -> Yellow -> Red
            # Or just nice trig functions
            import math
            def rgb(n):
                t = (n - min_key) / denom
                t = max(0.0, min(1.0, t))
                
                # Simple spectral approximation
                # R: peak at 1.0
                # G: peak at 0.5
                # B: peak at 0.0
                
                # B = max(0, 1 - 2*t)
                # G = max(0, 1 - 2*abs(t - 0.5))
                # R = max(0, 2*t - 1) 
                # This is a bit dark in middles. 
                
                # Let's use a Sine-based palette (Cosine actually for 0..1)
                # r = 0.5 + 0.5*cos(2*pi* (t + 0.0))
                # g = 0.5 + 0.5*cos(2*pi* (t + 0.33))
                # b = 0.5 + 0.5*cos(2*pi* (t + 0.67))
                
                # Actually, standard "Turbo" or "Jet" like look is popular.
                # Let's stick to a procedural sine palette which often looks nice and artistic
                # R: t
                # G: sin(pi * t)
                # B: cos(0.5 * pi * t)
                
                r = int(255 * t)
                g = int(255 * math.sin(math.pi * t))
                b = int(255 * math.cos(0.5 * math.pi * t))
                
                return (r, g, b)
                return (r, g, b)
            return rgb

        # Single color gradients
        # Use a map of name -> (r_scale, g_scale, b_scale)
        single_colors = {
            'red': (1.0, 0.0, 0.0),
            'green': (0.0, 1.0, 0.0),
            'blue': (0.0, 0.0, 1.0),
            'cyan': (0.0, 1.0, 1.0),
            'magenta': (1.0, 0.0, 1.0),
            'yellow': (1.0, 1.0, 0.0),
            'orange': (1.0, 0.647, 0.0), # Approximately 255, 165, 0
            'grey': (1.0, 1.0, 1.0),     # Same as gradient
            'gray': (1.0, 1.0, 1.0)
        }

        if mode in single_colors:
            denom = float(max_key - min_key)
            if denom == 0: denom = 1.0
            r_s, g_s, b_s = single_colors[mode]
            
            def single_gradient(n):
                mag = (n - min_key) / denom
                mag = max(0.0, min(1.0, mag))
                return (int(mag * 255 * r_s), int(mag * 255 * g_s), int(mag * 255 * b_s))
            return single_gradient

        return lambda n: (128, 128, 128) # fallback

        return lambda n: (128, 128, 128) # fallback
