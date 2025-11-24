import tkinter as tk
from tkinter import filedialog, messagebox
import musique.musique as music_player
import subprocess
import re
import sys
import os

OPCODES = {
    'NOP': 0x0,
    'HLT': 0x1,
    'ADD': 0x2,
    'SUB': 0x3,
    'AND': 0x4,
    'OR':  0x5,
    'XOR': 0x6,
    'NOR': 0x7,
    'JMP': 0x8,
    'RSH': 0x9,
    'LSH': 0xA,
    'LDI': 0xB,
    'ADI': 0xC,
    'BRZ': 0xD,
    'PLT': 0xE,
    'SEG': 0xF
}

def print_list_hex(lst):
    for item in lst:
        print(hex(item))

def reg_num_token(tok):
    return int(tok.strip().upper().replace("R", ""))

def assemble(asm):
    lines = []
    for raw_line in asm.splitlines():
        line = raw_line.split(";", 1)[0].strip()
        lines.append(line.upper())

    labels = {}
    pc = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            label, rest = line.split(":", 1)
            labels[label.strip()] = pc
            line = rest.strip()
            if not line:
                continue
        pc += 2

    rom = []
    for lineno, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            _, line = line.split(":", 1)
            line = line.strip()
            if not line:
                continue

        parts = line.split()
        if not parts:
            continue

        instr = parts[0]
        opcode = OPCODES.get(instr)
        if opcode is None:
            raise ValueError(f"Line {lineno}: Unknown instruction: {instr}")

        try:
            operands_str = line[len(instr):].strip()
            operands = [op.strip() for op in operands_str.split(",") if op.strip()]

            if instr in ('ADD', 'SUB', 'AND', 'OR', 'XOR', 'NOR'):
                if len(operands) != 3:
                    raise ValueError(f"Line {lineno}: Expected 3 operands")
                a, b, c = map(reg_num_token, operands)
                opval = (a << 8) | (b << 4) | c

            elif instr in ('RSH', 'LSH'):
                if len(operands) != 3:
                    raise ValueError(f"Line {lineno}: Expected 3 operands")
                a = reg_num_token(operands[0])
                c = reg_num_token(operands[2])
                opval = (a << 8) | c

            elif instr in ('LDI', 'ADI'):
                if len(operands) != 2:
                    raise ValueError(f"Line {lineno}: Expected 2 operands")
                r = reg_num_token(operands[0])
                val_tok = operands[1].upper()
                if re.match(r'^[A-Z_][A-Z0-9_]*$', val_tok) and val_tok in labels:
                    val = labels[val_tok]
                else:
                    val = int(val_tok, 0)
                opval = (r << 8) | (val & 0xFF)

            elif instr == 'SEG':
                if len(operands) != 1:
                    raise ValueError(f"Line {lineno}: Expected 1 operand")
                r = reg_num_token(operands[0])
                opval = (r << 8)

            elif instr in ('JMP', 'BRZ'):
                if len(operands) != 1:
                    raise ValueError(f"Line {lineno}: Expected 1 operand")
                arg = operands[0].upper()
                if re.match(r'^[A-Z_][A-Z0-9_]*$', arg) and arg in labels:
                    addr = labels[arg]
                else:
                    addr = int(arg, 0)
                opval = addr & 0xFF

            elif instr == 'PLT':
                if len(operands) != 2:
                    raise ValueError(f"Line {lineno}: Expected 2 operands")
                x, y = map(reg_num_token, operands)
                opval = (x << 8) | (y << 4)

            elif instr in ('NOP', 'HLT'):
                opval = 0

            else:
                raise ValueError(f"Line {lineno}: Invalid syntax")

            byte1 = (opcode << 4) | ((opval >> 8) & 0xF)
            byte2 = opval & 0xFF
            rom.append(byte1)
            rom.append(byte2)

        except Exception as e:
            raise ValueError(f"Line {lineno}: {e}")

    return rom

