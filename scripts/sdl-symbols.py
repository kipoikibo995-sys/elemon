"""Prints the SDL_* functions that the given ELF64 little-endian object files use but do not define.

Used by build-arm64.ps1 to make a stand-in libSDL2 (the real one is on the handheld).
"""
import struct
import sys

names = set()
for path in sys.argv[1:]:
    d = open(path, 'rb').read()
    shoff, = struct.unpack_from('<Q', d, 0x28)
    shentsize, shnum = struct.unpack_from('<HH', d, 0x3A)
    secs = [struct.unpack_from('<IIQQQQIIQQ', d, shoff + i * shentsize) for i in range(shnum)]
    for s in secs:
        if s[1] != 2:          # SHT_SYMTAB
            continue
        strtab = secs[s[6]]
        for off in range(s[4], s[4] + s[5], 24):
            name, info, other, shndx, value, size = struct.unpack_from('<IBBHQQ', d, off)
            if shndx == 0 and name:
                n = d[strtab[4] + name:d.index(b'\0', strtab[4] + name)].decode()
                if n.startswith('SDL_'):
                    names.add(n)
print('\n'.join(sorted(names)))
