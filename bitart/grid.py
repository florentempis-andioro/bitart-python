from collections import Counter

class Grid:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.points = [0] * (width * height)

    def __getitem__(self, xy):
        x, y = xy
        if not (0 <= x < self.width): raise IndexError(f"X out of bounds: {x}")
        if not (0 <= y < self.height): raise IndexError(f"Y out of bounds: {y}")
        return self.points[x + (self.width * y)]

    def __setitem__(self, xy, value):
        x, y = xy
        # Ruby version throws error, Python list throws IndexError usually, we can strict check if we want
        # but let's assume valid access or rely on list bounds check + index calc
        if not (0 <= x < self.width): raise IndexError(f"X out of bounds: {x}")
        if not (0 <= y < self.height): raise IndexError(f"Y out of bounds: {y}")
        self.points[x + (self.width * y)] = value

    def fill(self, value):
        self.points = [value] * (self.width * self.height)

    def map_inplace(self, func):
        """func takes (x, y, current_value) and returns new_value"""
        for y in range(self.height):
            for x in range(self.width):
                i = x + (self.width * y)
                self.points[i] = func(x, y, self.points[i])

    def each_pos(self):
        """Yields (x, y, value)"""
        for y in range(self.height):
            for x in range(self.width):
                val = self.points[x + (self.width * y)]
                yield x, y, val

    def histogram(self):
        return Counter(self.points)

    def analysis(self):
        hist = self.histogram()
        total_pixels = len(self.points)
        
        if not hist:
            return {
                'num_keys': 0, 'min_key': 0, 'max_key': 0,
                'most_common_key': 0, 'most_common_key_count': 0,
                'density': 0.0, 'dominance': 0.0
            }

        keys = list(hist.keys())
        min_key = min(keys)
        max_key = max(keys)
        num_keys = len(keys)
        
        # Most common
        most_common_key, most_common_key_count = hist.most_common(1)[0]
        
        # Density: num_keys / (range)
        key_range = (max_key - min_key + 1)
        density = num_keys / float(key_range) if key_range > 0 else 0.0
        
        # Dominance: fraction of pixels containing most common value
        dominance = most_common_key_count / float(total_pixels)
        
        return {
            'num_keys': num_keys,
            'min_key': min_key,
            'max_key': max_key,
            'most_common_key': most_common_key,
            'most_common_key_count': most_common_key_count,
            'density': density,
            'dominance': dominance
        }

    def repeated_pattern(self, index, vertical=True, maxlen=8):
        if vertical:
            stripe = [self[index, y] for y in range(self.height)]
        else:
            stripe = [self[x, index] for x in range(self.width)]
            
        return self._find_pattern_in(stripe, maxlen)

    def _find_pattern_in(self, stripe, max_pattern_length):
        if not stripe: return None
        pattern = [stripe[0]]
        
        while True:
            idx = self._repeats_to(stripe, pattern)
            # If the pattern repeats until the end of the stripe, we found it
            if idx + len(pattern) > len(stripe):
                return pattern
            
            # Extend pattern
            pattern = stripe[:idx+1] # Ruby: stripe[0..idx] is inclusive, python slice exclusive
            
            if len(pattern) > max_pattern_length:
                return None

    def _repeats_to(self, stripe, pattern):
        pat_len = len(pattern)
        for n in range(len(stripe)):
            if stripe[n] != pattern[n % pat_len]:
                return n
        return len(stripe)