root = tk.Tk()
root.title("Hydra2 IDE")

ROOT_BG = "#1e1e1e"
EDITOR_BG = "#1e1e1e"
EDITOR_FG = "#d4d4d4"
SELECTION_BG = "#264f78"
BUTTON_BG = "#2d2d2d"
BUTTON_FG = "#d4d4d4"

root.configure(bg=ROOT_BG)

line_font = ("Courier", 12)
vscroll = tk.Scrollbar(root, orient=tk.VERTICAL)
vscroll.pack(side=tk.RIGHT, fill=tk.Y)

liner_frame = tk.Frame(root, bg=ROOT_BG)
liner_frame.pack(side=tk.LEFT, fill=tk.Y)

linenumbers = tk.Text(liner_frame, width=5, padx=4, pady=4, bd=0, takefocus=0,
                      bg="#252526", fg="#858585", relief=tk.FLAT, font=line_font,
                      state=tk.DISABLED)
linenumbers.pack(fill=tk.Y, expand=False)

editor = tk.Text(root, wrap=tk.NONE, font=("Courier", 12), bg=EDITOR_BG, fg=EDITOR_FG,
                 insertbackground=EDITOR_FG, selectbackground=SELECTION_BG, selectforeground="#ffffff",
                 relief=tk.FLAT, yscrollcommand=vscroll.set)
editor.pack(fill=tk.BOTH, expand=True)
vscroll.config(command=lambda *args: (editor.yview(*args), linenumbers.yview(*args)))

editor.tag_configure("opcode", foreground="#C586C0")
editor.tag_configure("reg", foreground="#569CD6")
editor.tag_configure("number", foreground="#DCDCAA")
editor.tag_configure("comment", foreground="#6A9955")
editor.tag_configure("label", foreground="#f44747")

editor.tag_configure("nib1", foreground="#f44747")
editor.tag_configure("nib2", foreground="#569CD6")
editor.tag_configure("nib3", foreground="#6A9955")
editor.tag_configure("nib4", foreground="#569CD6")

MAX_LINES = 64

def enforce_line_limit():
    try:
        total_lines = int(editor.index("end-1c").split(".")[0])
    except Exception:
        return
    if total_lines > MAX_LINES:
        start_delete = f"{MAX_LINES + 1}.0"
        editor.delete(start_delete, "end")
        try:
            messagebox.showwarning("Limite atteinte", f"Le fichier ne peut pas dépasser {MAX_LINES} lignes.")
        except Exception:
            pass

def update_line_numbers(event=None):
    enforce_line_limit()
    try:
        first_vis = int(editor.index("@0,0").split(".")[0])
        last_index = editor.index(f"@0,{editor.winfo_height() - 2}")
        last_vis = int(last_index.split(".")[0])
    except Exception:
        last_vis = int(editor.index("end-1c").split(".")[0])
        first_vis = 1

    if last_vis > MAX_LINES:
        last_vis = MAX_LINES
    if first_vis > MAX_LINES:
        first_vis = MAX_LINES

    start_num = max(0, first_vis - 1)
    end_num = max(0, last_vis - 1)

    lines = "".join(f"{i}\n" for i in range(start_num, end_num + 1))
    linenumbers.config(state=tk.NORMAL)
    linenumbers.delete("1.0", tk.END)
    linenumbers.insert("1.0", lines)
    linenumbers.config(state=tk.DISABLED)

