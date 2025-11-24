import pygame
import sys
import time
import os

SCREEN_SCALE = 10
SCREEN_WIDTH = 24
SCREEN_HEIGHT = 24
SEGMENT_HEIGHT = 100
FPS = 60

ROM = [0] * 256
REG = [0] * 16
FLAGS = {"Z": 0, "C": 0}
PC = 0
HALT = False

screen_buf = [[0] * SCREEN_WIDTH for _ in range(SCREEN_HEIGHT)]
segment_value = 0

backupprint = print
start = 0
stop = 0
cycle_count = 0

def fakeprint(*args): pass

def decode(instr1, instr2):
    opcode = (instr1 & 0xF0) >> 4
    op = (instr1 & 0x0F) << 8 | instr2
    return opcode, op

def set_flag(val):
    FLAGS["Z"] = int(val == 0)
    FLAGS["C"] = int(val > 255 or val < 0)

def run_instruction():
    global PC, HALT, segment_value
    instr1 = ROM[PC % len(ROM)]
    instr2 = ROM[(PC + 1) % len(ROM)]
    opcode, operands = decode(instr1, instr2)
    PC = (PC + 2) % len(ROM)

    print("PC:", PC, "     Instruction:", hex((instr1 << 8) + instr2))

    if opcode == 0x0:
        return
    elif opcode == 0x1:
        HALT = True
    elif opcode in (0x2, 0x3, 0x4, 0x5, 0x6, 0x7):
        a = (operands >> 8) & 0xF
        b = (operands >> 4) & 0xF
        c = operands & 0xF

        if opcode == 0x2:
            s = REG[a] + REG[b]
            REG[c] = s & 0xFF
            FLAGS["C"] = int(s > 0xFF)
            FLAGS["Z"] = int(REG[c] == 0)

        elif opcode == 0x3:
            d = REG[a] - REG[b]
            REG[c] = d & 0xFF
            FLAGS["C"] = int(d < 0)
            FLAGS["Z"] = int(REG[c] == 0)

        elif opcode == 0x4:
            REG[c] = REG[a] & REG[b]
            FLAGS["C"] = 0
            FLAGS["Z"] = int(REG[c] == 0)

        elif opcode == 0x5:
            REG[c] = REG[a] | REG[b]
            FLAGS["C"] = 0
            FLAGS["Z"] = int(REG[c] == 0)

        elif opcode == 0x6:
            REG[c] = REG[a] ^ REG[b]
            FLAGS["C"] = 0
            FLAGS["Z"] = int(REG[c] == 0)

        elif opcode == 0x7:
            REG[c] = (~(REG[a] | REG[b])) & 0xFF
            FLAGS["C"] = 0
            FLAGS["Z"] = int(REG[c] == 0)

    elif opcode == 0x8:
        addr = operands & 0xFF
        PC = addr
    elif opcode == 0x9:
        a = (operands >> 8) & 0xF
        c = operands & 0xF
        REG[c] = REG[a] >> 1
        set_flag(REG[c])
    elif opcode == 0xA:
        a = (operands >> 8) & 0xF
        c = operands & 0xF
        REG[c] = (REG[a] << 1) & 0xFF
        set_flag(REG[c])
    elif opcode == 0xB:
        reg = (operands >> 8) & 0xF
        imm = operands & 0xFF
        REG[reg] = imm
    elif opcode == 0xC:
        reg = (operands >> 8) & 0xF
        imm = operands & 0xFF
        REG[reg] = (REG[reg] + imm) & 0xFF
        set_flag(REG[reg])
    elif opcode == 0xD:
        addr = operands & 0xFF
        if FLAGS["Z"]:
            PC = addr
    elif opcode == 0xE:
        x_reg = (operands >> 8) & 0xF
        y_reg = (operands >> 4) & 0xF
        x = REG[x_reg] % SCREEN_WIDTH
        y = REG[y_reg] % SCREEN_HEIGHT
        screen_buf[y][x] ^= 1

    elif opcode == 0xF:
        reg = (operands >> 8) & 0xF
        segment_value = REG[reg]
        print("New segment:", segment_value)

LAMP_BROWN = (0, 0, 0)
LAMP_YELLOW = (255, 235, 103)

