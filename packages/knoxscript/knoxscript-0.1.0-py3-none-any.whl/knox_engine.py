import cv2
import numpy as np
import re
import os
import sys

class KnoxEngine:
    def __init__(self):
        self.buffers = {}   # Stores Images (@img)
        self.floats = {}    # Stores Numbers ($val)
        self.keyframes = {} # Stores Animations: {'$val': {0: 10, 60: 50}}
        self.frame_index = 0

    def _lerp(self, start_val, end_val, t):
        """Linear Interpolation formula"""
        return start_val + (end_val - start_val) * t

    def _update_variables(self):
        """Updates $vars based on current frame_index and keyframes"""
        for var, keys in self.keyframes.items():
            # Find the previous keyframe and next keyframe
            frames = sorted(keys.keys())
            
            # 1. Before first keyframe? Use first value.
            if self.frame_index <= frames[0]:
                self.floats[var] = keys[frames[0]]
                continue
            
            # 2. After last keyframe? Use last value.
            if self.frame_index >= frames[-1]:
                self.floats[var] = keys[frames[-1]]
                continue

            # 3. Interpolate between two keyframes
            for i in range(len(frames) - 1):
                f_start, f_end = frames[i], frames[i+1]
                if f_start <= self.frame_index <= f_end:
                    # Calculate percentage of completion (0.0 to 1.0)
                    t = (self.frame_index - f_start) / (f_end - f_start)
                    val_start = keys[f_start]
                    val_end = keys[f_end]
                    
                    # Calculate current value
                    self.floats[var] = int(self._lerp(val_start, val_end, t))
                    break

    def execute_line(self, line):
        line = line.strip()
        if not line or line.startswith("#"): return

        try:
            # --- 1. KEYFRAME DEFINITION (Run once per script load) ---
            # Syntax: Key : $fade [0:0, 60:100]
            if line.startswith("Key :"):
                # Only parse keys on frame 0 to setup
                if self.frame_index > 0: return 

                match = re.search(r"(\$\w+)\s*\[(.*?)\]", line)
                if match:
                    var, raw_keys = match.groups()
                    self.keyframes[var] = {}
                    # Parse "0:0, 60:100"
                    pairs = raw_keys.split(',')
                    for pair in pairs:
                        f, v = pair.split(':')
                        self.keyframes[var][int(f)] = int(v)
                    print(f"[Knox] Animation registered for {var}")

            # --- 2. MIX with Variable Opacity ---
            # Syntax: Mix : @A | @B ($opacity) > @C
            elif line.startswith("Mix :"):
                # Check for dynamic opacity variable ($var)
                match = re.search(r"(@\w+)\s*\|\s*(@\w+)\s*\((.*?)\)\s*>\s*(@\w+)", line)
                if match:
                    a, b, alpha_raw, target = match.groups()
                    
                    # Determine opacity (is it a static number 50 or a var $fade?)
                    if alpha_raw.startswith("$"):
                        alpha = self.floats.get(alpha_raw, 50) / 100.0 # Normalize 0-100 to 0.0-1.0
                    else:
                        alpha = int(alpha_raw) / 100.0

                    # Resize safety
                    if self.buffers[a].shape != self.buffers[b].shape:
                        self.buffers[b] = cv2.resize(self.buffers[b], (self.buffers[a].shape[1], self.buffers[a].shape[0]))
                    
                    self.buffers[target] = cv2.addWeighted(self.buffers[a], 1.0 - alpha, self.buffers[b], alpha, 0)

            # --- 3. DYNAMIC BLUR ---
            # Syntax: C : ~@img ($amount)
            elif "C : ~" in line:
                match = re.search(r"~(@\w+)\s*\((.*?)\)", line)
                if match:
                    var, radius_raw = match.groups()
                    
                    # Get radius from variable
                    if radius_raw.startswith("$"):
                        r = self.floats.get(radius_raw, 1)
                    else:
                        r = int(radius_raw)

                    # Blur radius must be odd
                    if r % 2 == 0: r += 1
                    if r < 1: r = 1
                    
                    self.buffers[var] = cv2.GaussianBlur(self.buffers[var], (r, r), 0)

            # --- Standard Load/View commands (omitted for brevity) ---
            elif line.startswith("Img :"):
                path, var = re.search(r"{(.*?)} > (@\w+)", line).groups()
                self.buffers[var] = cv2.imread(path)
            
            elif line.startswith("Save :"):
                 # Save frames as sequence: output_001.jpg
                var, base_name = re.search(r"(@\w+) > {(.*?)}", line).groups()
                filename = f"{base_name}_{self.frame_index:03d}.jpg"
                cv2.imwrite(filename, self.buffers[var])
                print(f"[Render] Frame {self.frame_index} saved.")

        except Exception as e:
            print(f"[Error Frame {self.frame_index}] {e}")

    def render(self, script, frames=60):
        """ The Main Loop """
        lines = script.split('\n')
        
        for f in range(frames):
            self.frame_index = f
            self._update_variables() # Calculate new values for $fade, $blur
            
            for line in lines:
                self.execute_line(line)

def main():
    if len(sys.argv) < 2:
        print("Usage: knox <script.knox>")
        sys.exit(1)
    
    script_path = sys.argv[1]
    
    if not os.path.exists(script_path):
        print(f"Error: File '{script_path}' not found.")
        sys.exit(1)

    with open(script_path, 'r') as f:
        script_content = f.read()

    print(f"--- KnoxScript Rendering: {script_path} ---")
    engine = KnoxEngine()
    engine.render(script_content, frames=60)
    print("--- Render Complete ---")

if __name__ == "__main__":
    main()