def highlight_syntax(event=None):
    content = editor.get("1.0", "end-1c")
    for t in ("opcode", "reg", "number", "comment", "label"):
        editor.tag_remove(t, "1.0", "end")

    if not content:
        update_line_numbers()
        return

    comment_spans = []
    for m in re.finditer(r";.*", content):
        s, e = m.start(), m.end()
        editor.tag_add("comment", f"1.0+{s}c", f"1.0+{e}c")
        comment_spans.append((s, e))

    def in_comment(s, e):
        for a, b in comment_spans:
            if not (e <= a or s >= b):
                return True
        return False

    label_matches = list(re.finditer(r"(?m)^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:", content))
    label_spans = []
    for m in label_matches:
        s = m.start(1)
        e = m.end() + 1
        if in_comment(s, e):
            continue
        label_spans.append((s, e))
        editor.tag_add("label", f"1.0+{s}c", f"1.0+{e}c")

    jump_pattern = re.compile(r'\b(?:JMP|BRZ)\b\s+([A-Za-z_][A-ZaZ0-9_]*|0x[0-9A-Fa-f]+|\d+)', re.IGNORECASE)
    for m in jump_pattern.finditer(content):
        s = m.start(1)
        e = m.end(1)
        if in_comment(s, e):
            continue
        overlap = any(not (e <= a or s >= b) for (a, b) in label_spans)
        if not overlap:
            editor.tag_add("label", f"1.0+{s}c", f"1.0+{e}c")
            label_spans.append((s, e))

    ops = "|".join(re.escape(k) for k in OPCODES.keys())
    op_pattern = re.compile(r"\b(?:" + ops + r")\b", re.IGNORECASE)
    reg_pattern = re.compile(r"\bR(?:[0-9]|1[0-5])\b", re.IGNORECASE)
    num_pattern = re.compile(r"\b0x[0-9A-Fa-f]+\b|\b\d+\b")

    def overlaps_label(s, e):
        return any(not (e <= a or s >= b) for (a, b) in label_spans)

    def add_tag_from_matches(pattern, tag):
        for m in pattern.finditer(content):
            s, e = m.start(), m.end()
            if in_comment(s, e):
                continue
            if overlaps_label(s, e) and tag != "label":
                continue
            editor.tag_add(tag, f"1.0+{s}c", f"1.0+{e}c")

    add_tag_from_matches(op_pattern, "opcode")
    add_tag_from_matches(reg_pattern, "reg")
    add_tag_from_matches(num_pattern, "number")

    try:
        editor.tag_raise("label")
    except Exception:
        pass

    update_line_numbers()

def convert_to_binary():
    src_lines = editor.get("1.0", tk.END).splitlines()
    label_to_line = {}
    label_re = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(?:;.*)?$')
    for idx, raw in enumerate(src_lines):
        m = label_re.match(raw)
        if m:
            label_to_line[m.group(1).upper()] = idx * 2

    out_lines = []
    def reg_num_token(tok):
        t = tok.strip().upper()
        if not t.startswith("R"):
            raise ValueError("Registre attendu")
        return int(t[1:])

    for idx, raw in enumerate(src_lines):
        line_no_comment = raw.split(";", 1)[0].strip()
        if not line_no_comment:
            out_lines.append("0000000000000000")
            continue
        if label_re.match(line_no_comment):
            out_lines.append("0000000000000000")
            continue

        line = re.sub(r'^\s*[A-Za-z_][A-Za-z0-9_]*\s*:\s*', '', line_no_comment, count=1).strip()
        if not line:
            out_lines.append("0000000000000000")
            continue

        parts = [p.strip() for p in re.split(r'\s+', line, maxsplit=1) if p.strip()]
        instr = parts[0].upper()
        operands_part = parts[1] if len(parts) > 1 else ""
        operands = [o.strip() for o in re.split(r'\s*,\s*', operands_part) if o.strip()]

        opcode = OPCODES.get(instr)
        if opcode is None:
            out_lines.append("0000000000000000")
            continue

        try:
            opval = 0
            if instr in ('ADD', 'SUB', 'AND', 'OR', 'XOR', 'NOR'):
                a, b, c = map(reg_num_token, operands)
                opval = (a << 8) | (b << 4) | c
            elif instr in ('RSH', 'LSH'):
                a = reg_num_token(operands[0])
                c = reg_num_token(operands[2])
                opval = (a << 8) | c
            elif instr in ('LDI', 'ADI'):
                r = reg_num_token(operands[0])
                val_tok = operands[1].strip().upper()
                if re.match(r'^[A-Z_][A-Z0-9_]*$', val_tok):
                    val = label_to_line.get(val_tok, 0)
                else:
                    val = int(val_tok, 0)
                opval = (r << 8) | (val & 0xFF)
            elif instr == 'SEG':
                r = reg_num_token(operands[0])
                opval = (r << 8)
            elif instr in ('JMP', 'BRZ'):
                arg = operands[0].strip().upper()
                if re.match(r'^[A-Z_][A-Z0-9_]*$', arg):
                    addr = label_to_line.get(arg, 0)
                else:
                    addr = int(arg, 0)
                opval = addr & 0xFF
            elif instr == 'PLT':
                x = reg_num_token(operands[0])
                y = reg_num_token(operands[1])
                opval = (x << 8) | (y << 4)
            elif instr in ('NOP', 'HLT'):
                opval = 0
            else:
                opval = 0

            byte1 = (opcode << 4) | ((opval >> 8) & 0xF)
            byte2 = opval & 0xFF
            word = (byte1 << 8) | byte2
            bin16 = format(word & 0xFFFF, "016b")
            out_lines.append(bin16)
        except Exception:
            out_lines.append("0000000000000000")

    grouped_lines = []
    for ln in out_lines:
        ln = ln.strip()
        if len(ln) < 16:
            ln = ln.rjust(16, "0")
        elif len(ln) > 16:
            ln = ln[-16:]
        groups = [ln[i:i+4] for i in range(0, 16, 4)]
        grouped_lines.append(" ".join(groups))

    editor.delete("1.0", tk.END)
    editor.insert(tk.END, "\n".join(grouped_lines))

    apply_nibble_tags()
    highlight_syntax()
    update_line_numbers()