def draw_screen(screen):
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    pxarray = pygame.PixelArray(surf)
    for y in range(SCREEN_HEIGHT):
        for x in range(SCREEN_WIDTH):
            if screen_buf[y][x]:
                pxarray[x, y] = LAMP_YELLOW
            else:
                pxarray[x, y] = LAMP_BROWN
    del pxarray
    scaled = pygame.transform.scale(surf, (SCREEN_WIDTH * SCREEN_SCALE, SCREEN_HEIGHT * SCREEN_SCALE))
    screen.blit(scaled, (0, 0))

def draw_segment(screen, value, font=None):
    font_path = os.path.join(os.path.dirname(__file__), "DS-DIGI.TTF")
    if not font:
        font = pygame.font.Font(font_path, 48)

    pygame.draw.rect(
        screen,
        LAMP_BROWN,
        (0, SCREEN_HEIGHT * SCREEN_SCALE, SCREEN_WIDTH * SCREEN_SCALE, 100)
    )
    text = font.render(f"{value:03}", True, LAMP_YELLOW)
    screen.blit(text, (10, SCREEN_HEIGHT * SCREEN_SCALE + 10))

_input_state = {"down": False, "left": False, "up": False, "right": False}

def update_input(events):
    global REG, _input_state

    for ev in events:
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_DOWN:
                _input_state["down"] = True
            elif ev.key == pygame.K_LEFT:
                _input_state["left"] = True
            elif ev.key == pygame.K_UP:
                _input_state["up"] = True
            elif ev.key == pygame.K_RIGHT:
                _input_state["right"] = True
        elif ev.type == pygame.KEYUP:
            if ev.key == pygame.K_DOWN:
                _input_state["down"] = False
            elif ev.key == pygame.K_LEFT:
                _input_state["left"] = False
            elif ev.key == pygame.K_UP:
                _input_state["up"] = False
            elif ev.key == pygame.K_RIGHT:
                _input_state["right"] = False

    try:
        keys = pygame.key.get_pressed()
        _input_state["down"]  = bool(keys[pygame.K_DOWN])  or _input_state["down"]
        _input_state["left"]  = bool(keys[pygame.K_LEFT])  or _input_state["left"]
        _input_state["up"]    = bool(keys[pygame.K_UP])    or _input_state["up"]
        _input_state["right"] = bool(keys[pygame.K_RIGHT]) or _input_state["right"]
    except Exception:
        pass

    if _input_state["down"]:
        REG[15] = 3
    elif _input_state["left"]:
        REG[15] = 2
    elif _input_state["up"]:
        REG[15] = 1
    elif _input_state["right"]:
        REG[15] = 4
    else:
        REG[15] = 0

def main(hz=1000.0, debug=False):
    global cycle_count,start,stop,backupprint, print
    if not debug:
        backupprint = print
        print = fakeprint

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH * SCREEN_SCALE, SCREEN_HEIGHT * SCREEN_SCALE + SEGMENT_HEIGHT))
    clock = pygame.time.Clock()
    pygame.display.set_caption("Hydrazen v2")

    icon_path = os.path.join(os.path.dirname(__file__), "icone", "hydrazen_icone.ico")  # PNG recommandé
    if os.path.exists(icon_path):
        icon = pygame.image.load(icon_path)
        pygame.display.set_icon(icon)

    try:
        font = pygame.font.SysFont("Courier", 48, bold=True)
    except Exception:
        font = pygame.font.Font(None, 48)

    cycle_time = 1.0 / hz
    cycle_count = 0
    last_cycle = time.time()
    start = time.time()
    stop = 0

    try:
        while True:
           
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    end()

            update_input(events)

            now = time.time()
            cycles_to_run = int((now - last_cycle) / cycle_time)

            for _ in range(cycles_to_run):
                if HALT:
                    if not stop:
                        stop = time.time()
                else:
                    run_instruction()
                    cycle_count += 1
                last_cycle += cycle_time

            screen.fill(LAMP_BROWN)
            draw_screen(screen)
            draw_segment(screen, segment_value, font)
            pygame.display.flip()
            clock.tick(FPS)
    except KeyboardInterrupt:
        end()

def end():
    global stop,start,backupprint,cycle_count
    if not stop:
        stop = time.time()
    try:
        backupprint(f"{cycle_count} cycles exécutés en {stop-start} secondes, moyenne {cycle_count / (stop-start)} cycles par seconde")
    except Exception:
        print(f"{cycle_count} cycles exécutés en {stop-start} secondes")
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()