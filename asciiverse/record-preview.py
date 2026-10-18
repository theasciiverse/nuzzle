#!/usr/bin/env python3
"""Records asciiverse/nuzzle.cast, the catalog preview, at 100x30
(hub/RECORDING.md): a game of Lines played from the keyboard by a driver
that reads the board and the three pieces from the screen, tries every
piece at every place, and picks the one that clears the most lines and
packs the board best. After about 50 seconds (or when no piece fits) it
quits with q.

nuzzle runs from out/ (asciiverse/build.sh) by name, with a fresh HOME so
the high score starts at 0, and the cast's header holds no local path.

Needs asciinema 3.x and pyte. Usage, from the repo root:
  uv run --with pyte python3 asciiverse/record-preview.py
Any extra argument is used as the cast's path instead (for test runs);
with --dry-run it plays without recording."""
import fcntl, os, pty, select, shutil, struct, sys, tempfile, termios, time
import pyte

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = [a for a in sys.argv[1:] if a != "--dry-run"]
dry = "--dry-run" in sys.argv
cast = os.path.abspath(args[0]) if args else f"{root}/asciiverse/nuzzle.cast"
COLS, ROWS, PLAY = 100, 30, float(os.environ.get("PLAY", "50"))
# keypad mode: the cursor keys send their application-mode codes
KEYS = {"up": b"\x1bOA", "down": b"\x1bOB", "right": b"\x1bOC", "left": b"\x1bOD"}
# Lines: 11 rows of 10 blocks, each block 4 columns by 2 rows; three home
# areas of 5x5 cells, each cell 2 columns by 1 row, 12 columns apart
B_ROWS, B_COLS = 11, 10

home = tempfile.mkdtemp()
env = dict(os.environ, HOME=home, TERM="xterm-256color", COLORTERM="truecolor", LANG="C.UTF-8",
           PATH=f"{root}/out:{os.environ['PATH']}")
for v in ("XDG_DATA_HOME", "VTE_VERSION", "TERM_PROGRAM", "TERM_PROGRAM_VERSION", "TMUX"):
    env.pop(v, None)

pid, fd = pty.fork()
if pid == 0:
    os.chdir(home)
    if dry:
        os.execvpe("nuzzle", ["nuzzle"], env)
    os.execvpe("asciinema", ["asciinema", "rec", "--overwrite", "-q", "--idle-time-limit", "2",
        "--window-size", f"{COLS}x{ROWS}", "--capture-env", "TERM,COLORTERM,LANG",
        "--title", "nuzzle", "--command", "nuzzle", cast], env)
fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLS, 0, 0))
screen = pyte.Screen(COLS, ROWS)
stream = pyte.ByteStream(screen)
start = time.time()


def pump(seconds):
    end = time.time() + seconds
    while True:
        left = end - time.time()
        r, _, _ = select.select([fd], [], [], max(0.0, min(0.02, left)))
        if r:
            try:
                stream.feed(os.read(fd, 65536))
            except OSError:
                return False
        if left <= 0:
            return True


def key(k, wait=0.12):
    os.write(fd, k)
    pump(wait)


def layout():
    """Row and column of the info box's corner, which sits beside the
    board's top right (4 columns of space after the 40 board columns)."""
    for y, line in enumerate(screen.display):
        x = line.find("┌")
        if x >= 0:
            return y, x
    return None


def counter(name):
    for line in screen.display:
        if name in line:
            return int(line.split(":")[1].strip(" │"))
    return None


def turn():
    return counter("Turn")


def read_state():
    y, x = layout()
    top, left = y, x - 44
    board = [[screen.display[top + 2 * r][left + 4 * c] == "█" for c in range(B_COLS)]
             for r in range(B_ROWS)]
    pieces = []
    for i in range(3):
        cells = [(r, c) for r in range(5) for c in range(5)
                 if screen.display[y + 9 + r][x + 12 * i + 2 * c] == "█"]
        if cells:
            r0 = min(r for r, _ in cells)
            c0 = min(c for _, c in cells)
            cells = [(r - r0, c - c0) for r, c in cells]
        pieces.append(cells)
    return board, pieces


def fits(board, piece, r, c):
    return all(0 <= r + pr < B_ROWS and 0 <= c + pc < B_COLS and not board[r + pr][c + pc]
               for pr, pc in piece)


def place(board, piece, r, c):
    b = [row[:] for row in board]
    for pr, pc in piece:
        b[r + pr][c + pc] = True
    full_rows = [i for i in range(B_ROWS) if all(b[i])]
    full_cols = [j for j in range(B_COLS) if all(b[i][j] for i in range(B_ROWS))]
    for i in full_rows:
        b[i] = [False] * B_COLS
    for j in full_cols:
        for i in range(B_ROWS):
            b[i][j] = False
    return b, len(full_rows) + len(full_cols)


def value(board, piece, r, c):
    after, cleared = place(board, piece, r, c)
    contact = 0
    for pr, pc in piece:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = r + pr + dr, c + pc + dc
            if not (0 <= rr < B_ROWS and 0 <= cc < B_COLS) or board[rr][cc]:
                contact += 1
    holes = 0
    for i in range(B_ROWS):
        for j in range(B_COLS):
            if not after[i][j] and all(not (0 <= i + di < B_ROWS and 0 <= j + dj < B_COLS)
                                       or after[i + di][j + dj]
                                       for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                holes += 1
    return cleared * 20 + contact - holes * 4


def first_fit(board, piece):
    """Where the game puts a picked up piece on the first arrow key: the
    first place, row by row, where its bounding box fits."""
    h = max(r for r, _ in piece) + 1
    w = max(c for _, c in piece) + 1
    for r in range(B_ROWS - h + 1):
        for c in range(B_COLS - w + 1):
            if fits(board, piece, r, c):
                return r, c
    return None


pump(1.5)
key(b"\r", 0.8)      # the menu: Lines
moves = 0
while time.time() - start < PLAY:
    board, pieces = read_state()
    best = None
    for i, piece in enumerate(pieces):
        if not piece:
            continue
        for r in range(B_ROWS):
            for c in range(B_COLS):
                if fits(board, piece, r, c):
                    v = value(board, piece, r, c)
                    if best is None or v > best[0]:
                        best = (v, i, r, c)
    if best is None:
        break
    _, i, r, c = best
    before = turn()
    tabs = 1 + sum(1 for j in range(i) if pieces[j])
    for _ in range(tabs):
        key(b"\t", 0.15)
    key(KEYS["right"], 0.2)
    fr, fc = first_fit(board, pieces[i])
    for _ in range(abs(r - fr)):
        key(KEYS["down" if r > fr else "up"], 0.08)
    for _ in range(abs(c - fc)):
        key(KEYS["right" if c > fc else "left"], 0.08)
    pump(0.25)
    key(b"\r", 1.0)
    if turn() == before:
        print(f"drop failed at move {moves}: piece {i} at {r},{c}, first fit {fr},{fc}", file=sys.stderr)
        if os.environ.get("DEBUG"):
            print("\n".join(screen.display), file=sys.stderr)
        break
    moves += 1
score = counter("Current")
pump(2.0)
key(b"q", 0.5)
end = time.time() + 5
while time.time() < end:
    if not pump(0.1):
        break
    done, _ = os.waitpid(pid, os.WNOHANG)
    if done:
        break
else:
    os.kill(pid, 9)
try:
    os.waitpid(pid, 0)
except ChildProcessError:
    pass
shutil.rmtree(home, ignore_errors=True)
print(f"{cast}: {time.time() - start:.0f} s, {moves} pieces placed, score {score}", file=sys.stderr)