def apply_nibble_tags():
    for t in ("nib1", "nib2", "nib3", "nib4"):
        editor.tag_remove(t, "1.0", "end")

    lines = editor.get("1.0", "end-1c").splitlines()
    for i, line in enumerate(lines):
        bits = re.sub(r'[^01]', '', line)
        if len(bits) != 16:
            continue
        line_idx = i + 1
        offsets = [0, 5, 10, 15]
        tags = ("nib1", "nib2", "nib3", "nib4")
        for off, tag in zip(offsets, tags):
            start = f"{line_idx}.0+{off}c"
            end = f"{line_idx}.0+{off+4}c"
            editor.tag_add(tag, start, end)

def run_emulator(rom_bytes=None, speed=60.0, debug=False):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    runner_path = os.path.join(base_dir, "_temp_emulator_runner.py")
    emulator_path = os.path.join(base_dir, "hydrazen v2.py")

    with open(runner_path, "w", encoding="utf-8") as f:
        f.write("import importlib.util\n")
        f.write("import os\n")
        f.write(f"base_dir = os.path.dirname(os.path.abspath(__file__))\n")
        f.write(f"emulator_path = os.path.join(base_dir, 'hydrazen v2.py')\n")
        f.write("spec = importlib.util.spec_from_file_location('emulator', emulator_path)\n")
        f.write("emulator = importlib.util.module_from_spec(spec)\n")
        f.write("spec.loader.exec_module(emulator)\n")
        if rom_bytes is not None:
            f.write(f"emulator.ROM = {list(rom_bytes)}\n")
        f.write("emulator.main(60.0, debug=False)\n")

    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW

    subprocess.Popen([sys.executable, runner_path], creationflags=creationflags)

def on_assemble():
    try:
        asm = editor.get("1.0", tk.END)
        rom = assemble(asm)
        speed = float(speed_entry.get())
        run_emulator(rom, speed, debug_var.get())
    except Exception as e:
        messagebox.showerror("Assembly Error", str(e))

