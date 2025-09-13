#!/usr/bin/env python3
import curses
import math
import time
import json
import os
import random
from collections import defaultdict, deque
W, H = 80, 24  
DEBUG = os.environ.get('WHITEBOARD_DEBUG', 'false').lower() == 'true'
TOOLS = ["pen", "ers", "line", "box", "circ", "fill", "spray", "text", "sel", "move", "copy", "pat", "arrow", "star", "tri", "hex"]
def toggle_debug():
    global DEBUG
    DEBUG = not DEBUG
class Pt:
    def __init__(self, x, y):
        self.x = x
        self.y = y
class Lyr:
    def __init__(self, w, h, nm="layer"):
        self.w = w
        self.h = h
        self.nm = nm
        self.d = [[' ' for _ in range(w)] for _ in range(h)]
        self.cols = [[0 for _ in range(w)] for _ in range(h)]  
        self.bg_cols = [[0 for _ in range(w)] for _ in range(h)]  
        self.vis = True
        self.lock = False
        self.alpha = 1.0  
    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.d[y][x]
        return ' '
    def get_col(self, x, y):
        if x >= 0 and x < self.w and y >= 0 and y < self.h:
            return self.cols[y][x]
        else:
            return 0
    def get_bg(self, x, y):
        if x >= 0 and x < self.w:
            if y >= 0 and y < self.h:
                return self.bg_cols[y][x] 
        return 0
    def set(self, x, y, c, col=None, bg=None):
        if x < 0 or x >= self.w or y < 0 or y >= self.h:
            return
        if self.lock:
            return  
        self.d[y][x] = c
        if col is not None:
            self.cols[y][x] = col
        if bg is not None:
            self.bg_cols[y][x] = bg
    def clr(self):
        for y in range(self.h):
            for x in range(self.w):
                self.d[y][x] = ' '
                self.cols[y][x] = 0
                self.bg_cols[y][x] = 0
class Brush:
    def __init__(self, sz=1, c='*', fg=7, bg=0, nm="brush"):
        self.sz = sz    
        self.c = c      
        self.fg = fg    
        self.bg = bg    
        self.nm = nm    
        self.mode = 'normal'  
    def get_pts(self, cx, cy):
        pts = []
        if self.sz == 1:
            pts.append((cx, cy))
        else:
            r = self.sz // 2
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if dx*dx + dy*dy <= r*r:
                        pts.append((cx + dx, cy + dy))
        return pts
    def draw(self, lyr, x, y, c=None, col=None, bg=None):
        if c is None:
            c = self.c
        if col is None:
            col = self.fg
        if bg is None:
            bg = self.bg
        pts = self.get_pts(x, y)
        for px, py in pts:
            lyr.set(px, py, c, col, bg)
class Pat:
    def __init__(self, nm="pat"):
        self.nm = nm
        self.sz = 5
    def apply(self, lyr, x, y, col=0, bg=0):
        if self.nm == "wave":
            self._wave(lyr, x, y, col, bg)
        elif self.nm == "mesh":
            self._mesh(lyr, x, y, col, bg) 
        elif self.nm == "dots":
            self._dots(lyr, x, y, col, bg)
        elif self.nm == "cross":
            self._cross(lyr, x, y, col, bg)
        elif self.nm == "spiral":
            self._spiral(lyr, x, y, col, bg)
        elif self.nm == "brick":
            self._brick(lyr, x, y, col, bg)
        elif self.nm == "hash":
            self._hash(lyr, x, y, col, bg)
        elif self.nm == "circle":
            self._circle(lyr, x, y, col, bg)
        elif self.nm == "arrow":
            self._arrow(lyr, x, y, col, bg)
        elif self.nm == "star":
            self._star(lyr, x, y, col, bg)
    def _wave(self, lyr, x, y, col=0, bg=0):
        for i in range(-5, 6):
            wx = x + i
            wy = int(y + 2 * math.sin(i * 0.5))
            lyr.set(wx, wy, '~', col, bg)
            lyr.set(wx, wy + 1, '≈', col, bg)
    def _mesh(self, lyr, x, y, col=0, bg=0):
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if dx % 2 == 0 and dy % 2 == 0:
                    lyr.set(x + dx, y + dy, 'o', col, bg)
                elif dx % 2 == 0:
                    lyr.set(x + dx, y + dy, '|', col, bg)
                elif dy % 2 == 0:
                    lyr.set(x + dx, y + dy, '-', col, bg)
    def _dots(self, lyr, x, y, col=0, bg=0):
        for i in range(8):
            angle = i * math.pi / 4
            dx = int(2 * math.cos(angle))
            dy = int(2 * math.sin(angle))
            lyr.set(x + dx, y + dy, '•', col, bg)
    def _cross(self, lyr, x, y, col=0, bg=0):
        for i in range(-3, 4):
            lyr.set(x + i, y, '#', col, bg)
            lyr.set(x, y + i, '#', col, bg)
        lyr.set(x, y, '+', col, bg)
    def _spiral(self, lyr, x, y, col=0, bg=0):
        for i in range(20):
            t = i * 0.3
            r = i * 0.2
            sx = int(x + r * math.cos(t))
            sy = int(y + r * math.sin(t))
            ch = ['*', '#', '@', '%'][i % 4]
            lyr.set(sx, sy, ch, col, bg)
    def _brick(self, lyr, x, y, col=0, bg=0):
        for dy in range(-2, 3):
            for dx in range(-4, 5):
                if dy % 2 == 0:
                    if dx % 4 == 0:
                        lyr.set(x + dx, y + dy, '#', col, bg)
                else:
                    if (dx + 2) % 4 == 0:
                        lyr.set(x + dx, y + dy, '#', col, bg)
    def _hash(self, lyr, x, y, col=0, bg=0):
        for i in range(-2, 3):
            if i != 0:
                lyr.set(x + i, y - 1, '#', col, bg)
                lyr.set(x + i, y + 1, '#', col, bg)
                lyr.set(x - 1, y + i, '#', col, bg)
                lyr.set(x + 1, y + i, '#', col, bg)
    def _circle(self, lyr, x, y, col=0, bg=0):
        r = 3
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            cx = int(x + r * math.cos(rad))
            cy = int(y + r * math.sin(rad))
            lyr.set(cx, cy, 'o', col, bg)
    def _arrow(self, lyr, x, y, col=0, bg=0):
        lyr.set(x, y, '>', col, bg)
        lyr.set(x - 1, y, '-', col, bg)
        lyr.set(x - 2, y, '-', col, bg)
        lyr.set(x + 1, y - 1, '/', col, bg)
        lyr.set(x + 1, y + 1, '\\', col, bg)
    def _star(self, lyr, x, y, col=0, bg=0):
        lyr.set(x, y, '*', col, bg)
        lyr.set(x, y - 1, '|', col, bg)
        lyr.set(x, y + 1, '|', col, bg)
        lyr.set(x - 1, y, '-', col, bg)
        lyr.set(x + 1, y, '-', col, bg)
        lyr.set(x - 1, y - 1, '\\', col, bg)
        lyr.set(x + 1, y - 1, '/', col, bg)
        lyr.set(x - 1, y + 1, '/', col, bg)
        lyr.set(x + 1, y + 1, '\\', col, bg)
