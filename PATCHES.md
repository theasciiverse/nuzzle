# Changes from upstream

This is the Asciiverse packaging of [nuzzle](https://github.com/dead-end/nuzzle)
by Dead End, a terminal collection of three block-placing puzzles (C,
ncursesw with the menu library). Upstream is the `upstream` remote; the
`asciiverse` branch carries the changes below.

Built from upstream `master` at `7f2822d` (2023-07-14), not the v0.3.2 tag
(2021-08-08): the ten commits since fix a crash when picking up an empty
home area and a `strncpy` size, add mouse events, and update the docs and
packaging scripts. Upstream tagged nothing later and the code still says
0.3.2, so the version here is 0.3.2+20230714.

## Licence

MIT. LICENSE reads "Copyright (c) 2019 dead-end", and every source and
header file carries the same MIT notice (2019 or 2020).

## Debian

Not packaged by Debian (checked 2026-10-18); upstream builds its own .deb
with `bin/build-pkgs.sh`, which is not used here.

## Code

- **Builds with musl and on macOS.** `on_exit()` (glibc only) is now
  `atexit()`, `<linux/limits.h>` is `<limits.h>`, with a fallback for
  `PATH_MAX`. The config reader's `index()` (a BSD leftover from
  `<strings.h>`, which the file never includes and macOS does not bring
  in on its own) is `strchr()` from `<string.h>`.
- **Scores in the XDG data folder, config beside the binary.** The score
  files moved from `~/.nuzzle` to `$XDG_DATA_HOME/nuzzle`
  (`~/.local/share/nuzzle`), made with its parents on the first saved
  score; an existing `~/.nuzzle` is still used. The default config files
  are also looked for in `cfg/` beside the executable (`/proc/self/exe`,
  `_NSGetExecutablePath`), so the unpacked archive runs from any working
  directory. The man page says the same.
- **Colours without redefining the terminal palette.** nuzzle refused to
  start unless the terminal could redefine colours, so it did not run in
  tmux, screen or the Linux console, and terminals that claim the
  capability but ignore it (macOS Terminal) showed its colours 16 to 32
  as dark blues. With 256 colours each colour from `color.cfg` now uses
  the nearest entry of the xterm palette; with fewer, colours are
  redefined where the terminal can, otherwise the nearest of the 8 basic
  colours is used.
- **The menu follows a resize.** It stayed where it was (a TODO in the
  code); it is now made again in the centre with the same item
  selected. A terminal smaller than the menu ended the game with "Unable
  to create window!"; it now says "Terminal too small" and waits.
- **Ctrl+C, SIGTERM and SIGHUP quit the way q does.** In raw mode Ctrl+C
  did nothing, and the two signals left the terminal with mouse motion
  tracking on. The signals now set a flag that the key reading turns into
  q, so the terminal is reset and the exit status is 0.
- **Fixes found with ASan and UBSan** (random keys, mouse sequences and
  resizes in tmux):
  - Enter with no blocks picked up dropped an undefined drop area: a
    write before the home area array (index -1) and colour lookups far
    outside the colour pair table. Enter now only drops picked up blocks.
  - A resize (SIGWINCH) during the drop animation made `usleep()` fail
    and ended the game; the pause is now a `nanosleep()` that carries on.
  - A mouse event that `getmouse()` cannot read ended the game; it is
    ignored now, in the game and in the menu.

## Packaging (new files)

- `asciiverse/build.sh`: compiles `src/` (two files at a time) into
  `out/nuzzle` and `out/ut_test`, with `cfg/` copied to `out/cfg/`; the
  compiler and curses libraries come from the environment. Upstream's
  makefile is left as it is.
- `asciiverse/package.sh`: one archive per target with the binary, its
  `cfg/` folder, the man page, README.md, LICENSE and this file.
- `.github/workflows/release.yml`: static Linux in Alpine (x86_64,
  aarch64) and macOS (x86_64, arm64), plus SHA256SUMS, on our tags
  (`*-av.*`); the unit tests run where the binary can run. macOS links
  ncurses 6.5 statically, built in the workflow for each architecture
  and reading the system's terminfo: the system's `libmenu` exports no
  symbols at all (its SDK stub lists none), so the menu cannot link
  against it. No Windows
  build: PDCurses has no menu library, and the menu is built on it.
- `asciiverse/record-preview.py`: records `asciiverse/nuzzle.cast`, a
  game of Lines played by a driver that reads the board and pieces from
  the screen and picks the placement that clears the most lines.
- `.gitignore`: the build folders.

av starts nuzzle with no arguments, at its menu of the three games.

## Tested

Linux: native (glibc) and static (Alpine 3.22, musl) builds; the unit
tests pass; played with keys and with the mouse at 100x30 under TERM
xterm-256color, tmux-256color, screen-256color and linux from the
unpacked archive in another working directory; scores written to
`~/.local/share/nuzzle`; resized down to 20x8 and back in the menu and
in a game; q, the menu's Exit, Ctrl+C, SIGTERM and SIGHUP all exit with
status 0 and mouse tracking off. ASan and UBSan: a 90-second soak found
the three bugs above, a 120-second soak after the fixes was clean.
macOS: not built here.

## Ours

- **How to play it, at the top of README.md.** A short note on installing and
  starting it with av, or from a release archive; the original text follows
  unchanged.
