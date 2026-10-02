/* Entry stubs for the Classic Controller hooks (see cc.c).  The last word is the
 * slot the hook installer turns into the branch back. */
    .macro SAVE
    stwu    1, -0x70(1)
    stw     0, 0x0c(1)
    stw     3, 0x10(1)
    stw     4, 0x14(1)
    stw     5, 0x18(1)
    stw     6, 0x1c(1)
    stw     7, 0x20(1)
    stw     8, 0x24(1)
    stw     9, 0x28(1)
    stw     10, 0x2c(1)
    stw     11, 0x30(1)
    stw     12, 0x34(1)
    mflr    0
    stw     0, 0x38(1)
    mfcr    0
    stw     0, 0x3c(1)
    mfctr   0
    stw     0, 0x40(1)
    mfxer   0
    stw     0, 0x44(1)
    .endm

    .macro RESTORE_ALL          /* everything but r0 */
    lwz     0, 0x44(1)
    mtxer   0
    lwz     0, 0x40(1)
    mtctr   0
    lwz     0, 0x3c(1)
    mtcr    0
    lwz     0, 0x38(1)
    mtlr    0
    lwz     3, 0x10(1)
    lwz     4, 0x14(1)
    lwz     5, 0x18(1)
    lwz     6, 0x1c(1)
    lwz     7, 0x20(1)
    lwz     8, 0x24(1)
    lwz     9, 0x28(1)
    lwz     10, 0x2c(1)
    lwz     11, 0x30(1)
    lwz     12, 0x34(1)
    .endm

    .section .gcstart, "ax"
    b       _entry

    .section .gctail, "ax"
    .globl _entry
_entry:
#if defined(HOOK_BUTTONS)
    # before `andi. r0,r7,0x9fff` in the sample loop: r7 = Wii Remote buttons,
    # r4 = extension type, r9 = Classic Controller buttons
    SAVE
    mr      3, 7
    mr      5, 9
    bl      cc_buttons
    stw     3, 0x08(1)
    RESTORE_ALL
    lwz     7, 0x08(1)
    lwz     0, 0x0c(1)
    addi    1, 1, 0x70
    DISP_BUTTONS
#elif defined(HOOK_POINTER)
    # the sample loop's `bl IR_FUNC` (r3 = KPAD struct, r4 = sample): run it, then
    # put the pointer where the sticks say
    stwu    1, -0x20(1)
    mflr    0
    stw     0, 0x24(1)
    stw     3, 0x08(1)
    stw     4, 0x0c(1)
    lis     12, FN_IR@ha
    addi    12, 12, FN_IR@l
    mtctr   12
    bctrl
    lwz     3, 0x08(1)
    lwz     4, 0x0c(1)
    bl      cc_pointer
    lwz     0, 0x24(1)
    mtlr    0
    addi    1, 1, 0x20
#endif
    nop
