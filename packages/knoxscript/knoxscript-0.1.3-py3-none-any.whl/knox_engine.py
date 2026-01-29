import cv2
import numpy as np
import re
import os
import sys

class KnoxEngine:
    def __init__(self):
        self.buffers = {}
        self.floats = {}
        self.keyframes = {}
        self.frame_index = 0
        self.last_buffer_name = None

    def _lerp(self, start_val, end_val, t):
        return start_val + (end_val - start_val) * t

    def _update_variables(self):
        for var, keys in self.keyframes.items():
            frames = sorted(keys.keys())
            
            if self.frame_index <= frames[0]:
                self.floats[var] = keys[frames[0]]
                continue
            
            if self.frame_index >= frames[-1]:
                self.floats[var] = keys[frames[-1]]
                continue

            for i in range(len(frames) - 1):
                f_start, f_end = frames[i], frames[i+1]
                if f_start <= self.frame_index <= f_end:
                    t = (self.frame_index - f_start) / (f_end - f_start)
                    self.floats[var] = int(self._lerp(keys[f_start], keys[f_end], t))
                    break

    def execute_line(self, line):
        line = line.strip()
        if not line or line.startswith("#"): return

        try:
            # --- 1. KEYFRAMES ---
            if line.startswith("Key :"):
                if self.frame_index > 0: return 
                match = re.search(r"(\$\w+)\s*\[(.*?)\]", line)
                if match:
                    var, raw_keys = match.groups()
                    self.keyframes[var] = {}
                    pairs = raw_keys.split(',')
                    for pair in pairs:
                        if ':' in pair:
                            f, v = pair.split(':')
                            self.keyframes[var][int(f)] = int(v)

            # --- 2. COLOR GENERATION ---
            elif "C : !" in line:
                match = re.search(r"!(@\w+)\s*{(.*?)}", line)
                if match:
                    target, color_raw = match.groups()
                    b, g, r = map(int, color_raw.split(','))
                    self.buffers[target] = np.full((1080, 1920, 3), (b, g, r), dtype=np.uint8)
                    self.last_buffer_name = target

            # --- 3. ROBUST MIX COMMAND (Replaces Regex) ---
            elif "Mix" in line and ">" in line:
                try:
                    clean = line.split(":", 1)[1].strip() 
                    left_side, target = clean.split(">")
                    target = target.strip()
                    
                    part_a, part_b = left_side.split("|")
                    a = part_a.strip()
                    
                    if "(" in part_b:
                        b = part_b.split("(")[0].strip()
                        alpha_raw = part_b.split("(")[1].replace(")", "").strip()
                    else:
                        b = part_b.strip()
                        alpha_raw = "50"

                    if alpha_raw.startswith("$"):
                        alpha = self.floats.get(alpha_raw, 50) / 100.0
                    else:
                        alpha = int(alpha_raw) / 100.0

                    if a not in self.buffers: self.buffers[a] = np.zeros((1080, 1920, 3), np.uint8)
                    if b not in self.buffers: self.buffers[b] = np.zeros((1080, 1920, 3), np.uint8)

                    if self.buffers[a].shape != self.buffers[b].shape:
                         self.buffers[b] = cv2.resize(self.buffers[b], (self.buffers[a].shape[1], self.buffers[a].shape[0]))

                    # Perform Mix
                    self.buffers[target] = cv2.addWeighted(self.buffers[a], 1.0 - alpha, self.buffers[b], alpha, 0)
                    self.last_buffer_name = target
                    # print(f"[DEBUG] Mixed {a} with {b} -> {target}") # Uncomment for debugging

                except Exception as e:
                    print(f"[Mix Error] Line '{line}' failed: {e}")

            # --- 4. BLUR ---
            elif "C : ~" in line:
                match = re.search(r"~(@\w+)\s*\((.*?)\)", line)
                if match:
                    var, radius_raw = match.groups()
                    
                    if radius_raw.startswith("$"):
                        r = self.floats.get(radius_raw, 1)
                    else:
                        r = int(radius_raw)

                    if r % 2 == 0: r += 1
                    if r < 1: r = 1
                    
                    if var in self.buffers:
                        self.buffers[var] = cv2.GaussianBlur(self.buffers[var], (r, r), 0)
                        self.last_buffer_name = var

            # --- 5. IMAGE LOAD ---
            elif line.startswith("Img :"):
                match = re.search(r"{(.*?)} > (@\w+)", line)
                if match:
                    path_raw, var = match.groups()
                    path = os.path.expanduser(path_raw)
                    if os.path.exists(path):
                        self.buffers[var] = cv2.imread(path)
                        self.last_buffer_name = var
                    else:
                        print(f"[Error] Image not found: {path}")

            # --- 6. SAVE (Auto-Create Folders) ---
            elif line.startswith("Save :"):
                match = re.search(r"(@\w+) > {(.*?)}", line)
                if match:
                    var, path_raw = match.groups()
                    full_path_base = os.path.expanduser(path_raw)
                    
                    folder = os.path.dirname(full_path_base)
                    if folder and not os.path.exists(folder):
                        try:
                            os.makedirs(folder, exist_ok=True)
                        except OSError as e:
                            print(f"[Error] Could not create folder {folder}: {e}")

                    filename = f"{full_path_base}_{self.frame_index:03d}.jpg"
                    if var in self.buffers:
                        cv2.imwrite(filename, self.buffers[var])
                        print(f"[Save] {filename}")

        except Exception as e:
            print(f"[Error Frame {self.frame_index}] Line: {line} -> {e}")

    def render(self, script, frames=60, output_mp4=None):
        lines = script.split('\n')
        
        video_writer = None
        if output_mp4:
            output_mp4 = os.path.expanduser(output_mp4)
            # Remove existing file if it exists so we don't get write errors
            if os.path.exists(output_mp4):
                try:
                    os.remove(output_mp4)
                except:
                    pass
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(output_mp4, fourcc, 30.0, (1920, 1080))
            print(f"--- Recording Video to: {output_mp4} ---")

        for f in range(frames):
            self.frame_index = f
            self._update_variables() 
            
            for line in lines:
                self.execute_line(line)
            
            # Write the last active buffer to the video
            if video_writer and self.last_buffer_name and self.last_buffer_name in self.buffers:
                frame_data = self.buffers[self.last_buffer_name]
                if frame_data.shape[:2] != (1080, 1920):
                    frame_data = cv2.resize(frame_data, (1920, 1080))
                video_writer.write(frame_data)
            
            if f % 10 == 0:
                print(f"[Render] Processing Frame {f}/{frames}...")

        if video_writer:
            video_writer.release()
            print(f"--- Render Complete: {output_mp4} ---")
            if sys.platform == "darwin":
                os.system(f"open '{output_mp4}'")

def main():
    if len(sys.argv) < 2:
        print("Usage: knox <script.knox> [frames=60]")
        sys.exit(1)
    
    script_path = sys.argv[1]
    
    frames = 60
    if len(sys.argv) > 2:
        try:
            frames = int(sys.argv[2])
        except ValueError:
            frames = 60

    if not os.path.exists(script_path):
        print(f"Error: File '{script_path}' not found.")
        sys.exit(1)

    with open(script_path, 'r') as f:
        script_content = f.read()

    desktop_video = os.path.expanduser("~/Desktop/knox_render.mp4")

    engine = KnoxEngine()
    engine.render(script_content, frames=frames, output_mp4=desktop_video)

if __name__ == "__main__":
    main()
