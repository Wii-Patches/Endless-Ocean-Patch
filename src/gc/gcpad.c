/* GameCube controller (port 1) -> Classic Controller bridge for Endless Ocean.
 *
 * Three hooks, one blob each (hooks.S has the register-saving entry stubs).
 * The game links the SI library but nothing polls the pads, so gc_poll() drives
 * the Serial Interface's own auto-polling (the approach is Barrel Blast Patch's,
 * hardware-tested there).  gc_sample() turns the pad into Classic Controller
 * samples in KPAD's ring, and gc_probe() makes WPADProbe report a Classic
 * Controller on channel 0 while a pad is plugged in, so the game treats the pad
 * as one.  Everything downstream -- button translation, cursor, swimming --
 * is then the game's own Classic Controller code.
 *
 * Addresses and KPAD offsets come in as -D macros, per game and disc release.
 */
typedef unsigned int u32;
typedef signed int s32;
typedef unsigned short u16;
typedef signed short s16;
typedef unsigned char u8;
typedef signed char s8;

#define R32(a) (*(volatile u32 *)(a))
#define SI_OUT0   (0xCD006400u)
#define SI_IN0H   (0xCD006404u)
#define SI_IN0L   (0xCD006408u)
#define SI_POLL   (0xCD006430u)
#define SI_COMCSR (0xCD006434u)
#define SI_SR     (0xCD006438u)

struct st {
    u32 probe_tb;   /* last SIGetType */
    u32 busy_tb;    /* when si:: was first seen busy (0 = idle) */
    u8 norep;       /* consecutive frames with NOREP on port 1 */
    u8 pad[3];
    u32 prev_btn;   /* Classic Controller buttons of the previous frame's sample */
};
#define ST ((volatile struct st *)STATE)

static inline u32 tb(void)
{
    u32 t;
    __asm__ volatile("mftb %0" : "=r"(t));
    return t;
}

/* a valid, error-free pad response on port 1 */
static inline int gc_in(u32 *h, u32 *l)
{
#ifdef DEBUG_FEED
    /* test builds: the pad's response is written to STATE+0x20/0x24 by a debugger */
    if (!R32(STATE + 0x20))
        return 0;
    *h = R32(STATE + 0x20);
    *l = R32(STATE + 0x24);
    return 1;
#else
    u32 v = R32(SI_IN0H);
    if ((v & 0x80000000u) || !(v & 0x00800000u))
        return 0;
    *h = v;
    *l = R32(SI_IN0L);
    return 1;
#endif
}

#if defined(HOOK_POLL)
void gc_poll(u32 chan)
{
    volatile u32 *types = (volatile u32 *)SI_TYPES;
    u32 type, sisr, mask, poll;
    int confirmed;
    s32 busy;

    if (chan)
        return;

    /* probe the port until a standard pad answers, at most every 0.25 s:
     * probing every frame collided with the pad's own polling on hardware */
    type = types[0];
    confirmed = !(type & 0x80) && (type & 0x18000000u) == 0x08000000u;
    if (!confirmed) {
        u32 now = tb();
        if (now - ST->probe_tb >= 15187500u) {
            ST->probe_tb = now;
            ((u32 (*)(u32))FN_SIGETTYPE)(0);
        }
    }

    /* an unplugged pad latches NOREP; si:: never reads it (no PAD library),
     * so copy a persistent one into the type cache ourselves, which makes
     * SIGetType probe the port again once a pad is plugged back in */
    sisr = R32(SI_SR);
    if (sisr & 0x08000000u) {
        if (ST->norep < 10)
            ST->norep++;
        else
            types[0] = 8;
    } else {
        ST->norep = 0;
    }

    R32(SI_OUT0) = 0x00400300u;                    /* poll command */
    R32(SI_SR) = (sisr & 0x0F0F0F0Fu) | 0x80000000u; /* ack errors, latch OUT */

    type = types[0];
    confirmed = !(type & 0x80) && (type & 0x18000000u) == 0x08000000u;
    mask = confirmed ? 0x88u : 0;                  /* EN0 + VBCPY0 */
    poll = R32(SI_POLL) & ~0xFFu;
    if (!(poll & 0xFF00u))
        poll |= 0x0100u;
    R32(SI_POLL) = poll | mask;
    /* si:: rewrites SIPOLL from its own shadow on every retrace */
    R32(SI_SHADOW) = (R32(SI_SHADOW) & ~0xFFu) | mask;

    /* a pad unplugged mid-transfer leaves si::'s global busy flag wedged
     * (nothing times it out); force it idle after a second */
    busy = (s32)R32(SI_BUSY);
    if (busy == -1) {
        ST->busy_tb = 0;
    } else {
        u32 now = tb();
        if (ST->busy_tb == 0) {
            ST->busy_tb = now | 1;
        } else if (now - ST->busy_tb >= 60750000u) {
            u32 lvl = ((u32 (*)(void))FN_OSDISABLE)();
            R32(SI_BUSY) = (u32)-1;
            R32(SI_COMCSR) = 0x80000000u;
            ((void (*)(u32))FN_OSRESTORE)(lvl);
            ST->busy_tb = 0;
        }
    }
}
#endif

