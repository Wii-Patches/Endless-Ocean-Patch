"""Compile a small C blob (plus its assembly entry stub) to PowerPC words with devkitPPC."""
import os
import struct
import subprocess
import tempfile

DEVKIT = os.environ.get('DEVKITPPC', '/opt/devkitpro/devkitPPC')
CC = DEVKIT + '/bin/powerpc-eabi-'

CFLAGS = ['-O2', '-fno-unroll-loops', '-mbig-endian', '-msdata=none', '-ffreestanding', '-fno-pic',
          '-fno-asynchronous-unwind-tables', '-fno-stack-protector', '-fno-strict-aliasing', '-nostdlib', '-Wall']


def compile_blob(srcdir, cfile, sfile, defs, extra_defs, hard_float=False):
    """Build srcdir/cfile + srcdir/sfile (linked by srcdir/link.ld) and return its words.

    `defs` are numeric -D macros (addresses, offsets); `extra_defs` are ready-made -D strings.
    """
    tmp = tempfile.mkdtemp(prefix='eoblob')
    d = ['-D%s=%s' % (k, ('0x%08Xu' % v) if v > 255 else v) for k, v in defs.items()] + list(extra_defs)
    flags = CFLAGS + (['-mhard-float', '-mcpu=750'] if hard_float else ['-msoft-float'])
    subprocess.check_call([CC + 'gcc'] + flags + d + ['-c', os.path.join(srcdir, cfile), '-o', tmp + '/g.o'])
    subprocess.check_call([CC + 'gcc', '-mbig-endian', '-c', '-x', 'assembler-with-cpp'] + d +
                          [os.path.join(srcdir, sfile), '-o', tmp + '/h.o'])
    subprocess.check_call([CC + 'ld', '-T', os.path.join(srcdir, 'link.ld'), '-o', tmp + '/b.elf',
                           tmp + '/h.o', tmp + '/g.o'])
    subprocess.check_call([CC + 'objcopy', '-O', 'binary', tmp + '/b.elf', tmp + '/b.bin'])
    b = open(tmp + '/b.bin', 'rb').read()
    return list(struct.unpack('>%dI' % (len(b) // 4), b))
