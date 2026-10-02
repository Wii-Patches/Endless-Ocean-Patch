"""Build the SDHC feature (Endless Ocean, USA) from the City Folk / Pokemon Ranch fix.

Endless Ocean links the same Nintendo PFD SD driver as Animal Crossing: City Folk,
instruction for instruction at every site, so Bero's SDHC Extension carries over:
the driver assumes a standard-capacity card (byte addresses, CSD v1 capacity), and
the fix reads the SDHC bit IOS reports, then uses block addresses and the CSD v2
capacity formula.  Blue World's driver is newer and already does all of this itself
(it checks the same IOS status bit), so it has no SDHC feature.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
import asm
from ops import Blob, Feature, Hook, Patch, b_insn

# Dead padding in the .init exception-vector image (zero in the retail DOL); the
# run's address differs per release.  Layout from the cave base: three helpers,
# FLAG, then the hook trampolines.
CAVES = {'RFBE01': (0x800058C0, 0x80005D80)}      # (base, end)

# Retail sites by disc id: (site, retail word at the site)
SITES = {
    'RFBE01': dict(
        status=(0x8035EC10, 0x2C1D0000),    # ISD_GetDeviceStatus: cmpwi r29,0
        csd=(0x803774A8, 0x80A1000C),       # pfd_sddrv_get_total_sectors: lwz r5,0xc(r1)
        count=(0x8035ECE4, 0x38C00001),     # duCommandv: li r6,1
        resp=(0x8035EE0C, 0x806DE19C),      # duCommandv: lwz r3,-0x1e64(r13)
        read_chk=(0x8035F25C, 0x7C040040),  # ISD_ReadMultiBlockAsync: cmplw r4,r0
        write_chk=(0x8035F598, 0x7C040040),
        read_mul=(0x803770B0, 0x7F2531D6),  # pfd_sddrv_physical_read: mullw r25,r5,r6
        write_mul=(0x803772AC, 0x7F2531D6),
        read_add=(0x803771FC, 0x7F39BA14),  # add r25,r25,r23
        write_add=(0x803773F8, 0x7F39BA14),
    ),
}

STATUS = f'''
    rlwinm  3, 3, 12, 31, 31            # IOS status word: SDHC bit -> 0/1
    lis     4, FLAG@ha
    ori     4, 4, FLAG@l
    stw     3, 0(4)                     # FLAG follows the card in the slot
    cmpwi   29, 0                       # displaced
'''
CSD = '''
    lwz     3, 0x14(1)
    rlwinm. 3, 3, 0, 9, 9               # CSD_STRUCTURE == 1 (SDHC)?
    beq     1f
    li      0, 9
    lwz     3, 0x0c(1)
    rlwinm  3, 3, 24, 10, 31            # C_SIZE (22 bits)
    addi    3, 3, 1
    mulli   6, 3, 0x400                 # sectors = (C_SIZE + 1) * 1024
    lis     3, TARGET@ha
    ori     3, 3, TARGET@l              # the v1 code just after its own maths
    mtctr   3
    bctr
1:  lwz     5, 0x0c(1)                  # displaced
'''
COUNT = '''
    li      6, 0
    cmpwi   22, 0                       # r22 = FLAG, loaded by helper1
    beq     1f
    li      6, 1                        # displaced
1:  nop
'''
RESP = '''
    lwz     3, 0x1c(28)
    cmpwi   3, 1
    lwz     3, ORIG_OFF(13)             # displaced
    beq     1f
    lwz     0, 0(3)
    stw     0, 0(25)
    lwz     0, 4(3)
    stw     0, 4(25)
    lwz     0, 8(3)
    stw     0, 8(25)
    lwz     0, 12(3)
    stw     0, 12(25)
    lis     3, TARGET@ha
    ori     3, 3, TARGET@l
    mtctr   3
    bctr
1:  nop
'''
HELPER1 = '''
    lis     22, FLAG@ha
    ori     22, 22, FLAG@l
    lwz     22, 0(22)                   # r22 = FLAG (hook for duCommandv reads it too)
    cmpwi   22, 0
    beq     1f
    mr      0, 4                        # SDHC: the offset is a block number, always "aligned"
1:  cmplw   4, 0                        # displaced
    blr
'''
HELPER2 = '''
    lis     24, FLAG@ha
    ori     24, 24, FLAG@l
    lwz     24, 0(24)
    cmpwi   24, 0
    beq     1f
    mr      25, 5                       # SDHC: the sector index is the address
    b       2f
1:  mullw   25, 5, 6                    # displaced
2:  clrlwi. 0, 4, 27                    # restore CR0 for the caller
    blr
'''
HELPER3 = '''
    lis     3, FLAG@ha
    ori     3, 3, FLAG@l
    lwz     3, 0(3)
    cmpwi   3, 0
    beq     1f
    addi    25, 25, 1                   # SDHC: advance one block
    b       2f
1:  add     25, 25, 23                  # displaced
2:  blr
'''


def build(region, dol):
    s = SITES[region]
    for k, (addr, want) in s.items():
        got = struct.unpack('>I', dol.read(addr, 4))[0]
        if got != want:
            raise SystemExit('%s: %s at 0x%08X is 0x%08X, expected 0x%08X' % (region, k, addr, got, want))
    base, end = CAVES[region]
    H1, H2, H3, FLAG, TRAMP = base, base + 0x20, base + 0x48, base + 0x70, base + 0x80
    for a in range(base, end, 4):
        if dol.read(a, 4) != b'\0\0\0\0':
            raise SystemExit('%s: cave 0x%08X is not zero' % (region, a))
    ops = []
    for addr, text, note in ((H1, HELPER1, 'helper1: SDHC block offsets pass the alignment check'),
                             (H2, HELPER2, 'helper2: sector -> block address'),
                             (H3, HELPER3, 'helper3: advance one block')):
        ops.append(Blob(addr, asm.assemble(text, addr, dict(FLAG=FLAG)), note))
    ops.append(Blob(FLAG, b'\0\0\0\0', 'FLAG: 1 = SDHC card in the slot'))
    for key, hl in (('read_chk', H1), ('write_chk', H1), ('read_mul', H2), ('write_mul', H2),
                    ('read_add', H3)):
        addr, orig = s[key]
        ops.append(Patch(addr, struct.pack('>I', b_insn(hl, addr, link=True)), struct.pack('>I', orig),
                         '%s -> bl helper' % key))
    addr, orig = s['write_add']
    ops.append(Patch(addr, struct.pack('>I', b_insn(H3, addr, link=True)), struct.pack('>I', orig), 'write_add -> bl helper3'))

    cur = TRAMP

    def hook(key, text, note, syms=None, consts=None):
        nonlocal cur
        addr, orig = s[key]
        body = asm.words(asm.assemble(text, cur, dict(syms or {}, FLAG=FLAG), consts)) + [0]
        ops.append(Hook(addr, orig, body, cur, note=note))
        cur += len(body) * 4

    hook('status', STATUS, 'ISD_GetDeviceStatus: remember whether the card is SDHC')
    csd = s['csd'][0]
    hook('csd', CSD, 'get_total_sectors: CSD v2 capacity', dict(TARGET=csd + 0x40))
    hook('count', COUNT, 'duCommandv: block-count argument')
    resp = s['resp']
    off = struct.unpack('>I', struct.pack('>I', resp[1]))[0] & 0xFFFF
    hook('resp', RESP, 'duCommandv: four-word response copy', dict(TARGET=resp[0] + 0xC),
         dict(ORIG_OFF=off - 0x10000 if off & 0x8000 else off))
    if cur > end:
        raise SystemExit('sd trampolines overflow 0x%X' % cur)
    return Feature('sd', 'SDHC card support', region, ops)
