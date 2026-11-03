#!/bin/sh
# Builds nuzzle and its unit tests into out/, with the default config files
# in out/cfg/ beside the binary (nuzzle looks for them there). The compiler
# and curses libraries come from the environment, so one script serves every
# target (see .github/workflows/release.yml):
#
#   asciiverse/build.sh                                          # Linux
#   LIBS="-lmenuw -lncursesw" LDFLAGS="-static -s" asciiverse/build.sh    # Alpine, static
#   CFLAGS="-O2 -arch arm64 -I$NC/include" LDFLAGS="-arch arm64" \
#     LIBS="$NC/lib/libmenuw.a $NC/lib/libncursesw.a" asciiverse/build.sh  # macOS
#
# No Windows build: PDCurses has no menu library.
set -eu
cd "$(dirname "$0")/.."
CC="${CC:-cc}"
CFLAGS="${CFLAGS:--O2}"
LDFLAGS="${LDFLAGS:-}"
LIBS="${LIBS:-$(pkg-config --libs menuw ncursesw 2>/dev/null || echo -lmenuw -lncursesw)}"
JOBS="${JOBS:-2}"
mkdir -p out/obj
rm -rf out/cfg && cp -r cfg out/cfg
flags="-std=c11 -D_XOPEN_SOURCE=700 -D_DEFAULT_SOURCE -Wall -Wextra -Iinc $CFLAGS"
# compile at most $JOBS files at a time
# shellcheck disable=SC2086
ls src/*.c | xargs -P "$JOBS" -I{} sh -c 'f={}; o=out/obj/$(basename "$f" .c).o; nice -n 10 '"$CC $flags"' -c "$f" -o "$o"'
libs=$(ls out/obj/*.o | grep -v -e '/nuzzle\.o$' -e '/ut_test\.o$')
# shellcheck disable=SC2086
nice -n 10 $CC $CFLAGS $LDFLAGS -o out/nuzzle $libs out/obj/nuzzle.o $LIBS -lm
# shellcheck disable=SC2086
nice -n 10 $CC $CFLAGS $LDFLAGS -o out/ut_test $libs out/obj/ut_test.o $LIBS -lm
echo "built nuzzle"
