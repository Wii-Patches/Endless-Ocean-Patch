/* Entry stubs: save every volatile register, call the C hook, restore, then run
 * the instruction the hook replaced.  The last word is the slot the hook
 * installer turns into the branch back.
 *
 * Per-game parameters (-D): DISP_POLL / DISP_SAMPLE / DISP_PROBE are the
 * displaced instructions, SAMPLE_K / SAMPLE_CH the registers holding the KPAD
 * channel struct and the channel number at the sample hook. */
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
#if defined(HOOK_POLL)
    # KPADiRead(chan, ...): r3 = channel
    SAVE
    bl      gc_poll
    RESTORE_ALL
    lwz     0, 0x0c(1)
    addi    1, 1, 0x70
    DISP_POLL
#elif defined(HOOK_SAMPLE)
    # KPADiRead before the queued-sample check
    SAVE
    mr      3, SAMPLE_K
    mr      4, SAMPLE_CH
    bl      gc_sample
    RESTORE_ALL
    lwz     0, 0x0c(1)
    addi    1, 1, 0x70
    DISP_SAMPLE
#elif defined(HOOK_PROBE)
    # WPADProbe(chan, &type)
    SAVE
    bl      gc_probe
    stw     3, 0x08(1)
    RESTORE_ALL
    lwz     0, 0x08(1)
    addi    1, 1, 0x70
    cmpwi   0, 0
    beq     1f
    li      3, 0
    blr
1:  DISP_PROBE
#elif defined(HOOK_SCENE)
    # The controller-check scene is about to ask "Use the Classic Controller?".
    # With a pad plugged in, say yes without asking: run the game's own "use the
    # Classic Controller" routine, mark the scene finished and leave it.
    # (r31 = the scene object, a callee-saved register of the scene's function)
    SAVE
    bl      gc_present
    stw     3, 0x08(1)
    RESTORE_ALL
    lwz     0, 0x08(1)
    addi    1, 1, 0x70
    cmpwi   0, 0
    beq     1f
    lis     12, FN_USE_CC@ha
    addi    12, 12, FN_USE_CC@l
    mtctr   12
    bctrl
    lwz     3, 20(31)
    li      0, 20
    sth     0, 0(3)
    lis     12, SCENE_DONE@ha
    addi    12, 12, SCENE_DONE@l
    mtctr   12
    bctr
1:  DISP_SCENE
#elif defined(HOOK_DPD)
    # WPAD's "is the IR camera enabled" query: yes, for the pad (returns 1)
    SAVE
    bl      gc_dpd
    stw     3, 0x08(1)
    RESTORE_ALL
    lwz     0, 0x08(1)
    addi    1, 1, 0x70
    cmpwi   0, 0
    beq     1f
    li      3, 1
    blr
1:  DISP_DPD
#elif defined(HOOK_INFO) || defined(HOOK_INFOASYNC)
    # WPADGetInfo(chan, &info) / WPADGetInfoAsync(chan, &info, cb): answer for the
    # pad ourselves while no real Wii Remote is connected (returns 0 = no error)
    SAVE
#if defined(HOOK_INFO)
    bl      gc_info
#else
    bl      gc_infoasync
#endif
    stw     3, 0x08(1)
    RESTORE_ALL
    lwz     0, 0x08(1)
    addi    1, 1, 0x70
    cmpwi   0, 0
    beq     1f
    li      3, 0
    blr
1:
#if defined(HOOK_INFO)
    DISP_INFO
#else
    DISP_INFOASYNC
#endif
#endif
    nop