def on_open():
    path = filedialog.askopenfilename(filetypes=[("Hydra2 files", "*.hydra2"), ("All files", "*.*")])
    if path:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            editor.delete("1.0", tk.END)
            editor.insert(tk.END, f.read())
        enforce_line_limit()
        highlight_syntax()
        update_line_numbers()

def on_save():
    path = filedialog.asksaveasfilename(defaultextension=".hydra2",
                                        filetypes=[("Hydra2 files", "*.hydra2"), ("All files", "*.*")])
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(editor.get("1.0", tk.END))

toolbar = tk.Frame(root, bg=ROOT_BG, padx=8, pady=6)
toolbar.pack(fill=tk.X)

BTN_BG = "#3b3b3b"
BTN_ACTIVE = "#505050"
BTN_BORDER = "#5a5a5a"

btn_opts = {
    "bg": BTN_BG,
    "fg": BUTTON_FG,
    "activebackground": BTN_ACTIVE,
    "activeforeground": BUTTON_FG,
    "bd": 1,
    "relief": "groove",
    "highlightthickness": 1,
    "highlightbackground": BTN_BORDER,
    "padx": 8,
    "pady": 4
}

tk.Button(toolbar, text="Convert to binary", command=convert_to_binary, **btn_opts).pack(side=tk.LEFT, padx=6)
tk.Button(toolbar, text="Assemble & Run", command=on_assemble, **btn_opts).pack(side=tk.LEFT, padx=6)
tk.Button(toolbar, text="Open", command=on_open, **btn_opts).pack(side=tk.LEFT, padx=6)
tk.Button(toolbar, text="Save", command=on_save, **btn_opts).pack(side=tk.LEFT, padx=6)

speed_label = tk.Label(toolbar, text="Speed (Hz):", bg=ROOT_BG, fg=EDITOR_FG)
speed_label.pack(side=tk.LEFT, padx=(16,4))
speed_entry = tk.Entry(toolbar, width=6, bg="#2b2b2b", fg=EDITOR_FG, insertbackground=EDITOR_FG)
speed_entry.insert(0, "60.0")
speed_entry.pack(side=tk.LEFT, padx=(0,8))

debug_var = tk.BooleanVar()
CHECK_BG = "#1a1a2e"  

debug_check = tk.Checkbutton(
    toolbar,
    text="Debug Mode",
    variable=debug_var,
    bg=ROOT_BG,
    fg=EDITOR_FG,
    activebackground=ROOT_BG,
    activeforeground=EDITOR_FG,
    selectcolor=CHECK_BG,
    bd=0
)
debug_check.pack(side=tk.LEFT, padx=6)

music_var = tk.BooleanVar(value=False)

def toggle_music():
    if music_var.get():
        music_player.start_music()
    else:
        music_player.stop_music()

music_check = tk.Checkbutton(
    toolbar,
    text="Enable Music", 
    variable=music_var,
    command=toggle_music,
    bg=ROOT_BG,
    fg=EDITOR_FG,
    activebackground=ROOT_BG,
    activeforeground=EDITOR_FG,
    selectcolor="#23233b",
    bd=0
)
music_check.pack(side=tk.LEFT, padx=6)

icon_path = os.path.join(os.path.dirname(__file__), "icone", "hydrazen_icone.ico")

try:
    root.iconbitmap(icon_path)
except Exception as e:
    print("Impossible d'appliquer l'icône :", e)

editor.bind("<KeyRelease>", lambda e: (highlight_syntax(), enforce_line_limit(), update_line_numbers()))
editor.bind("<ButtonRelease-1>", update_line_numbers)
editor.bind("<Configure>", lambda e: (highlight_syntax(), enforce_line_limit(), update_line_numbers()))
editor.bind("<<Modified>>", lambda e=None: (highlight_syntax(), enforce_line_limit(), update_line_numbers(), editor.edit_modified(False)))

highlight_syntax()
update_line_numbers()

editor.config(
    insertbackground="#5a5a5a",
    insertwidth=2.5,
    insertofftime=300,
    insertontime=300
)

root.mainloop()