#if defined(HOOK_SAMPLE)
/* Classic Controller buttons as WPAD reports them */
#define CL_UP    0x0001
#define CL_LEFT  0x0002
#define CL_ZR    0x0004
#define CL_X     0x0008
#define CL_A     0x0010
#define CL_Y     0x0020
#define CL_B     0x0040
#define CL_ZL    0x0080
#define CL_R     0x0200
#define CL_PLUS  0x0400
#define CL_MINUS 0x1000
#define CL_L     0x2000
#define CL_DOWN  0x4000
#define CL_RIGHT 0x8000

/* a sample made by us carries this in its (otherwise unused) last byte */
#define MARK 0xA5

static inline s16 stick(u32 raw)
{
    s32 v = ((s32)(raw & 0xFF) - 128) * 3;       /* pad ~+-100 -> game +-300 */
    if (v > 308)
        v = 308;
    if (v < -308)
        v = -308;
    return (s16)v;
}

static __attribute__((noinline)) u32 cc_buttons(u32 h)
{
    u32 b = 0;

    if (h & 0x01000000u) b |= CL_A;
    if (h & 0x02000000u) b |= CL_B;
    if (h & 0x04000000u) b |= CL_X;
    if (h & 0x08000000u) b |= CL_Y;
    if (h & 0x10000000u) b |= CL_PLUS;
    if (h & 0x00100000u) b |= CL_MINUS;      /* Z */
    if (h & 0x00400000u) b |= CL_L;
    if (h & 0x00200000u) b |= CL_R;
    if (h & 0x00080000u) b |= CL_UP;
    if (h & 0x00040000u) b |= CL_DOWN;
    if (h & 0x00020000u) b |= CL_RIGHT;
    if (h & 0x00010000u) b |= CL_LEFT;
    return b;
}

/* KPAD ring: `idx` is the next slot to write, `count` how many are queued; the
 * ring is 16 slots in the channel struct plus an optional extra buffer. */
#if K_EXTLEN
static inline u32 ring_len(u8 *k)
{
    return 16 + *(u32 *)(k + K_EXTLEN);
}

static inline u8 *slot(u8 *k, u32 i)
{
    return i < 16 ? k + K_RING + i * 0x38 : *(u8 **)(k + K_EXTBUF) + (i - 16) * 0x38;
}
#else
/* the older KPAD library: a fixed ring of 16 */
static inline u32 ring_len(u8 *k)
{
    return 16;
}

static inline u8 *slot(u8 *k, u32 i)
{
    return k + K_RING + i * 0x38;
}
#endif

static __attribute__((noinline)) void fill_cc(u8 *s, u32 h, u32 l, u32 b)
{
#if SWAP_STICKS
    u32 lx = l >> 24, ly = l >> 16;          /* C-stick moves the cursor (left stick) */
    u32 rx = h >> 8, ry = h;                 /* control stick swims (right stick) */
#else
    u32 lx = h >> 8, ly = h;
    u32 rx = l >> 24, ry = l >> 16;
#endif
    *(u16 *)(s + 0x2A) = (u16)b;
    *(s16 *)(s + 0x2C) = stick(lx);
    *(s16 *)(s + 0x2E) = stick(ly);
    *(s16 *)(s + 0x30) = stick(rx);
    *(s16 *)(s + 0x32) = stick(ry);
    s[0x34] = (b & CL_L) ? 180 : 0;          /* digital L / R: pressed = fully in */
    s[0x35] = (b & CL_R) ? 180 : 0;
    s[0x28] = 2;                             /* extension: Classic Controller */
    s[0x29] = 0;                             /* no extension error */
    s[0x36] = 8;                             /* classic + accel + pointer data */
}

static __attribute__((noinline)) void put_sample(u8 *k, u32 idx, u32 h, u32 l, u32 b)
{
    u32 *p = (u32 *)slot(k, idx);
    u32 i;

    for (i = 0; i < 0x38 / 4; i++)
        p[i] = 0;
    fill_cc((u8 *)p, h, l, b);
    ((u8 *)p)[0x37] = MARK;
}

