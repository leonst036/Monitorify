def render_braille(rx_data, tx_data, width_chars, height_chars):
    w = width_chars * 2
    h = height_chars * 4
    
    grid = [[False]*w for _ in range(h)]
    
    max_rx = max(rx_data) if rx_data else 1
    max_tx = max(tx_data) if tx_data else 1
    max_val = max(max_rx, max_tx)
    if max_val == 0:
        max_val = 1
        
    center_y = h // 2
    
    # Fill grid
    for x in range(w):
        idx = int((x / w) * len(rx_data))
        if idx < len(rx_data):
            rx = rx_data[idx]
            tx = tx_data[idx]
            
            rx_dots = int((rx / max_val) * (h / 2))
            tx_dots = int((tx / max_val) * (h / 2))
            
            # Download goes up (lower y)
            for y in range(center_y - rx_dots, center_y):
                if 0 <= y < h:
                    grid[y][x] = True
            
            # Upload goes down (higher y)
            for y in range(center_y, center_y + tx_dots):
                if 0 <= y < h:
                    grid[y][x] = True
                    
    # Convert grid to braille
    braille_map = [
        [0x01, 0x08],
        [0x02, 0x10],
        [0x04, 0x20],
        [0x40, 0x80]
    ]
    
    lines = []
    for cy in range(0, h, 4):
        line = ""
        for cx in range(0, w, 2):
            char_val = 0x2800
            for dy in range(4):
                for dx in range(2):
                    if grid[cy+dy][cx+dx]:
                        char_val += braille_map[dy][dx]
            line += chr(char_val)
        lines.append(line)
        
    return "\n".join(lines)

import random
rx = [random.randint(0, 100) for _ in range(100)]
tx = [random.randint(0, 100) for _ in range(100)]
print(render_braille(rx, tx, 50, 10))