class App:
    def __init__(self, scr):
        self.scr = scr
        self.h, self.w = scr.getmaxyx()
        self.cw = self.w - 2
        self.ch = self.h - 4
        self.cx = self.cw // 2
        self.cy = self.ch // 2
        self.zoom = 1.0    
        self.view_x = 0    
        self.view_y = 0    
        self.snap = False  
        self.tools = TOOLS
        self.tool = 0
        self.size = 1
        self.char = '#'
        self.thick = 1     
        self.col_names = [
            'default', 'blue', 'green', 'cyan', 'red', 'magenta', 'yellow', 'white',
            'black'
        ]
        self.bg_names = [
            'default', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white',
            'black'
        ]
        self.col = 0  
        self.bg_col = 0  
        self.lyrs = [Lyr(self.cw, self.ch, "main")]
        self.lyr = 0
        self.brs = [
            Brush(1, '#', 1, 0, "small"),     
            Brush(2, '#', 2, 0, "medium"),    
            Brush(3, '*', 4, 0, "large"),     
            Brush(4, '@', 5, 0, "huge"),      
            Brush(5, '█', 6, 0, "block")      
        ]
        self.br = 0
        self.pats = [
            Pat("wave"),
            Pat("mesh"), 
            Pat("dots"),
            Pat("cross"),
            Pat("spiral"),
            Pat("brick"),
            Pat("hash"),
            Pat("circle"),
            Pat("arrow"),
            Pat("star")
        ]
        self.pat = 0
        self.shapes = [
            "line", "box", "circle", "arrow", "star", "triangle", "diamond", "heart"
        ]
        self.shape = 0
        self.sx = None  
        self.sy = None  
        self.sel = None  
        self.clip = None  
        self.undo_stack = deque(maxlen=50)
        self.redo_stack = deque(maxlen=50)
        self.grid = False
        self.help = False
        self.dirty = True
        self.running = True
        self.txt_mode = False
        self.txt_buf = ""
        self.txt_x = 0
        self.txt_y = 0
        self.mouse_down = False
        self.last_mx = 0
        self.last_my = 0
        self.drawing = False
        self.fps = 0
        self.last_t = time.time()
        self.frames = 0
        self.stats = {
            'strokes': 0,     
            'saves': 0,       
            'undos': 0,       
            'tool_use': defaultdict(int),  
            'start_time': time.time()      
        }
        self.exp = False        
        self.debug_info = False 
        curses.curs_set(0)
        self.scr.nodelay(1)  
        self.scr.keypad(1)   
        self.ft = 16
        self.scr.timeout(self.ft)  
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            pair_id = 1
            fc = len(self.col_names)
            bc = len(self.bg_names)
            def ic(idx):
                if idx == 0:
                    return -1  
                if idx == 8:
                    return curses.COLOR_BLACK
                return idx  
            for fg in range(fc):
                for bg in range(bc):
                    if pair_id < 256:
                        fg_val = ic(fg)
                        bg_val = ic(bg)
                        try:
                            curses.init_pair(pair_id, fg_val, bg_val)
                        except:
                            pass
                        pair_id += 1
        try:
            curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
            curses.mouseinterval(0)
            import sys
            try:
                sys.stdout.write("\033[?1006h\033[?1003h")
                sys.stdout.flush()
            except Exception:
                pass
        except Exception:
            try:
                curses.mousemask(curses.BUTTON1_PRESSED | curses.BUTTON1_RELEASED | curses.BUTTON1_CLICKED)
            except Exception:
                pass
        self.sv()
    def get_lyr(self):
        if self.lyrs and 0 <= self.lyr < len(self.lyrs):
            return self.lyrs[self.lyr]
        else:
            return None
    def gl(self):
        return self.get_lyr()
    def sv(self):
        return self.save_state()
    def uf(self):
        return self.update_fps()
    def cb(self, x, y):
        return self.check_bounds(x, y)
    def sg(self, x, y):
        return self.snap_to_grid(x, y)
    def rp(self):
        return self.get_real_pos()
    def zp(self, x, y):
        return self.zoom_pt(x, y)
    def hk(self, k):
        return self.handle_keyboard(k)
    def hm(self, e):
        return self.handle_mouse(e)
    def ht(self):
        return self.handle_tool()
    def mt(self):
        return self.tool_menu()
    def mb(self):
        return self.brush_menu()
    def mc(self):
        return self.col_menu()
    def mp(self):
        return self.pat_menu()
    def ml(self):
        return self.lyr_menu()
    def ms(self):
        return self.shape_menu()
    def cc(self):
        return self.clr_canvas()
    def ca(self):
        return self.clr_all()
    def sh(self):
        return self.show_help()
    def rd(self):
        return self.render()
    def svf(self, fname="drawing.json"):
        return self.save_file(fname)
    def ldf(self, fname="drawing.json"):
        return self.load_file(fname)
    def al(self):
        return self.add_lyr()
    def dl(self):
        return self.del_lyr()
    def un(self):
        return self.undo()
    def re(self):
        return self.redo()
    def check_bounds(self, x, y):
        if x < 0 or y < 0:
            return False
        if x >= self.cw or y >= self.ch:
            return False
        return True
    def snap_to_grid(self, x, y):
        if self.snap:
            grid_size = 5  
            x = (x // grid_size) * grid_size
            y = (y // grid_size) * grid_size
        return x, y
    def zoom_pt(self, x, y):
        zx = int((x - self.view_x) * self.zoom)
        zy = int((y - self.view_y) * self.zoom)  
        return zx, zy
    def get_real_pos(self):
        real_x = int(self.cx / self.zoom + self.view_x)
        real_y = int(self.cy / self.zoom + self.view_y)
        if self.snap:
            real_x, real_y = self.snap_to_grid(real_x, real_y)
        return real_x, real_y
    def save_state(self):
        state = []
        for lyr in self.lyrs:
            lyr_state = {
                'data': [row[:] for row in lyr.d],
                'cols': [row[:] for row in lyr.cols],
                'bg_cols': [row[:] for row in lyr.bg_cols]
            }
            state.append(lyr_state)
        self.undo_stack.append(state)
        self.redo_stack.clear()
    def undo(self):
        if len(self.undo_stack) > 1:  
            self.redo_stack.append(self.undo_stack.pop())
            state = self.undo_stack[-1]
            for i, lyr_state in enumerate(state):
                if i < len(self.lyrs):
                    self.lyrs[i].d = [row[:] for row in lyr_state['data']]
                    if 'cols' in lyr_state:
                        self.lyrs[i].cols = [row[:] for row in lyr_state['cols']]
                    if 'bg_cols' in lyr_state:
                        self.lyrs[i].bg_cols = [row[:] for row in lyr_state['bg_cols']]
            self.stats['undos'] += 1
            self.dirty = True
    def redo(self):
        if self.redo_stack:
            state = self.redo_stack.pop()
            self.undo_stack.append(state)
            for i, lyr_state in enumerate(state):
                if i < len(self.lyrs):
                    self.lyrs[i].d = [row[:] for row in lyr_state['data']]
                    if 'cols' in lyr_state:
                        self.lyrs[i].cols = [row[:] for row in lyr_state['cols']]
                    if 'bg_cols' in lyr_state:
                        self.lyrs[i].bg_cols = [row[:] for row in lyr_state['bg_cols']]
            self.dirty = True
    def draw_pt(self, x, y, c=None, col=None, bg=None):
        lyr = self.get_lyr()
        if lyr:
            if c is None:
                c = self.char
            if col is None:
                col = self.col
            if bg is None:
                bg = self.bg_col
            lyr.set(x, y, c, col, bg)
    def draw_line(self, x1, y1, x2, y2):
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        if x1 < x2:
            sx = 1
        else:
            sx = -1
        if y1 < y2:
            sy = 1
        else:
            sy = -1
        err = dx - dy
        x = x1
        y = y1
        while True:
            if self.thick == 1:
                self.draw_pt(x, y)
            else:
                for tx in range(self.thick):
                    for ty in range(self.thick):
                        offset_x = tx - self.thick // 2
                        offset_y = ty - self.thick // 2
                        self.draw_pt(x + offset_x, y + offset_y)
            if x == x2 and y == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err = err - dy
                x = x + sx
            if e2 < dx:
                err = err + dx
                y = y + sy
    def draw_rect(self, x1, y1, x2, y2, fill=False):
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        if fill:
            for y in range(y1, y2 + 1):
                for x in range(x1, x2 + 1):
                    self.draw_pt(x, y)
        else:
            for x in range(x1, x2 + 1):
                self.draw_pt(x, y1)  
                self.draw_pt(x, y2)  
            for y in range(y1, y2 + 1):
                self.draw_pt(x1, y)  
                self.draw_pt(x2, y)  
    def draw_circ(self, cx, cy, r, fill=False):
        if fill:
            for y in range(cy - r, cy + r + 1):
                for x in range(cx - r, cx + r + 1):
                    if (x - cx)**2 + (y - cy)**2 <= r**2:
                        self.draw_pt(x, y)
        else:
            x, y = 0, r
            d = 3 - 2 * r
            self._draw_circ_pts(cx, cy, x, y)
            while y >= x:
                x += 1
                if d > 0:
                    y -= 1
                    d = d + 4 * (x - y) + 10
                else:
                    d = d + 4 * x + 6
                self._draw_circ_pts(cx, cy, x, y)
    def _draw_circ_pts(self, cx, cy, x, y):
        pts = [(cx+x, cy+y), (cx-x, cy+y), (cx+x, cy-y), (cx-x, cy-y),
               (cx+y, cy+x), (cx-y, cy+x), (cx+y, cy-x), (cx-y, cy-x)]
        for px, py in pts:
            self.draw_pt(px, py)
    def draw_arrow(self, x1, y1, x2, y2):
        self.draw_line(x1, y1, x2, y2)
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx*dx + dy*dy)
        if length > 2:  
            dx = dx / length
            dy = dy / length
            head_len = max(3, int(length * 0.3))  
            if head_len > 8:
                head_len = 8  
            angle = 0.6  
            perp_x = -dy
            perp_y = dx
            ax1 = x2 - head_len * dx + head_len * 0.4 * perp_x
            ay1 = y2 - head_len * dy + head_len * 0.4 * perp_y
            ax2 = x2 - head_len * dx - head_len * 0.4 * perp_x
            ay2 = y2 - head_len * dy - head_len * 0.4 * perp_y
            self.draw_line(x2, y2, int(ax1), int(ay1))
            self.draw_line(x2, y2, int(ax2), int(ay2))
    def draw_star(self, cx, cy, r):
        pts = []
        inner_r = r * 0.38  
        for i in range(10):  
            angle = i * math.pi / 5 - math.pi/2  
            if i % 2 == 0:
                x = cx + int(r * math.cos(angle))
                y = cy + int(r * math.sin(angle) * 0.6)  
            else:
                x = cx + int(inner_r * math.cos(angle))
                y = cy + int(inner_r * math.sin(angle) * 0.6)  
            pts.append((x, y))
        for i in range(10):
            next_i = (i + 1) % 10
            self.draw_line(pts[i][0], pts[i][1], pts[next_i][0], pts[next_i][1])
    def draw_triangle(self, cx, cy, r):
        pts = []
        v_scale = 0.7  
        for i in range(3):
            angle = i * 2 * math.pi / 3 - math.pi/2  
            x = cx + int(r * math.cos(angle))
            y = cy + int(r * math.sin(angle) * v_scale)
            pts.append((x, y))
        for i in range(3):
            next_i = (i + 1) % 3
            self.draw_line(pts[i][0], pts[i][1], pts[next_i][0], pts[next_i][1])
    def draw_hex(self, cx, cy, r):
        pts = []
        v_scale = 0.65  
        for i in range(6):
            angle = i * math.pi / 3 + math.pi/6  
            x = cx + int(r * math.cos(angle))
            y = cy + int(r * math.sin(angle) * v_scale)  
            pts.append((x, y))
        for i in range(6):
            next_i = (i + 1) % 6
            self.draw_line(pts[i][0], pts[i][1], pts[next_i][0], pts[next_i][1])
    def flood_fill(self, x, y, new_c=None, new_col=None, new_bg=None):
        lyr = self.get_lyr()
        if not lyr:
            return
        if new_c is None:
            new_c = self.char
        if new_col is None:
            new_col = self.col
        if new_bg is None:
            new_bg = self.bg_col
        old_c = lyr.get(x, y)
        old_col = lyr.get_col(x, y)
        if old_c == new_c and old_col == new_col:
            return
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if lyr.get(cx, cy) != old_c or lyr.get_col(cx, cy) != old_col:
                continue
            lyr.set(cx, cy, new_c, new_col, new_bg)
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < lyr.w and 0 <= ny < lyr.h:
                    if lyr.get(nx, ny) == old_c and lyr.get_col(nx, ny) == old_col:
                        stack.append((nx, ny))
    def spray_paint(self, x, y):
        for _ in range(self.size * 3):
            dx = random.randint(-self.size*2, self.size*2)
            dy = random.randint(-self.size*2, self.size*2) 
            if dx*dx + dy*dy <= (self.size*2)**2:
                self.draw_pt(x + dx, y + dy)
    def use_brush(self, x, y):
        br = self.brs[self.br]
        br.draw(self.get_lyr(), x, y, self.char, self.col, self.bg_col)
    def use_pat(self, x, y):
        pat = self.pats[self.pat]
        pat.apply(self.get_lyr(), x, y, self.col, self.bg_col)
    def handle_tool(self):
        tool = self.tools[self.tool]
        self.stats['tool_use'][tool] += 1
        if DEBUG:
            try:
                self.scr.addstr(self.h - 3, 0, f"Using tool: {tool} at {self.cx},{self.cy}", curses.A_DIM)
            except curses.error:
                pass
        if tool == "pen":
            self.use_brush(self.cx, self.cy)
            self.stats['strokes'] += 1
            self.save_state()
        elif tool == "ers":
            old_char = self.char
            old_col = self.col
            old_bg = self.bg_col
            self.char = ' '
            self.col = 0
            self.bg_col = 0
            self.use_brush(self.cx, self.cy)
            self.char = old_char
            self.col = old_col
            self.bg_col = old_bg
            self.save_state()
        elif tool == "line":
            if self.sx is None:
                self.sx, self.sy = self.cx, self.cy
            else:
                self.draw_line(self.sx, self.sy, self.cx, self.cy)
                self.sx, self.sy = None, None
                self.save_state()
        elif tool == "box":
            if self.sx is None:
                self.sx, self.sy = self.cx, self.cy
            else:
                self.draw_rect(self.sx, self.sy, self.cx, self.cy)
                self.sx, self.sy = None, None
                self.save_state()
        elif tool == "circ":
            if self.sx is None:
                self.sx, self.sy = self.cx, self.cy
            else:
                r = int(math.sqrt((self.cx - self.sx)**2 + (self.cy - self.sy)**2))
                self.draw_circ(self.sx, self.sy, r)
                self.sx, self.sy = None, None
                self.save_state()
        elif tool == "fill":
            self.flood_fill(self.cx, self.cy)
            self.save_state()
        elif tool == "spray":
            self.spray_paint(self.cx, self.cy)
            self.stats['strokes'] += 1
            self.save_state()
        elif tool == "text":
            self.txt_mode = True
            self.txt_buf = ""
            self.txt_x, self.txt_y = self.cx, self.cy
        elif tool == "sel":
            if self.sx is None:
                self.sx, self.sy = self.cx, self.cy
            else:
                x1, y1 = min(self.sx, self.cx), min(self.sy, self.cy)
                x2, y2 = max(self.sx, self.cx), max(self.sy, self.cy)
                self.sel = (x1, y1, x2, y2)
                self.sx, self.sy = None, None
        elif tool == "move":
            if self.sel and self.clip:
                self.paste_clip(self.cx, self.cy)
                self.save_state()
        elif tool == "copy":
            if self.sel:
                self.copy_sel()
        elif tool == "pat":
            self.use_pat(self.cx, self.cy)
            self.save_state()
        elif tool == "arrow":
            if self.sx is None:
                self.sx, self.sy = self.cx, self.cy
            else:
                self.draw_arrow(self.sx, self.sy, self.cx, self.cy)
                self.sx, self.sy = None, None
                self.save_state()
        elif tool == "star":
            if self.sx is None:
                self.sx, self.sy = self.cx, self.cy
            else:
                r = int(math.sqrt((self.cx - self.sx)**2 + (self.cy - self.sy)**2))
                if r < 3:
                    r = 3
                self.draw_star(self.sx, self.sy, r)
                self.sx, self.sy = None, None
                self.save_state()
        elif tool == "tri":
            if self.sx is None:
                self.sx, self.sy = self.cx, self.cy
            else:
                r = int(math.sqrt((self.cx - self.sx)**2 + (self.cy - self.sy)**2))
                if r < 3:
                    r = 3
                self.draw_triangle(self.sx, self.sy, r)
                self.sx, self.sy = None, None
                self.save_state()
        elif tool == "hex":
            if self.sx is None:
                self.sx, self.sy = self.cx, self.cy
            else:
                r = int(math.sqrt((self.cx - self.sx)**2 + (self.cy - self.sy)**2))
                if r < 3:
                    r = 3
                self.draw_hex(self.sx, self.sy, r)
                self.sx, self.sy = None, None
                self.save_state()
    def copy_sel(self):
        if not self.sel:
            return
        x1, y1, x2, y2 = self.sel
        lyr = self.get_lyr()
        if not lyr:
            return
        self.clip = []
        for y in range(y1, y2 + 1):
            row = []
            for x in range(x1, x2 + 1):
                ch = lyr.get(x, y)
                col = lyr.get_col(x, y)
                bg = lyr.get_bg(x, y)
                row.append((ch, col, bg))
            self.clip.append(row)
    def paste_clip(self, x, y):
        if not self.clip:
            return
        lyr = self.get_lyr()
        if not lyr:
            return
        for dy, row in enumerate(self.clip):
            for dx, (ch, col, bg) in enumerate(row):
                if ch != ' ':
                    lyr.set(x + dx, y + dy, ch, col, bg)
    def add_lyr(self):
        new_lyr = Lyr(self.cw, self.ch, f"layer{len(self.lyrs)+1}")
        self.lyrs.append(new_lyr)
        self.lyr = len(self.lyrs) - 1
        self.save_state()
    def del_lyr(self):
        if len(self.lyrs) > 1:
            del self.lyrs[self.lyr]
            self.lyr = min(self.lyr, len(self.lyrs) - 1)
            self.save_state()
    def clr_canvas(self):
        for lyr in self.lyrs:
            lyr.clr()
        self.save_state()
    def clr_all(self):
        self.scr.clear()
        h, w = self.scr.getmaxyx()
        msg1 = "Clear All - This will reset everything!"
        msg2 = "Canvas, layers, settings, history, clipboard..."
        msg3 = "Press Y to confirm, any other key to cancel"
        y_start = h // 2 - 2
        x1 = (w - len(msg1)) // 2
        x2 = (w - len(msg2)) // 2  
        x3 = (w - len(msg3)) // 2
        try:
            self.scr.addstr(y_start, x1, msg1, curses.A_BOLD | curses.A_REVERSE)
            self.scr.addstr(y_start + 1, x2, msg2)
            self.scr.addstr(y_start + 3, x3, msg3, curses.A_BOLD)
        except:
            self.scr.addstr(0, 0, "Clear All? Y/N")
        self.scr.refresh()
        try:
            curses.flushinp()  
            self.scr.nodelay(0)
            self.scr.timeout(-1)
            k = self.scr.getch()
            if k == ord('Y') or k == ord('y'):
                self.lyrs = [Lyr(self.cw, self.ch, "main")]
                self.lyr = 0
                self.undo_stack.clear()
                self.redo_stack.clear()
                self.clip = None
                self.sel = None
                self.view_x = 0
                self.view_y = 0
                self.zoom = 1.0
                self.tool = 0
                self.br = 0
                self.pat = 0
                self.thick = 1
                self.size = 2
                self.char = '#'
                self.col = 0
                self.bg_col = 0
                self.cx = self.cw // 2
                self.cy = self.ch // 2
                self.sx = None
                self.sy = None
                self.snap = False
                self.grid = False
                self.clr_canvas()
                self.save_state()
                self.scr.clear()
                success_msg = "Everything cleared! Press any key to continue..."
                x_pos = (w - len(success_msg)) // 2
                y_pos = h // 2
                try:
                    self.scr.addstr(y_pos, x_pos, success_msg, curses.A_BOLD | curses.A_STANDOUT)
                except:
                    self.scr.addstr(0, 0, "Cleared!")
                self.scr.refresh()
                self.scr.getch()
        finally:
            self.scr.nodelay(1)
            self.scr.timeout(self.ft)
        self.dirty = True
    def save_file(self, fname="drawing.json"):
        data = {
            'width': self.cw,
            'height': self.ch,
            'layers': []
        }
        for lyr in self.lyrs:
            lyr_data = {
                'name': lyr.nm,
                'visible': lyr.vis,
                'data': lyr.d,
                'colors': lyr.cols,
                'bg_colors': lyr.bg_cols
            }
            data['layers'].append(lyr_data)
        try:
            with open(fname, 'w') as f:
                json.dump(data, f)
            self.stats['saves'] += 1
            return True
        except:
            return False
    def load_file(self, fname):
        try:
            with open(fname, 'r') as f:
                data = json.load(f)
            self.cw = data['width']
            self.ch = data['height']
            self.lyrs = []
            for lyr_data in data['layers']:
                lyr = Lyr(self.cw, self.ch, lyr_data['name'])
                lyr.vis = lyr_data['visible']
                lyr.d = lyr_data['data']
                if 'colors' in lyr_data:
                    lyr.cols = [[int(col) if isinstance(col, str) else col for col in row] for row in lyr_data['colors']]
                if 'bg_colors' in lyr_data:
                    lyr.bg_cols = [[int(col) if isinstance(col, str) else col for col in row] for row in lyr_data['bg_colors']]
                self.lyrs.append(lyr)
            self.lyr = 0
            self.save_state()
            return True
        except:
            return False
    def show_menu(self, title, items, current):
        h = len(items) + 4
        if len(items) > 0:
            max_item_len = max(len(item) for item in items)
        else:
            max_item_len = 10  
        w = max(len(title) + 4, max_item_len + 6)
        sy = (self.h - h) // 2
        sx = (self.w - w) // 2
        for i in range(h):
            try:
                if sy + i < self.h and sx < self.w:
                    self.scr.addstr(sy + i, sx, ' ' * min(w, self.w - sx), curses.A_REVERSE)
            except curses.error:
                pass
        try:
            if sy + 1 < self.h and sx + 2 < self.w:
                self.scr.addstr(sy + 1, sx + 2, title[:self.w-sx-4], curses.A_REVERSE | curses.A_BOLD)
        except curses.error:
            pass
        for i, item in enumerate(items):
            try:
                if sy + i + 3 < self.h and sx + 1 < self.w:
                    marker = '>' if i == current else ' '
                    attr = curses.A_REVERSE | curses.A_BOLD if i == current else curses.A_REVERSE
                    display_text = f"{marker} {item}"[:self.w-sx-2]
                    self.scr.addstr(sy + i + 3, sx + 1, display_text, attr)
            except curses.error:
                pass
        self.scr.refresh()
    def tool_menu(self):
        while True:
            items = []
            for i in range(len(self.tools)):
                tool_name = self.tools[i]
                item = f"{i+1}. {tool_name}"
                items.append(item)
            self.show_menu("TOOLS", items, self.tool)
            k = self.scr.getch()
            if k == curses.KEY_UP or k == ord('w'):
                self.tool = self.tool - 1
                if self.tool < 0:
                    self.tool = len(self.tools) - 1
            elif k == curses.KEY_DOWN or k == ord('s'):
                self.tool = self.tool + 1
                if self.tool >= len(self.tools):
                    self.tool = 0
            elif k == ord('\n') or k == ord(' '):
                break
            elif k == 27:
                break
            elif ord('1') <= k <= ord('9'):
                idx = k - ord('1')
                if idx < len(self.tools):
                    self.tool = idx
                    break
        self.dirty = True
    def brush_menu(self):
        while True:
            items = []
            for i in range(len(self.brs)):
                br = self.brs[i]
                item = f"{i+1}. {br.nm} ({br.sz})"
                items.append(item)
            self.show_menu("BRUSHES", items, self.br)
            k = self.scr.getch()
            if k == curses.KEY_UP or k == ord('w'):
                self.br = self.br - 1
                if self.br < 0:
                    self.br = len(self.brs) - 1
            elif k == curses.KEY_DOWN or k == ord('s'):
                self.br = self.br + 1
                if self.br >= len(self.brs):
                    self.br = 0
            elif k == ord('\n') or k == ord(' '):
                break
            elif k == 27:
                break
        self.dirty = True
    def col_menu(self):
        while True:
            items = []
            for i in range(len(self.col_names)):
                name = self.col_names[i]
                if i == self.col:
                    marker = "►"
                else:
                    marker = " "
                sample = marker + " " + name
                items.append(sample)
            items.append("")
            bg_name = self.bg_names[self.bg_col]
            items.append("BG: " + bg_name)
            self.show_menu("COLORS (↑/↓ FG, SHIFT+↑/↓ BG)", items, self.col)
            k = self.scr.getch()
            if k == curses.KEY_UP or k == ord('w'):
                self.col = self.col - 1
                if self.col < 0:
                    self.col = len(self.col_names) - 1
            elif k == curses.KEY_DOWN or k == ord('s'):
                self.col = self.col + 1
                if self.col >= len(self.col_names):
                    self.col = 0
            elif k == curses.KEY_SR:  
                self.bg_col = self.bg_col - 1
                if self.bg_col < 0:
                    self.bg_col = len(self.bg_names) - 1
            elif k == curses.KEY_SF:  
                self.bg_col = self.bg_col + 1
                if self.bg_col >= len(self.bg_names):
                    self.bg_col = 0
            elif k == ord('B'):  
                self.bg_col = self.bg_col + 1
                if self.bg_col >= len(self.bg_names):
                    self.bg_col = 0
            elif k == ord('\n') or k == ord(' '):
                break
            elif k == 27:  
                break
            elif ord('0') <= k <= ord('9'):
                idx = k - ord('0')
                if idx < len(self.col_names):
                    self.col = idx
        self.dirty = True
    def pat_menu(self):
        while True:
            items = [pat.nm for pat in self.pats]
            self.show_menu("PATTERNS", items, self.pat)
            k = self.scr.getch()
            if k == curses.KEY_UP:
                self.pat = (self.pat - 1) % len(self.pats)
            elif k == curses.KEY_DOWN:
                self.pat = (self.pat + 1) % len(self.pats)
            elif k == ord('\n') or k == ord(' '):
                break
            elif k == 27:
                break
        self.dirty = True
    def lyr_menu(self):
        while True:
            items = []
            for i, lyr in enumerate(self.lyrs):
                vis = "+" if lyr.vis else "-"
                lock = "L" if lyr.lock else " "
                items.append(f"{vis}{lock} {lyr.nm}")
            self.show_menu("LAYERS", items, self.lyr)
            k = self.scr.getch()
            if k == curses.KEY_UP:
                self.lyr = (self.lyr - 1) % len(self.lyrs)
            elif k == curses.KEY_DOWN:
                self.lyr = (self.lyr + 1) % len(self.lyrs)
            elif k == ord('\n') or k == ord(' '):
                break
            elif k == 27:
                break
            elif k == ord('v'):  
                self.lyrs[self.lyr].vis = not self.lyrs[self.lyr].vis
            elif k == ord('l'):  
                self.lyrs[self.lyr].lock = not self.lyrs[self.lyr].lock
            elif k == ord('+'):
                self.add_lyr()
            elif k == ord('-'):
                self.del_lyr()
        self.dirty = True
    def shape_menu(self):
        while True:
            items = []
            for i in range(len(self.shapes)):
                shape_name = self.shapes[i]
                if i == self.shape:
                    marker = "►"
                else:
                    marker = " "
                line = marker + " " + shape_name
                items.append(line)
            self.show_menu("SHAPES", items, self.shape)
            k = self.scr.getch()
            if k == curses.KEY_UP:
                self.shape = self.shape - 1
                if self.shape < 0:
                    self.shape = len(self.shapes) - 1
            elif k == curses.KEY_DOWN:
                self.shape = self.shape + 1  
                if self.shape >= len(self.shapes):
                    self.shape = 0
            elif k == ord('\n') or k == ord(' '):
                break
            elif k == 27:  
                break
        self.dirty = True
    def show_help(self):
        help_txt = [
            "TERMINAL WHITEBOARD - HELP",
            "",
            "MOVEMENT:",
            "  WASD/Arrows - Move cursor",
            "  Mouse - Click to move & draw",
            "",
            "TOOLS:",
            "  SPACE - Use current tool",
            "  TAB - Tool menu (16 tools)",
            "  B - Brush menu", 
            "  P - Pattern menu (10 patterns)",
            "  L - Layer menu",
            "  K - Color menu (9 colors)",
            "  N - Shapes menu",
            "",
            "COLORS:",
            "  C - Cycle foreground color",
            "  V - Cycle background color", 
            "  K - Full color menu",
            "",
            "DRAWING:", 
            "  1-5 - Brush size & character",
            "  [ ] - Decrease/increase thickness",
            "  G - Toggle grid display",
            "  F - Toggle grid snap",
            "  U - Undo",
            "  R - Redo",
            "  X - Clear canvas",
            "  SHIFT+X - Clear canvas (no prompt)",
            "",
            "ZOOM & VIEW:",
            "  = - Zoom in",
            "  - - Zoom out", 
            "  0 - Reset zoom",
            "  CTRL+Arrows - Pan view",
            "",
            "SHAPES:",
            "  Arrow, Star, Triangle, Hexagon",
            "  Click start, click end",
            "",
            "FILES:",
            "  S - Save drawing",
            "  O - Open drawing",
            "",
            "H - Toggle this help",
            "Q - Quit",
            "",
            "New: Grid snap, zoom, 10 patterns,",
            "16 tools, shapes library!",
            "",
            "Press any key to close..."
        ]
        self.scr.clear()
        for i, line in enumerate(help_txt):
            if i < self.h - 1:
                self.scr.addstr(i, 2, line)
        self.scr.refresh()
        try:
            curses.flushinp()  
            self.scr.nodelay(0)
            self.scr.timeout(-1)
            self.scr.getch()
        finally:
            self.scr.nodelay(1)
            self.scr.timeout(self.ft)
        self.dirty = True
    def handle_mouse(self, event):
        try:
            id, x, y, z, state = curses.getmouse()
            cx = x
            cy = y - 1  
            if 0 <= cx < self.cw and 0 <= cy < self.ch:
                self.cx = cx
                self.cy = cy
                moved = (cx != self.last_mx or cy != self.last_my)
                if self.mouse_down and self.drawing and moved:
                    self.draw_line(self.last_mx, self.last_my, cx, cy)
                    self.last_mx = cx
                    self.last_my = cy
                if state & curses.BUTTON1_RELEASED:
                    if self.mouse_down:
                        if self.drawing and (cx != self.last_mx or cy != self.last_my):
                            self.draw_line(self.last_mx, self.last_my, cx, cy)
                        if self.drawing or self.tools[self.tool] not in ["pen", "ers"]:
                            self.sv()
                    self.mouse_down = False
                    self.drawing = False
                elif (state & curses.BUTTON1_PRESSED) and not self.mouse_down:
                    self.mouse_down = True
                    self.drawing = False
                    self.last_mx = cx
                    self.last_my = cy
                    if self.tools[self.tool] in ["pen", "ers"]:
                        self.ht()  
                        self.drawing = True
                    elif self.tools[self.tool] in ["line", "box", "circ", "arrow", "star", "tri", "hex"]:
                        if self.sx is None:
                            self.sx, self.sy = cx, cy
                        else:
                            self.ht()
                            self.sv()
                    else:
                        self.ht()
                        self.sv()
                elif (state & curses.BUTTON1_CLICKED) and not self.mouse_down:
                    self.ht()
                    self.sv()
                self.dirty = True
        except curses.error:
            pass
    def update_fps(self):
        self.frames += 1
        now = time.time()
        if now - self.last_t >= 1.0:
            self.fps = self.frames
            self.frames = 0
            self.last_t = now
    def render(self):
        if not self.dirty:
            return
        self.scr.clear()
        for y in range(self.ch):
            for x in range(self.cw):
                c = ' '
                fg_col = 0
                bg_col = 0
                for lyr in self.lyrs:
                    if lyr.vis:
                        px = lyr.get(x, y)
                        if px != ' ':
                            c = px
                            fg_col = lyr.get_col(x, y)
                            bg_col = lyr.get_bg(x, y)
                            if isinstance(fg_col, str):
                                fg_col = int(fg_col) if fg_col.isdigit() else 0
                            if isinstance(bg_col, str):
                                bg_col = int(bg_col) if bg_col.isdigit() else 0
                if self.grid and (x % 5 == 0 or y % 3 == 0) and c == ' ':
                    c = '·'
                try:
                    fc = len(self.col_names)
                    bc = len(self.bg_names)
                    pair_id = 1 + (fg_col * bc) + bg_col
                    mp = fc * bc
                    if pair_id < 1 or pair_id > mp:
                        pair_id = 1
                    attr = curses.color_pair(pair_id) if c != ' ' or bg_col > 0 else 0
                    self.scr.addch(y + 1, x, c, attr)
                except curses.error:
                    pass
        try:
            cur_c = self.gl().get(self.cx, self.cy) if self.gl() else ' '
            if cur_c == ' ':
                cur_c = '+'
            self.scr.addch(self.cy + 1, self.cx, cur_c, curses.A_REVERSE)
        except curses.error:
            pass
        if self.sel:
            x1, y1, x2, y2 = self.sel
            for x in range(x1, x2 + 1):
                try:
                    self.scr.addch(y1 + 1, x, '-', curses.A_BOLD)
                    self.scr.addch(y2 + 1, x, '-', curses.A_BOLD)
                except curses.error:
                    pass
            for y in range(y1, y2 + 1):
                try:
                    self.scr.addch(y + 1, x1, '|', curses.A_BOLD)
                    self.scr.addch(y + 1, x2, '|', curses.A_BOLD)
                except curses.error:
                    pass
        if self.sx is not None and self.sy is not None:
            try:
                self.scr.addch(self.sy + 1, self.sx, 'X', curses.A_BOLD | curses.A_BLINK)
            except curses.error:
                pass
        tool_name = self.tools[self.tool]
        lyr_name = self.get_lyr().nm if self.get_lyr() else "none"
        fg_name = self.col_names[self.col]
        bg_name = self.bg_names[self.bg_col]
        status = f"Tool: {tool_name} | FG: {fg_name} | BG: {bg_name} | Layer: {lyr_name}"
        status += f" | Pos: {self.cx},{self.cy} | Zoom: {self.zoom:.1f}x"
        if self.sx is not None and tool_name in ["line", "box", "circ", "arrow", "star", "tri", "hex"]:
            status += f" | START: {self.sx},{self.sy}"
        if self.snap:
            status += " | SNAP"
        if self.thick > 1:
            status += f" | T:{self.thick}"
        if self.debug_info:
            uptime = int(time.time() - self.stats['start_time'])
            status += f" | FPS: {self.fps} | Time: {uptime}s"
        try:
            self.scr.addstr(0, 0, status[:self.w-1])
        except curses.error:
            pass
        if self.txt_mode:
            txt_status = f"TEXT: {self.txt_buf}_"
            try:
                self.scr.addstr(self.h - 1, 0, txt_status[:self.w-1])
            except curses.error:
                pass
        else:
            bottom = f"TAB: Tools | K: Colors | N: Shapes | P: Patterns | F: Snap | =/-: Zoom | H: Help | Q: Quit"
            try:
                self.scr.addstr(self.h - 1, 0, bottom[:self.w-1])
            except curses.error:
                pass
        self.scr.refresh()
        self.dirty = False
    def run(self):
        while self.running:
            self.uf()
            if self.help:
                self.show_help()
                self.help = False
                continue
            self.render()
            while True:
                try:
                    k = self.scr.getch()
                    if k == -1 or k == curses.ERR:
                        break
                    if k == curses.KEY_MOUSE:
                        self.hm(k)
                    else:
                        self.hk(k)
                except curses.error:
                    break
    def handle_keyboard(self, k):
        if DEBUG and k != -1:
            try:
                self.scr.addstr(self.h - 2, 0, f"Key: {k} ({chr(k) if 32 <= k <= 126 else 'special'})", curses.A_DIM)
            except:
                pass
        if self.txt_mode:
            if k == 27:  
                    self.txt_mode = False
            elif k == 10 or k == 13:  
                    lyr = self.get_lyr()
                    if lyr:
                        for i, c in enumerate(self.txt_buf):
                            lyr.set(self.txt_x + i, self.txt_y, c)
                    self.txt_mode = False
                    self.save_state()
            elif k == 127 or k == curses.KEY_BACKSPACE:
                    self.txt_buf = self.txt_buf[:-1]
            elif 32 <= k <= 126:  
                    self.txt_buf += chr(k)
            self.dirty = True
            return
        if k == ord('q'):
            self.running = False
        elif k == curses.KEY_UP or k == ord('w'):
            if self.cy > 0:
                self.cy = self.cy - 1
            self.dirty = True
        elif k == curses.KEY_DOWN or k == ord('s'):
            if self.cy < self.ch - 1:
                self.cy = self.cy + 1
            self.dirty = True
        elif k == curses.KEY_LEFT or k == ord('a'):
            if self.cx > 0:
                self.cx = self.cx - 1
            self.dirty = True
        elif k == curses.KEY_RIGHT or k == ord('d'):
            if self.cx < self.cw - 1:
                self.cx = self.cx + 1
            self.dirty = True
        elif k == ord(' ') or k == 32:  
            self.ht()
            self.dirty = True
        elif k == ord('\t'):
            self.mt()
        elif k == ord('b'):
            self.mb()
        elif k == ord('p'):
            self.mp()
        elif k == ord('l'):
            self.ml()
        elif k == ord('k'):
            self.mc()
        elif k == ord('n'):
            self.ms()
        elif k == ord('['):
            if self.thick > 1:
                self.thick = self.thick - 1
            self.dirty = True
        elif k == ord(']'):
            if self.thick < 5:
                self.thick = self.thick + 1
            self.dirty = True
        elif k == ord('='):
            self.zoom = self.zoom * 1.2
            if self.zoom > 3.0:
                self.zoom = 3.0
            self.dirty = True
        elif k == ord('_'):
            self.zoom = self.zoom / 1.2  
            if self.zoom < 0.5:
                self.zoom = 0.5
            self.dirty = True
        elif k == ord('0'):
            self.zoom = 1.0
            self.view_x = 0
            self.view_y = 0
            self.dirty = True
        elif k == ord('f'):
            self.snap = not self.snap
            self.dirty = True
        elif k == curses.KEY_SR:  
            self.view_y = self.view_y - 2
            self.dirty = True
        elif k == curses.KEY_SF:  
            self.view_y = self.view_y + 2
            self.dirty = True
        elif k == curses.KEY_SLEFT:  
            self.view_x = self.view_x - 2
            self.dirty = True
        elif k == curses.KEY_SRIGHT:  
            self.view_x = self.view_x + 2
            self.dirty = True
        elif ord('1') <= k <= ord('5'):
            n = k - ord('0')  
            self.size = n
            if n <= len(self.brs):
                self.br = n - 1
                brush = self.brs[self.br]
                self.char = brush.c
                self.col = brush.fg
            self.dirty = True
        elif k == ord('c'):
            self.col = self.col + 1
            if self.col >= len(self.col_names):
                self.col = 0
            self.dirty = True
        elif k == ord('v'):
            self.bg_col = self.bg_col + 1
            if self.bg_col >= len(self.bg_names):
                self.bg_col = 0
            self.dirty = True
        elif k == ord('u'):
            self.undo()
        elif k == ord('r'):
            self.redo()
        elif k == ord('x'):
            self.clr_canvas()
            self.dirty = True
        elif k == ord('X'):  
            self.clr_canvas()
            self.dirty = True
        elif k == ord('g'):
            self.grid = not self.grid
            self.dirty = True
        elif k == ord('y'):
            if self.sel:
                self.copy_sel()
        elif k == ord('o'):  
            fname = "drawing.json"
            if os.path.exists(fname):
                self.load_file(fname)
                self.dirty = True
        elif k == ord('S'):  
            self.save_file("drawing.json")
        elif k == ord('+'):
            self.add_lyr()
            self.dirty = True
        elif k == ord('-'):
            self.del_lyr()
            self.dirty = True
        elif k == ord('~'):
            self.debug_info = not self.debug_info
            self.dirty = True
        elif k == ord('`'):
            self.exp = not self.exp
            self.dirty = True
        elif k == ord('D'):  
            toggle_debug()
            self.dirty = True
        elif k == ord('h'):
            self.help = True
        elif ord('6') <= k <= ord('9'):
            idx = k - ord('6') + 6  
            if idx < len(self.tools):
                self.tool = idx
                self.dirty = True
        elif k == ord(','):
            self.pat = (self.pat - 1) % len(self.pats)
            self.dirty = True
        elif k == ord('.'):
            self.pat = (self.pat + 1) % len(self.pats)
            self.dirty = True
        if k in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT, 
                 ord('w'), ord('a'), ord('s'), ord('d')]:
            self.sx = None
            self.sy = None
def main(scr):
    scr.clear()
    scr.refresh()
    h, w = scr.getmaxyx()
    if h < 20 or w < 60:
        scr.addstr(0, 0, f"Terminal too small: {w}x{h}. Need at least 60x20.")
        scr.addstr(1, 0, "Press any key to continue anyway...")
        scr.refresh()
        scr.getch()
    app = App(scr)
    app.run()
if __name__ == "__main__":
    curses.wrapper(main)