/* KPADRead hands the game the samples queued since its last call but one, and
 * needs at least two in the ring (it keeps the newest as the next call's
 * reference).  The game's controller class reads the left stick from the
 * *second* entry it gets back, so, like a Wii Remote does, we deliver two per
 * frame: the older with the previous frame's buttons (so the press and release
 * edges still land in the newest entry) and both with the current sticks.
 *
 * With a real Wii Remote queuing samples, the pad becomes the remote's
 * extension instead; a real Nunchuk or Classic Controller is never touched. */
void gc_sample(u8 *k, u32 chan)
{
    u32 h, l, b, n, idx, cnt, i;
    u8 *newest;

    if (chan || !gc_in(&h, &l))
        return;

    b = cc_buttons(h);
    n = ring_len(k);
    idx = k[K_IDX];
    cnt = k[K_CNT];
    if (idx >= n)
        idx = 0;
    newest = cnt ? slot(k, (idx + n - 1) % n) : 0;

    if (!newest || newest[0x37] == MARK) {
        /* nothing but our own samples (or nothing): queue the next two */
        if (cnt + 2 > n)
            return;
        put_sample(k, idx, h, l, ST->prev_btn);
        put_sample(k, (idx + 1) % n, h, l, b);
        k[K_IDX] = (idx + 2) % n;
        k[K_CNT] = cnt + 2;
        ST->prev_btn = b;
        return;
    }

    /* real samples queued: a bare Wii Remote gets the pad as its extension */
    ST->prev_btn = b;
    if (cnt > n)
        cnt = n;
    for (i = 0; i < cnt; i++) {
        u8 *s = slot(k, (idx + n - cnt + i) % n);
        if (s[0x37] != MARK && (s[0x28] == 0 || s[0x28] == 0xFD))
            fill_cc(s, h, l, b);
    }
}
#endif

#if defined(HOOK_PROBE)
/* WPADProbe(chan, &type): report a Classic Controller on channel 0 while a
 * pad is plugged in, unless the channel already has a real extension */
u32 gc_probe(u32 chan, u32 *type)
{
    u32 h, l;
    u8 *blk;
    u32 t;
    s32 status;

    if (chan || !gc_in(&h, &l))
        return 0;
    blk = *(u8 **)(WPAD_TBL + chan * 4);
    t = blk[2241];
    status = *(s32 *)(blk + 2236);
    if (status != -1 && (t == 1 || t == 2))
        return 0;
    if (type)
        *type = 2;
    return 1;
}
#endif

#if defined(HOOK_INFO) || defined(HOOK_INFOASYNC) || defined(HOOK_DPD)
/* The game asks WPAD for the controller's status (battery, extension) before it
 * lets you play, and WPADGetInfo even sleeps until the Wii Remote answers.  A
 * pad has no radio to ask, so answer for it: a full battery, an extension
 * attached.  Only while WPAD itself has no connection on the channel. */
static int fake_pad(u32 chan)
{
    u32 h, l;
    u8 *blk;

    if (chan || !gc_in(&h, &l))
        return 0;
    blk = *(u8 **)(WPAD_TBL + chan * 4);
    return *(s32 *)(blk + 2236) == -1;
}

#if defined(HOOK_INFO) || defined(HOOK_INFOASYNC)
static void fill_info(u8 *info)
{
    u32 *w = (u32 *)info;

    w[0] = 0;               /* dpd */
    w[1] = 0;               /* speaker */
    w[2] = 1;               /* attach: an extension is plugged in */
    w[3] = 0;               /* lowBat */
    w[4] = 0;               /* nearempty */
    info[0x14] = 4;         /* battery: full */
    info[0x15] = 1;         /* led */
    info[0x16] = 0;
    info[0x17] = 0;
}
#endif
#endif

#if defined(HOOK_DPD)
/* The game checks that the IR camera is enabled before it trusts the pointer
 * (the pad has no camera, but its pointer is made up from the sticks) */
u32 gc_dpd(u32 chan)
{
    return fake_pad(chan);
}
#endif

#if defined(HOOK_INFO)
u32 gc_info(u32 chan, u8 *info)
{
    if (!info || !fake_pad(chan))
        return 0;
    fill_info(info);
    return 1;
}
#endif

#if defined(HOOK_INFOASYNC)
u32 gc_infoasync(u32 chan, u8 *info, void (*cb)(s32, s32))
{
    if (!info || !fake_pad(chan))
        return 0;
    fill_info(info);
    if (cb)
        cb((s32)chan, 0);
    return 1;
}
#endif

#if defined(HOOK_SCENE)
/* 1 while a pad answers on port 1 */
u32 gc_present(void)
{
    u32 h, l;

    return gc_in(&h, &l);
}
#endif
